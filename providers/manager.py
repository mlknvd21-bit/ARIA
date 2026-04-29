import yaml
import os
from utils.logger import get_logger
from providers.groq import GroqProvider
from providers.deepseek import DeepSeekProvider
from providers.openrouter import OpenRouterProvider
from providers.gemini import GeminiProvider

logger = get_logger(__name__)

class ProviderManager:
    def __init__(self, providers_config_path="config/providers.yaml"):
        self.providers_config_path = providers_config_path
        self.providers = {}
        self.priority_order = []
        self.load_providers()

    def load_providers(self):
        config = self._read_config()
        providers_cfg = config.get("providers", {})
        ordered = sorted(
            [(name, cfg) for name, cfg in providers_cfg.items() if cfg.get("enabled", True)],
            key=lambda x: x[1].get("priority", 999)
        )
        self.priority_order = [name for name, _ in ordered]
        if self.priority_order:
            active_name = self.priority_order[0]
            self._load_provider(active_name, providers_cfg[active_name])
        else:
            raise RuntimeError("No enabled provider found in config!")
        logger.info(f"Active provider: {self.priority_order[0]} (priority order: {self.priority_order})")

    def _read_config(self):
        if not os.path.exists(self.providers_config_path):
            default = {"providers": {"groq": {"enabled": True, "priority": 1, "model": "llama-3.3-70b-versatile", "api_key_env": "GROQ_API_KEY", "type": "groq"}}}
            os.makedirs(os.path.dirname(self.providers_config_path), exist_ok=True)
            with open(self.providers_config_path, 'w') as f:
                yaml.dump(default, f)
        with open(self.providers_config_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def _write_config(self, config):
        with open(self.providers_config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

    def _load_provider(self, name, cfg):
        api_key = os.getenv(cfg.get("api_key_env", ""))
        if not api_key:
            logger.warning(f"API key ({cfg.get('api_key_env')}) not set for {name}")
            return None
        provider_config = {"api_key": api_key, "model": cfg.get("model", "llama-3.3-70b-versatile")}
        if name.lower() == "groq":
            provider = GroqProvider(provider_config)
        elif name.lower() == "openrouter":
            provider = OpenRouterProvider(provider_config)
        elif name.lower() == "deepseek":
            provider = DeepSeekProvider(provider_config)
        elif name.lower() == "gemini":
            provider = GeminiProvider(provider_config)
        else:
            logger.warning(f"Unknown provider type '{name}', skipping.")
            return None
        self.providers[name] = provider
        return provider

    def get_active_provider(self):
        if not self.providers:
            config = self._read_config()
            providers_cfg = config.get("providers", {})
            for name in self.priority_order:
                if name in providers_cfg:
                    inst = self._load_provider(name, providers_cfg[name])
                    if inst:
                        return inst
            raise RuntimeError("No provider could be loaded.")
        return next(iter(self.providers.values()))

    def get_available_models(self):
        active = self.get_active_provider()
        if hasattr(active, 'fetch_models'):
            return active.fetch_models()
        return []

    def get_active_model(self):
        """Return the currently active model name for the active provider."""
        config = self._read_config()
        active_name = self.priority_order[0] if self.priority_order else None
        if active_name and active_name in config.get("providers", {}):
            return config["providers"][active_name].get("model", "unknown")
        return "unknown"

    def set_active_model(self, model_id: str):
        """Change the model of the active provider and reload."""
        config = self._read_config()
        active_name = self.priority_order[0] if self.priority_order else None
        if not active_name:
            return False, "No active provider."
        if active_name not in config.get("providers", {}):
            return False, "Active provider not in config."
        config["providers"][active_name]["model"] = model_id
        self._write_config(config)
        self.load_providers()
        return True, f"Model changed to {model_id}."

    def add_provider(self, name, provider_type, api_key_env, model, priority, enabled=True):
        config = self._read_config()
        if "providers" not in config:
            config["providers"] = {}
        if name in config["providers"]:
            return False, f"Provider '{name}' already exists."
        config["providers"][name] = {
            "type": provider_type,
            "enabled": enabled,
            "priority": priority,
            "model": model,
            "api_key_env": api_key_env
        }
        self._write_config(config)
        self.load_providers()
        return True, f"Provider '{name}' added successfully."

    def remove_provider(self, name):
        config = self._read_config()
        if "providers" not in config or name not in config["providers"]:
            return False, f"Provider '{name}' not found."
        del config["providers"][name]
        self._write_config(config)
        self.load_providers()
        return True, f"Provider '{name}' removed."

    def set_enabled(self, name, enabled: bool):
        config = self._read_config()
        if name not in config.get("providers", {}):
            return False, "Provider not found."
        config["providers"][name]["enabled"] = enabled
        self._write_config(config)
        self.load_providers()
        state = "enabled" if enabled else "disabled"
        return True, f"Provider '{name}' {state}."
