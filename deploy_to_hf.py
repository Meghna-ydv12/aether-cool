import os
import sys
from huggingface_hub import HfApi

def main():
    print("==========================================")
    print("  Deploy AETHER-COOL to Hugging Face      ")
    print("==========================================")
    print("This script will upload your code directly to Hugging Face Spaces.\n")
    
    hf_username = input("Enter your Hugging Face username: ").strip()
    space_name = input("Enter your Space name (e.g. aether-cool): ").strip()
    hf_token = input("Enter your Hugging Face Access Token (with WRITE permission): ").strip()
    
    if not hf_username or not space_name or not hf_token:
        print("Error: You must provide all inputs.")
        sys.exit(1)
        
    repo_id = f"{hf_username}/{space_name}"
    print(f"\nConnecting to space: {repo_id}...")
    
    api = HfApi(token=hf_token)
    
    try:
        # Check if space exists
        api.space_info(repo_id)
    except Exception as e:
        print(f"\nError finding space {repo_id}: {e}")
        print("Did you create the space on HuggingFace first? (Choose Docker -> Blank)")
        sys.exit(1)
        
    print("\nUploading project files (this may take a minute depending on your internet speed)...")
    
    try:
        # Upload the whole directory except .git and node_modules
        api.upload_folder(
            folder_path=".",
            repo_id=repo_id,
            repo_type="space",
            ignore_patterns=["*.git*", "*node_modules*", "venv*", "__pycache__*"]
        )
        print("\n✅ Success! Your code has been uploaded.")
        print(f"Go to https://huggingface.co/spaces/{repo_id} to watch it build and go live!")
    except Exception as e:
        print(f"\nUpload failed: {e}")

if __name__ == "__main__":
    main()
