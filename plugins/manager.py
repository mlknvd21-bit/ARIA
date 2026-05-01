import json
import os
from utils.logger import get_logger

logger = get_logger(__name__)

STATE_FILE = os.path.join(os.path.dirname(__file__), "plugins_state.json")

class PluginManager:
    def __init__(self):
        self.state = self._load_state()

    def _load_state(self):
        if not os.path.exists(STATE_FILE):
            default = {}
            plugins_dir = os.path.dirname(__file__)
            if os.path.isdir(plugins_dir):
                for folder in os.listdir(plugins_dir):
                    folder_path = os.path.join(plugins_dir, folder)
                    manifest = os.path.join(folder_path, "manifest.json")
                    if os.path.isdir(folder_path) and os.path.isfile(manifest):
                        try:
                            with open(manifest, 'r') as f:
                                data = json.load(f)
                            default[data.get("name", folder)] = {
                                "enabled": True,
                                "version": data.get("version", "?")
                            }
                        except Exception:
                            pass
            with open(STATE_FILE, 'w') as f:
                json.dump(default, f, indent=2)
            return default
        with open(STATE_FILE, 'r') as f:
            return json.load(f)

    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def list_plugins(self):
        result = []
        plugins_dir = os.path.dirname(__file__)
        if not os.path.isdir(plugins_dir):
            return result
        for folder in os.listdir(plugins_dir):
            folder_path = os.path.join(plugins_dir, folder)
            manifest = os.path.join(folder_path, "manifest.json")
            if os.path.isdir(folder_path) and os.path.isfile(manifest):
                try:
                    with open(manifest, 'r') as f:
                        info = json.load(f)
                    name = info.get("name", folder)
                    enabled = self.is_enabled(name)  # use fresh check
                    result.append({
                        "name": name,
                        "version": info.get("version", "?"),
                        "author": info.get("author", "?"),
                        "description": info.get("description", ""),
                        "enabled": enabled
                    })
                except Exception:
                    pass
        return result

    def set_enabled(self, name, enabled):
        # Always re-read state before modifying
        self.state = self._load_state()
        if name in self.state:
            self.state[name]["enabled"] = enabled
            self.save_state()
            return True
        return False

    def is_enabled(self, name):
        """Check enabled status — ALWAYS reads the latest state file."""
        self.state = self._load_state()
        return self.state.get(name, {}).get("enabled", True)

    def get_plugin_info(self, name):
        plugins_dir = os.path.dirname(__file__)
        if not os.path.isdir(plugins_dir):
            return None
        for folder in os.listdir(plugins_dir):
            folder_path = os.path.join(plugins_dir, folder)
            manifest = os.path.join(folder_path, "manifest.json")
            if os.path.isdir(folder_path) and os.path.isfile(manifest):
                try:
                    with open(manifest, 'r') as f:
                        info = json.load(f)
                    if info.get("name", "") == name:
                        return info
                except Exception:
                    pass
        return None
