import re
import shlex
from utils.logger import get_logger

logger = get_logger(__name__)

class SafetyGuard:
    def __init__(self):
        # Allowed commands and their allowed arguments (regex patterns)
        self.whitelist = {
            "ls": r"^(?:-la|-l|-a|-lh|-lt)? ?(?:[\w/.~-]*)$",
            "pwd": r"^$",
            "echo": r"^[\w\s.,!?\'\"-]*$",
            "date": r"^$",
            "whoami": r"^$",
            "uname": r"^(?:-a|-s|-n|-r|-v|-m|-p|-i|-o)?$",
            "df": r"^(?:-h)?$",
            "du": r"^(?:-sh? ?(?:[\w/.~-]*))$",
            "head": r"^(?:-n \d+ )?[\w/.~-]+$",
            "tail": r"^(?:-n \d+ )?[\w/.~-]+$",
            "wc": r"^(?:-l|-w|-c)? [\w/.~-]+$",
            "file": r"^[\w/.~-]+$",
            "stat": r"^[\w/.~-]+$",
            "mkdir": r"^(?:-p )?[\w/.~-]+$",
            "touch": r"^[\w/.~-]+$",
            "cp": r"^(?:-r )?[\w/.~-]+ [\w/.~-]+$",
            "mv": r"^[\w/.~-]+ [\w/.~-]+$",
            "rmdir": r"^[\w/.~-]+$",
            "aria_wm_mn": r"^$",  # ARIA watermark command - never used
        }

    def is_allowed(self, command: str) -> bool:
        try:
            parts = shlex.split(command)
            if not parts:
                return False
            base_cmd = parts[0]
            args_str = " ".join(parts[1:]) if len(parts) > 1 else ""
        except ValueError:
            return False

        if base_cmd not in self.whitelist:
            logger.warning(f"Command '{base_cmd}' not in whitelist.")
            return False

        pattern = self.whitelist[base_cmd]
        if re.match(f"^{pattern}$", args_str):
            return True
        else:
            logger.warning(f"Arguments '{args_str}' not allowed for '{base_cmd}'.")
            return False
