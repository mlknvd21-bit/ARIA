import os
import json
import importlib.util
from plugins.manager import PluginManager
from utils.logger import get_logger

logger = get_logger(__name__)

class PluginLoader:
    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = plugins_dir
        self.loaded_plugins = {}       # name -> manifest
        self.extra_tools = {}          # name -> tool instance
        self.extra_commands = {}       # command -> handler string
        self.extra_hooks = []          # list of hook handler dicts
        self.manager = PluginManager()

    def discover_and_load(self):
        if not os.path.isdir(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            return

        for folder in os.listdir(self.plugins_dir):
            folder_path = os.path.join(self.plugins_dir, folder)
            if not os.path.isdir(folder_path):
                continue
            manifest_path = os.path.join(folder_path, "manifest.json")
            if not os.path.isfile(manifest_path):
                continue

            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            except Exception:
                logger.warning(f"Invalid manifest in {folder}")
                continue

            plugin_name = manifest.get("name", folder)
            if not self.manager.is_enabled(plugin_name):
                logger.info(f"Plugin '{plugin_name}' is disabled, skipping.")
                continue

            init_path = os.path.join(folder_path, "__init__.py")
            if not os.path.isfile(init_path):
                logger.warning(f"No __init__.py in {folder}, skipping.")
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{folder}", init_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, 'load'):
                    instances = module.load()
                    self.loaded_plugins[plugin_name] = manifest

                    # Register tools
                    for tool_name in manifest.get("tools", []):
                        for inst in instances:
                            if hasattr(inst, 'name') and inst.name == tool_name:
                                self.extra_tools[tool_name] = inst
                                logger.info(f"Plugin '{plugin_name}' loaded tool: {tool_name}")
                                break

                    # Register commands
                    for cmd_name in manifest.get("commands", []):
                        self.extra_commands[cmd_name] = f"plugin:{plugin_name}:{cmd_name}"

                    # Register hooks (on_message, etc.)
                    for hook_name in manifest.get("hooks", []):
                        for inst in instances:
                            if hasattr(inst, hook_name):
                                self.extra_hooks.append({
                                    "plugin": plugin_name,
                                    "hook": hook_name,
                                    "handler": getattr(inst, hook_name)
                                })
                                logger.info(f"Plugin '{plugin_name}' registered hook: {hook_name}")
                                break

                    logger.info(f"Plugin '{plugin_name}' v{manifest.get('version', '?')} loaded.")
            except Exception as e:
                logger.error(f"Failed to load plugin '{plugin_name}': {e}")

    def trigger_hooks(self, hook_name, **kwargs):
        """Call all registered hooks of a given name (e.g., 'on_message')."""
        for entry in self.extra_hooks:
            if entry["hook"] == hook_name:
                try:
                    entry["handler"](**kwargs)
                except Exception as e:
                    logger.error(f"Hook {hook_name} in plugin '{entry['plugin']}' failed: {e}")
