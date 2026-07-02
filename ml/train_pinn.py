"""
AETHER-COOL — PINN Training Script
Trains the Physics-Informed Neural Network on sample city data.
"""

import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.models.pinn import PINNModel, PINNLoss, create_model


def load_training_data(data_dir: str) -> tuple:
    """Load numpy arrays from sample data directory"""
    np_dir = os.path.join(data_dir, 'numpy')

    ndvi = np.load(os.path.join(np_dir, 'ndvi.npy')).flatten()
    albedo = np.load(os.path.join(np_dir, 'albedo.npy')).flatten()
    building_density = np.load(os.path.join(np_dir, 'building_density.npy')).flatten()
    svf = np.load(os.path.join(np_dir, 'svf.npy')).flatten()
    dist_water = np.load(os.path.join(np_dir, 'dist_water.npy')).flatten()
    lst = np.load(os.path.join(np_dir, 'lst.npy')).flatten()

    # Simulated ERA5 atmospheric data
    n = len(ndvi)
    np.random.seed(123)
    air_temp = np.random.normal(38.0, 2.0, n)       # °C
    wind_speed = np.random.uniform(1.0, 6.0, n)      # m/s
    humidity = np.random.uniform(30.0, 70.0, n)       # %

    # Stack features: [ndvi, albedo, building_density, svf, dist_water, air_temp, wind_speed, humidity]
    features = np.stack([
        ndvi, albedo, building_density, svf, dist_water,
        air_temp, wind_speed, humidity
    ], axis=1).astype(np.float32)

    targets = lst.astype(np.float32).reshape(-1, 1)

    return features, targets


def normalize_features(features: np.ndarray) -> tuple:
    """Normalize features to zero mean, unit variance"""
    mean = features.mean(axis=0)
    std = features.std(axis=0) + 1e-8
    normalized = (features - mean) / std
    return normalized, mean, std


def train(epochs: int = 200, batch_size: int = 256, lr: float = 1e-3,
          lambda_physics: float = 0.1, device: str = 'cpu'):
    """
    Train the PINN model.
    """
    print("=" * 60)
    print("AETHER-COOL — PINN Training")
    print("=" * 60)

    # Paths
    data_dir = os.path.join(os.path.dirname(__file__), 'data', 'sample')
    model_dir = os.path.join(os.path.dirname(__file__), 'data', 'models')
    os.makedirs(model_dir, exist_ok=True)

    # Load data
    print("\n[1] Loading training data...")
    features, targets = load_training_data(data_dir)
    print(f"    Samples: {features.shape[0]}, Features: {features.shape[1]}")
    print(f"    LST range: {targets.min():.1f}°C — {targets.max():.1f}°C")

    # Store raw features for physics loss (before normalization)
    raw_features = features.copy()

    # Normalize
    features_norm, feat_mean, feat_std = normalize_features(features)

    # Train/val split (80/20 spatial block split)
    n = len(features)
    split = int(0.8 * n)
    indices = np.random.permutation(n)
    train_idx, val_idx = indices[:split], indices[split:]

    X_train = torch.FloatTensor(features_norm[train_idx]).to(device)
    y_train = torch.FloatTensor(targets[train_idx]).to(device)
    raw_train = torch.FloatTensor(raw_features[train_idx]).to(device)

    X_val = torch.FloatTensor(features_norm[val_idx]).to(device)
    y_val = torch.FloatTensor(targets[val_idx]).to(device)

    # Create data loader
    train_dataset = TensorDataset(X_train, y_train, raw_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Create model and loss
    print(f"\n[2] Creating PINN model on device: {device}")
    model = create_model(input_dim=8, device=device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"    Total parameters: {total_params:,}")

    criterion = PINNLoss(
        lambda_physics=lambda_physics,
        lambda_boundary=0.01,
        lambda_smoothness=0.001
    )

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    # Training loop
    print(f"\n[3] Training for {epochs} epochs...")
    print(f"    Batch size: {batch_size}, LR: {lr}, λ_physics: {lambda_physics}")
    print("-" * 80)
    print(f"{'Epoch':>6} {'Total':>10} {'Data':>10} {'Physics':>10} "
          f"{'Val RMSE':>10} {'Val MAE':>10} {'LR':>10}")
    print("-" * 80)

    best_val_rmse = float('inf')
    history = []

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_losses = {'total': 0, 'data': 0, 'physics': 0}
        n_batches = 0

        for X_batch, y_batch, raw_batch in train_loader:
            optimizer.zero_grad()

            # Forward pass
            lst_pred, uncertainty = model(X_batch)

            # Compute loss
            losses = criterion(lst_pred, y_batch, uncertainty, raw_batch)
            losses['total'].backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

            optimizer.step()

            epoch_losses['total'] += losses['total'].item()
            epoch_losses['data'] += losses['data']
            epoch_losses['physics'] += losses['physics']
            n_batches += 1

        scheduler.step()

        # Validation
        model.eval()
        with torch.no_grad():
            val_pred, val_unc = model(X_val)
            val_mse = ((val_pred - y_val) ** 2).mean().item()
            val_rmse = np.sqrt(val_mse)
            val_mae = torch.abs(val_pred - y_val).mean().item()

        # Log
        avg_total = epoch_losses['total'] / n_batches
        avg_data = epoch_losses['data'] / n_batches
        avg_physics = epoch_losses['physics'] / n_batches
        current_lr = scheduler.get_last_lr()[0]

        history.append({
            'epoch': epoch,
            'total_loss': avg_total,
            'data_loss': avg_data,
            'physics_loss': avg_physics,
            'val_rmse': val_rmse,
            'val_mae': val_mae
        })

        if epoch % 10 == 0 or epoch == 1:
            print(f"{epoch:>6} {avg_total:>10.4f} {avg_data:>10.4f} {avg_physics:>10.4f} "
                  f"{val_rmse:>10.4f} {val_mae:>10.4f} {current_lr:>10.6f}")

        # Save best model
        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            torch.save(model.state_dict(), os.path.join(model_dir, 'pinn_best.pth'))

    # Save final model
    torch.save(model.state_dict(), os.path.join(model_dir, 'pinn_final.pth'))

    # Save normalization params
    norm_params = {
        'mean': feat_mean.tolist(),
        'std': feat_std.tolist(),
        'feature_names': ['ndvi', 'albedo', 'building_density', 'svf',
                          'dist_water', 'air_temp', 'wind_speed', 'humidity']
    }
    with open(os.path.join(model_dir, 'norm_params.json'), 'w') as f:
        json.dump(norm_params, f, indent=2)

    # Save training history
    with open(os.path.join(model_dir, 'training_history.json'), 'w') as f:
        json.dump(history, f, indent=2)

    # Final evaluation
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"\nBest Validation RMSE: {best_val_rmse:.4f}°C")
    print(f"Best Validation MAE:  {history[-1]['val_mae']:.4f}°C")

    # Compute R²
    model.eval()
    with torch.no_grad():
        all_pred, _ = model(torch.FloatTensor(features_norm).to(device))
        all_pred = all_pred.cpu().numpy().flatten()
        all_target = targets.flatten()
        ss_res = np.sum((all_target - all_pred) ** 2)
        ss_tot = np.sum((all_target - all_target.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot
        print(f"Overall R²:           {r2:.4f}")

    print(f"\nModels saved to: {os.path.abspath(model_dir)}")
    print(f"  → pinn_best.pth")
    print(f"  → pinn_final.pth")
    print(f"  → norm_params.json")
    print(f"  → training_history.json")

    return model, history


if __name__ == '__main__':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    train(epochs=200, batch_size=256, lr=1e-3, device=device)
