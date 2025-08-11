# config/config.py

import os
from dotenv import load_dotenv
from pathlib import Path

class Config:
    """
    Handles loading and accessing configuration settings from the .env file.
    """
    def __init__(self):
        # Find the project root by looking for the .env file
        self.project_dir = self._find_project_root()
        self.dotenv_path = self.project_dir / '.env'
        
        if not self.dotenv_path.exists():
            raise FileNotFoundError("Could not find .env file. Ensure it is in the project root.")
            
        load_dotenv(dotenv_path=self.dotenv_path)
        
        # Load all environment variables into a dictionary
        self.settings = {key: value for key, value in os.environ.items()}

    def _find_project_root(self, current_path=None):
        """Recursively find the project root by looking for the .env file."""
        if current_path is None:
            current_path = Path.cwd()
        
        if (current_path / '.env').exists():
            return current_path
        
        # Stop if we have reached the filesystem root
        if current_path.parent == current_path:
            return None
            
        return self._find_project_root(current_path.parent)

    def get(self, key, default=None):
        """
        Retrieves a configuration value by key.
        """
        return self.settings.get(key, default)

    def validate_config(self):
        """
        Validates that essential API keys and settings are present.
        """
        print("Validating configuration...")
        required_keys = [
            'ALPHA_VANTAGE_API_KEY',
            'NEWS_API_KEY',
            'FRED_API_KEY',
            'DATABASE_PATH'
        ]
        
        missing_keys = [key for key in required_keys if not self.get(key)]
        
        if missing_keys:
            print(f"❌ Missing required configuration keys: {', '.join(missing_keys)}")
            return False
            
        print("All essential keys found.")
        return True

# Create a single instance of the Config class to be used across the application
config = Config()