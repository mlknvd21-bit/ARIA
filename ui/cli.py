from core.engine import Engine
from core.builder import Builder
from core.upgrader import Upgrader
from core.swarm import Swarm
from utils.backup import create_backup, list_backups, restore_backup
from utils.logger import get_logger
from plugins.manager import PluginManager
from plugins.loader import PluginLoader

logger = get_logger(__name__)

class CLI:
    def __init__(self, engine: Engine, provider_manager=None, memory=None, builder: Builder = None, swarm: Swarm = None):
        self.engine = engine
        self.manager = provider_manager
        self.memory = memory
        self.builder = builder
        self.swarm = swarm
        self.running = True
        self.plugin_manager = PluginManager()
        self.upgrader = Upgrader()

        self.commands = {
            "!exit": self.cmd_exit,
            "!help": self.cmd_help,
            "/providers": self.cmd_providers,
            "/memory": self.cmd_memory,
            "/models": self.cmd_models,
            "!build": self.cmd_build,
            "!backup": self.cmd_backup,
            "!restore": self.cmd_restore,
            "!swarm": self.cmd_swarm,
            "!upgrade": self.cmd_upgrade,
            "!version": self.cmd_version,
            "!rollback": self.cmd_rollback,
            "/electronics": self.cmd_electronics,
            "/plugin": self.cmd_plugin,
        }

        # Auto-register plugin commands
        self._register_plugin_commands()

    def _register_plugin_commands(self):
        """Load all enabled plugins and register their CLI commands."""
        loader = PluginLoader()
        loader.discover_and_load()
        for plugin_name, manifest in loader.loaded_plugins.items():
            if not self.plugin_manager.is_enabled(plugin_name):
                continue
            for cmd_name in manifest.get("commands", []):
                tool_name = manifest.get("tools", [None])[0]
                if tool_name and tool_name in loader.extra_tools:
                    tool = loader.extra_tools[tool_name]
                    if hasattr(tool, 'handle_command'):
                        # درست کلوزر: ڈیفالٹ آرگیومنٹ سے بائنڈ کریں
                        def make_handler(t, c):
                            def handler(args, _t=t, _c=c):
                                return _t.handle_command(_c, args)
                            return handler
                        self.commands[cmd_name] = make_handler(tool, cmd_name)
                        logger.info(f"Registered plugin command: {cmd_name}")
                    else:
                        # Generic fallback
                        def make_generic(t, c):
                            def handler(args, _t=t, _c=c):
                                return _t.execute({"arg": args})
                            return handler
                        self.commands[cmd_name] = make_generic(tool, cmd_name)
                        logger.warning(f"Plugin {plugin_name} has command {cmd_name} but tool lacks handle_command; using generic.")

    def cmd_exit(self, args):
        logger.info("Exiting ARIA. Goodbye!")
        self.running = False

    def cmd_help(self, args):
        print("Available commands:")
        print("  !exit                        - Exit ARIA")
        print("  !help                        - Show this help")
        print("  /providers                   - Manage AI providers")
        print("  /memory                      - Manage personal memories")
        print("  /models                      - List available models [Coming Soon]")
        print("  !build <description>         - Build a web app [Coming Soon]")
        print("  !backup                      - Backup all ARIA data")
        print("  !restore <filename>          - Restore a previous backup")
        print("  !swarm <task>                - Complex multi-agent task")
        print("  !upgrade                     - Upgrade ARIA to latest version")
        print("  !version                     - Show current version")
        print("  !rollback                    - Rollback to previous version")
        print("  /electronics <part>          - Search electronics parts database")
        print("  /plugin [list|enable|disable|info] <name> - Plugin management")
        print("  /weather <city>              - Get weather for a city")
        print("  Just type any message to chat.")

    def cmd_providers(self, args):
        parts = args.strip().split()
        subcmd = parts[0].lower() if parts else "list"
        if subcmd == "list" or not subcmd:
            self._list_providers()
        elif subcmd == "add" and len(parts) >= 5:
            name = parts[1]; ptype = parts[2]; apikey_env = parts[3]; priority = parts[4]
            model = parts[5] if len(parts) > 5 else "default"
            if not model or model == "default":
                model = "openai/gpt-3.5-turbo" if ptype.lower() == "openrouter" else "llama-3.3-70b-versatile"
            ok, msg = self.manager.add_provider(name, ptype, apikey_env, model, int(priority))
            print(msg)
        elif subcmd == "remove" and len(parts) == 2:
            ok, msg = self.manager.remove_provider(parts[1]); print(msg)
        elif subcmd == "enable" and len(parts) == 2:
            ok, msg = self.manager.set_enabled(parts[1], True); print(msg)
        elif subcmd == "disable" and len(parts) == 2:
            ok, msg = self.manager.set_enabled(parts[1], False); print(msg)
        else:
            print("Usage: /providers [list|add|remove|enable|disable] ... (see !help)")

    def _list_providers(self):
        if not self.manager: print("[Error] Provider manager not available."); return
        try:
            import yaml
            with open(self.manager.providers_config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            providers = config.get("providers", {})
            if not providers: print("No providers configured."); return
            print("\nConfigured Providers:"); print("---------------------")
            for name, cfg in providers.items():
                enabled = cfg.get("enabled", True)
                priority = cfg.get("priority", "?"); model = cfg.get("model", "?")
                api_env = cfg.get("api_key_env", "?"); ptype = cfg.get("type", "?")
                if enabled and self.manager.priority_order and self.manager.priority_order[0] == name:
                    status = "🟢 Active"
                elif enabled: status = "✅ Enabled"
                else: status = "❌ Disabled"
                print(f"  {status}  {name}  type={ptype} priority={priority} model={model} key_env={api_env}")
            print()
        except Exception as e:
            print(f"[Error reading providers config: {e}]")

    def cmd_memory(self, args):
        if not self.memory: print("[Error] Memory module not available."); return
        parts = args.strip().split(); subcmd = parts[0].lower() if parts else "list"
        if subcmd == "list":
            keys = self.memory.all_keys()
            if not keys: print("No memories stored yet.")
            else:
                print("\nSaved Memories:"); print("---------------")
                for key in keys: print(f"  {key}: {self.memory.recall(key)}")
                print()
        elif subcmd == "recall" and len(parts) >= 2:
            val = self.memory.recall(parts[1]); print(val if val else f"No memory found for '{parts[1]}'.")
        elif subcmd == "remember" and len(parts) >= 3:
            key = parts[1]; value = " ".join(parts[2:]); self.memory.remember(key, value)
            print(f"Stored: {key} = {value}")
        elif subcmd == "forget" and len(parts) == 2:
            self.memory.forget(parts[1]); print(f"Forgot: {parts[1]}")
        elif subcmd == "search" and len(parts) >= 2:
            query = " ".join(parts[1:]); results = self.memory.search(query)
            if not results: print(f"No memories found for '{query}'.")
            else:
                print(f"\nSearch results for '{query}':")
                for k, v in results: print(f"  {k}: {v}")
                print()
        else:
            print("Usage: /memory [list|recall|remember|forget|search] ...")

    def cmd_models(self, args):
        if not self.manager: print("[Error] Provider manager not available."); return
        print("Fetching available models, please wait...")
        models = self.manager.get_available_models()
        if not models: print("Could not fetch model list.")
        else:
            print(f"\nAvailable models ({len(models)}):")
            for m in models: print(f"  - {m}")
            print()

    def cmd_build(self, args):
        if not self.builder: print("[Error] Builder not available."); return
        description = args.strip()
        if not description: print("Usage: !build <description>"); return
        print(f"Building project: {description} ...")
        result = self.builder.build(description)
        print(result)

    def cmd_backup(self, args):
        custom_name = args.strip() if args.strip() else None
        print("Creating backup...")
        try:
            fname, diff = create_backup(custom_name)
            print(f"✅ Backup saved: {fname}")
            print(diff)
        except Exception as e:
            print(f"❌ Backup failed: {e}")

    def cmd_restore(self, args):
        filename = args.strip()
        if not filename:
            backups = list_backups()
            if not backups: print("No backups found."); return
            filename = backups[0]; print(f"Restoring latest: {filename}")
        print(f"Restoring backup: {filename} ...")
        try:
            restore_backup(filename); print("Backup restored successfully.")
        except Exception as e: print(f"Restore failed: {e}")

    
    def cmd_upgrade(self, args):
        """Upgrade ARIA from GitHub."""
        print("Checking for updates...")
        available, new_version, notes = self.upgrader.check_for_update()
        if not available:
            print("✅ ARIA is already up to date (v" + self.upgrader.current_version + ").")
            return
        print(f"🔔 New version available: v{new_version}")
        if notes:
            print(f"   Notes: {notes}")
        confirm = input("Proceed with upgrade? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Upgrade cancelled.")
            return
        print("📦 Creating backup...")
        backup = self.upgrader.backup_current()
        if not backup:
            print("❌ Backup failed. Upgrade aborted.")
            return
        print("⬇️ Downloading latest version...")
        extracted = self.upgrader.download_and_extract()
        if not extracted:
            print("❌ Download failed. Upgrade aborted.")
            return
        print("🔄 Applying upgrade...")
        if self.upgrader.apply_upgrade(extracted):
            print("✅ Upgrade successful! ARIA will now restart.")
            print("   Run 'ar' or 'arw' to start the new version.")
            self.running = False
        else:
            print("❌ Upgrade failed. Restoring backup...")
            self.upgrader.restore_backup()
            print("✅ Backup restored. ARIA is back to previous version.")

    def cmd_version(self, args):
        """Show current ARIA version."""
        print(f"ARIA version: {self.upgrader.current_version}")

    def cmd_rollback(self, args):
        """Rollback to a previous upgrade backup."""
        backups = self.upgrader.list_backups()
        if not backups:
            print("No upgrade backups found.")
            return
        print("Available backups:")
        for i, b in enumerate(backups[:5]):
            print(f"  [{i+1}] {b}")
        choice = input("Enter backup number (or 0 to cancel): ").strip()
        if choice == "0" or not choice:
            print("Rollback cancelled.")
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                ok, msg = self.upgrader.restore_backup(backups[idx])
                if ok:
                    print(f"✅ {msg}. Restart ARIA.")
                    self.running = False
                else:
                    print(f"❌ {msg}")
        except Exception:
            print("Invalid choice.")

    def cmd_swarm(self, args):
        if not self.swarm: print("[Error] Swarm module not available."); return
        task = args.strip()
        if not task: print("Usage: !swarm <complex task description>"); return
        print("=" * 50); print(f"Swarm task: {task}"); print("=" * 50)
        result = self.swarm.run(task)
        print("\n" + "=" * 50); print("FINAL ANSWER:"); print(result); print("=" * 50)

    def cmd_electronics(self, args):
        part = args.strip()
        if not part: print("Usage: /electronics <part_number>"); return
        from plugins.electronics.tool import ElectronicsTool
        tool = ElectronicsTool()
        result = tool.execute({"part": part})
        print(result)

    def cmd_plugin(self, args):
        parts = args.strip().split()
        subcmd = parts[0].lower() if parts else "list"
        name = parts[1] if len(parts) > 1 else None
        if subcmd == "list":
            plugins = self.plugin_manager.list_plugins()
            if not plugins: print("No plugins installed."); return
            print("\nInstalled Plugins:"); print("------------------")
            for p in plugins:
                status = "✅ Enabled" if p["enabled"] else "❌ Disabled"
                print(f"  {status}  {p['name']} v{p['version']} by {p['author']}")
                print(f"           {p['description']}")
            print()
        elif subcmd == "enable" and name:
            if self.plugin_manager.set_enabled(name, True): print(f"Plugin '{name}' enabled.")
            else: print(f"Plugin '{name}' not found.")
        elif subcmd == "disable" and name:
            if self.plugin_manager.set_enabled(name, False): print(f"Plugin '{name}' disabled.")
            else: print(f"Plugin '{name}' not found.")
        elif subcmd == "info" and name:
            info = self.plugin_manager.get_plugin_info(name)
            if info:
                print(f"\nPlugin: {info.get('name', name)}")
                print(f"Version: {info.get('version', '?')}")
                print(f"Author: {info.get('author', '?')}")
                print(f"Description: {info.get('description', '')}")
                print(f"Tools: {', '.join(info.get('tools', []))}")
                print(f"Commands: {', '.join(info.get('commands', []))}")
                enabled = self.plugin_manager.is_enabled(name)
                print(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}")
            else: print(f"Plugin '{name}' not found.")
        else:
            print("Usage: /plugin [list|enable|disable|info] <name>")

    def run(self):
        print("ARIA is ready. Type !help for commands, !exit to quit.")
        while self.running:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!"); break
            if not user_input: continue
            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=1)
                command = parts[0]; args = parts[1] if len(parts) > 1 else ""
                if command in self.commands:
                    result = self.commands[command](args)
                    if result and str(result).strip():
                        print(result)
                else:
                    print(f"Unknown command: {command}. Type !help for list.")
                continue
            if user_input.startswith("!"):
                parts = user_input.split(maxsplit=1)
                command = parts[0]; args = parts[1] if len(parts) > 1 else ""
                if command in self.commands:
                    result = self.commands[command](args)
                    if result and str(result).strip():
                        print(result)
                else:
                    print(f"Unknown command: {command}. Type !help for list.")
                continue
            response = self.engine.process(user_input)
            print(response)
