import os
import yaml
from utils.logger import get_logger

logger = get_logger(__name__)

class Config:
    def __init__(self, config_path="config.yaml", defaults_path="config/defaults.yaml"):
        self.data = {}
        self.load_defaults(defaults_path)
        self.load_user_config(config_path)
        self.apply_env_overrides()

    def load_defaults(self, path):
        try:
            with open(path, 'r') as f:
                defaults = yaml.safe_load(f) or {}
                self.data.update(defaults)
                logger.debug(f"Defaults loaded: {defaults}")
        except FileNotFoundError:
            logger.warning("Defaults file not found, continuing.")

    def load_user_config(self, path):
        try:
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
                for key, value in user_config.items():
                    self.data[key] = value
                logger.debug(f"User config loaded: {user_config}")
        except FileNotFoundError:
            logger.warning(f"Config file {path} not found, using defaults.")

    def apply_env_overrides(self):
        env_key = os.getenv("GROQ_API_KEY")
        if env_key:
            self.data['api_key'] = env_key
            logger.debug("GROQ_API_KEY loaded from environment.")
        env_provider = os.getenv("ARIA_PROVIDER")
        if env_provider:
            self.data['provider'] = env_provider
            logger.debug(f"Provider override from env: {env_provider}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]
