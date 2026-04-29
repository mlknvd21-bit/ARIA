import subprocess
from tools.base import BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)

class PackageManagerTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="package_manager",
            description="Manage packages using pkg, pip, or npm. Allowed actions: install, list, search."
        )
        # Allowed package managers and their allowed subcommands
        self.allowed = {
            "pkg": {
                "install": r"^[\w\-]+$",
                "search": r"^[\w\-]+$",
                "list-installed": r"^$"
            },
            "pip": {
                "install": r"^[\w\-\[\],.=<>!; ]+$",  # allow version specifiers
                "list": r"^$",
                "search": r"^[\w\-]+$"
            },
            "npm": {
                "install": r"^(?:-g )?[\w\-@/]+$",
                "list": r"^(?:-g)?$",
                "search": r"^[\w\-]+$"
            }
        }

    def _is_allowed(self, manager: str, action: str, args: str) -> bool:
        if manager not in self.allowed:
            return False
        if action not in self.allowed[manager]:
            return False
        pattern = self.allowed[manager][action]
        import re
        return bool(re.match(f"^{pattern}$", args.strip()))

    def execute(self, params: dict) -> str:
        manager = params.get("manager", "").strip().lower()
        action = params.get("action", "").strip().lower()
        package = params.get("package", "").strip()

        if not manager or not action:
            return "[Error] manager and action are required."

        # Build command
        if action == "list-installed":
            cmd = f"{manager} list-installed"
        elif action in ("install", "search", "list"):
            if action == "list":
                cmd = f"{manager} list"
            else:
                if not package:
                    return f"[Error] package name required for {action}."
                cmd = f"{manager} {action} {package}"
        else:
            return f"[Error] Unknown action: {action}"

        # Safety check
        if not self._is_allowed(manager, action, package if action != "list" else ""):
            return f"[Error] Command not allowed: {cmd}"

        # Execute
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60  # package installs might take time
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                return output if output else "[Command executed successfully, no output]"
            else:
                return f"[Error] {result.stderr.strip()[:500]}"  # limit error length
        except subprocess.TimeoutExpired:
            return "[Error] Command timed out."
        except Exception as e:
            return f"[Error] {str(e)}"
