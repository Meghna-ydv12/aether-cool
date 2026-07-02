"""
AETHER-COOL — Physics-Informed Neural Network (PINN)
Predicts Land Surface Temperature from urban features while
enforcing the urban energy balance equation as a physics constraint.

Energy Balance: Q* = Q_H + Q_E + Q_S + Q_F
Where:
  Q* = Net radiation (function of albedo, solar angle)
  Q_H = Sensible heat flux (function of LST - T_air, wind)
  Q_E = Latent heat flux (function of NDVI / evapotranspiration)
  Q_S = Storage heat flux (function of building density, thermal mass)
  Q_F = Anthropogenic heat flux (function of LULC type)
"""

import torch
import torch.nn as nn
import numpy as np
import os


class UrbanEnergyBalancePhysics:
    """
    Physics module encoding the urban energy balance equation.
    Used to compute physics residual loss during training.
    """

    # Physical constants
    STEFAN_BOLTZMANN = 5.67e-8  # W/m²/K⁴
    SOLAR_CONSTANT = 1000.0     # W/m² (peak incoming solar)
    AIR_DENSITY = 1.225         # kg/m³
    CP_AIR = 1005.0             # J/kg/K (specific heat of air)

    @staticmethod
    def net_radiation(albedo: torch.Tensor, lst_kelvin: torch.Tensor) -> torch.Tensor:
        """Q* = (1-α)·S↓ - ε·σ·T⁴ + L↓"""
        shortwave_in = UrbanEnergyBalancePhysics.SOLAR_CONSTANT
        emissivity = 0.95
        longwave_down = 350.0  # W/m² (approximate atmospheric longwave)

        q_star = ((1 - albedo) * shortwave_in
                  - emissivity * UrbanEnergyBalancePhysics.STEFAN_BOLTZMANN * lst_kelvin ** 4
                  + longwave_down)
        return q_star

    @staticmethod
    def sensible_heat(lst_kelvin: torch.Tensor, t_air_kelvin: torch.Tensor,
                      wind_speed: torch.Tensor) -> torch.Tensor:
        """Q_H = ρ · cp · C_H · U · (T_s - T_a)"""
        c_h = 0.003  # bulk transfer coefficient
        rho = UrbanEnergyBalancePhysics.AIR_DENSITY
        cp = UrbanEnergyBalancePhysics.CP_AIR
        wind_eff = torch.clamp(wind_speed, min=0.5)

        q_h = rho * cp * c_h * wind_eff * (lst_kelvin - t_air_kelvin)
        return q_h

    @staticmethod
    def latent_heat(ndvi: torch.Tensor) -> torch.Tensor:
        """Q_E ≈ f(NDVI) — evapotranspiration proxy"""
        # Higher NDVI → more evapotranspiration → more latent heat loss
        lambda_v = 2.45e6  # J/kg (latent heat of vaporization)
        et_rate = 0.0001 * ndvi  # kg/m²/s (simplified ET rate)
        q_e = lambda_v * et_rate
        return q_e

    @staticmethod
    def storage_heat(building_density: torch.Tensor,
                     net_rad: torch.Tensor) -> torch.Tensor:
        """Q_S ≈ α_s · Q* — storage as fraction of net radiation"""
        # Higher building density → higher thermal mass → more storage
        alpha_s = 0.2 + 0.3 * building_density
        q_s = alpha_s * net_rad
        return q_s

    @staticmethod
    def anthropogenic_heat(lulc_commercial: torch.Tensor,
                           lulc_industrial: torch.Tensor) -> torch.Tensor:
        """Q_F — anthropogenic heat from human activities"""
        q_f = 50.0 * lulc_commercial + 80.0 * lulc_industrial
        return q_f

    @staticmethod
    def energy_balance_residual(lst_kelvin, albedo, ndvi, building_density,
                                 t_air_kelvin, wind_speed,
                                 lulc_commercial, lulc_industrial):
        """
        Compute residual: Q* - Q_H - Q_E - Q_S - Q_F ≈ 0
        Returns the residual (should be close to zero for physical consistency)
        """
        q_star = UrbanEnergyBalancePhysics.net_radiation(albedo, lst_kelvin)
        q_h = UrbanEnergyBalancePhysics.sensible_heat(lst_kelvin, t_air_kelvin, wind_speed)
        q_e = UrbanEnergyBalancePhysics.latent_heat(ndvi)
        q_s = UrbanEnergyBalancePhysics.storage_heat(building_density, q_star)
        q_f = UrbanEnergyBalancePhysics.anthropogenic_heat(lulc_commercial, lulc_industrial)

        residual = q_star - q_h - q_e - q_s + q_f
        return residual


class PINNModel(nn.Module):
    """
    Physics-Informed Neural Network for Land Surface Temperature prediction.

    Input features (8):
        - NDVI (vegetation index)
        - Albedo (surface reflectance)
        - Building Density
        - Sky View Factor (SVF)
        - Distance to Water Body
        - Air Temperature (ERA5)
        - Wind Speed (ERA5)
        - Relative Humidity (ERA5)

    Output:
        - LST (°C) prediction
        - Uncertainty estimate (epistemic)
    """

    def __init__(self, input_dim: int = 8, hidden_dims: list = None,
                 dropout: float = 0.1):
        super().__init__()

        if hidden_dims is None:
            hidden_dims = [128, 256, 256, 128, 64]

        self.input_dim = input_dim

        # Build encoder network
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.LayerNorm(h_dim),
                nn.GELU(),
                nn.Dropout(dropout),
            ])
            prev_dim = h_dim

        self.encoder = nn.Sequential(*layers)

        # LST prediction head
        self.lst_head = nn.Sequential(
            nn.Linear(prev_dim, 32),
            nn.GELU(),
            nn.Linear(32, 1)
        )

        # Uncertainty prediction head (log variance)
        self.uncertainty_head = nn.Sequential(
            nn.Linear(prev_dim, 32),
            nn.GELU(),
            nn.Linear(32, 1)
        )

        # Skip connection for residual learning
        self.skip_linear = nn.Linear(input_dim, prev_dim)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='linear')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> tuple:
        """
        Forward pass.
        Args:
            x: Input features [batch_size, input_dim]
        Returns:
            lst_pred: Predicted LST in °C [batch_size, 1]
            uncertainty: Predicted uncertainty (std dev) [batch_size, 1]
        """
        # Encode features
        h = self.encoder(x)

        # Skip connection
        h = h + self.skip_linear(x)

        # Predict LST
        lst_pred = self.lst_head(h)

        # Predict uncertainty (log variance → std dev)
        log_var = self.uncertainty_head(h)
        uncertainty = torch.exp(0.5 * log_var)

        return lst_pred, uncertainty


class PINNLoss(nn.Module):
    """
    Combined loss function for PINN training:
    L_total = L_data + λ₁·L_physics + λ₂·L_boundary + λ₃·L_smoothness
    """

    def __init__(self, lambda_physics: float = 0.1,
                 lambda_boundary: float = 0.01,
                 lambda_smoothness: float = 0.001):
        super().__init__()
        self.lambda_physics = lambda_physics
        self.lambda_boundary = lambda_boundary
        self.lambda_smoothness = lambda_smoothness
        self.physics = UrbanEnergyBalancePhysics()

    def data_loss(self, pred: torch.Tensor, target: torch.Tensor,
                  uncertainty: torch.Tensor) -> torch.Tensor:
        """Negative log-likelihood loss with learned uncertainty"""
        # NLL: 0.5 * (log(σ²) + (y - ŷ)² / σ²)
        log_var = 2 * torch.log(uncertainty + 1e-8)
        mse = (pred - target) ** 2
        nll = 0.5 * (log_var + mse / (uncertainty ** 2 + 1e-8))
        return nll.mean()

    def physics_loss(self, lst_pred_celsius: torch.Tensor,
                     features: torch.Tensor) -> torch.Tensor:
        """
        Physics residual loss — enforce energy balance equation.
        features columns: [ndvi, albedo, building_density, svf,
                           dist_water, air_temp, wind_speed, humidity]
        """
        # Convert LST to Kelvin
        lst_kelvin = lst_pred_celsius + 273.15

        # Extract features
        ndvi = features[:, 0:1]
        albedo = features[:, 1:2]
        building_density = features[:, 2:3]
        air_temp_celsius = features[:, 5:6]
        wind_speed = features[:, 6:7]

        t_air_kelvin = air_temp_celsius + 273.15

        # LULC proxies (commercial ~ high building density, industrial ~ mid density)
        lulc_commercial = (building_density > 0.7).float()
        lulc_industrial = ((building_density > 0.5) & (building_density <= 0.7)).float()

        # Compute energy balance residual
        residual = self.physics.energy_balance_residual(
            lst_kelvin, albedo, ndvi, building_density,
            t_air_kelvin, wind_speed,
            lulc_commercial, lulc_industrial
        )

        # Normalize residual (energy flux can be large)
        residual_normalized = residual / 1000.0
        return (residual_normalized ** 2).mean()

    def boundary_loss(self, lst_pred: torch.Tensor) -> torch.Tensor:
        """
        Physical boundary constraints:
        - LST must be in [-10°C, 70°C]
        - Penalize predictions outside this range
        """
        lower_violation = torch.relu(-10.0 - lst_pred)
        upper_violation = torch.relu(lst_pred - 70.0)
        return (lower_violation ** 2 + upper_violation ** 2).mean()

    def smoothness_loss(self, lst_pred: torch.Tensor) -> torch.Tensor:
        """
        Spatial smoothness — adjacent pixels shouldn't differ by >15°C.
        Applied when predictions are on a grid (reshape needed).
        """
        if lst_pred.dim() == 1 or lst_pred.shape[0] < 4:
            return torch.tensor(0.0, device=lst_pred.device)

        # Compute differences between consecutive predictions
        diffs = torch.abs(lst_pred[1:] - lst_pred[:-1])
        violations = torch.relu(diffs - 15.0)
        return (violations ** 2).mean()

    def forward(self, pred: torch.Tensor, target: torch.Tensor,
                uncertainty: torch.Tensor, features: torch.Tensor) -> dict:
        """
        Compute total PINN loss.
        Returns dict with total loss and individual components.
        """
        l_data = self.data_loss(pred, target, uncertainty)
        l_physics = self.physics_loss(pred, features)
        l_boundary = self.boundary_loss(pred)
        l_smooth = self.smoothness_loss(pred)

        total = (l_data
                 + self.lambda_physics * l_physics
                 + self.lambda_boundary * l_boundary
                 + self.lambda_smoothness * l_smooth)

        return {
            'total': total,
            'data': l_data.item(),
            'physics': l_physics.item(),
            'boundary': l_boundary.item(),
            'smoothness': l_smooth.item()
        }


def create_model(input_dim: int = 8, device: str = 'cpu') -> PINNModel:
    """Factory function to create a PINN model"""
    model = PINNModel(input_dim=input_dim)
    model = model.to(device)
    return model


def load_model(path: str, input_dim: int = 8, device: str = 'cpu') -> PINNModel:
    """Load a trained PINN model from disk"""
    model = create_model(input_dim, device)
    if os.path.exists(path):
        state_dict = torch.load(path, map_location=device, weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()
    return model


def predict(model: PINNModel, features: np.ndarray, device: str = 'cpu') -> dict:
    """
    Run inference with the PINN model.
    Args:
        model: Trained PINNModel
        features: numpy array of shape [N, 8]
        device: torch device
    Returns:
        dict with 'lst' and 'uncertainty' arrays
    """
    model.eval()
    with torch.no_grad():
        x = torch.FloatTensor(features).to(device)
        lst_pred, uncertainty = model(x)

    return {
        'lst': lst_pred.cpu().numpy().flatten(),
        'uncertainty': uncertainty.cpu().numpy().flatten()
    }
