import os
from tools.base import BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)

class FileSystemTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="filesystem",
            description="Read, write, create, or list files within the home directory."
        )
        self.allowed_base = os.path.expanduser("~")

    def _is_allowed_path(self, path: str) -> bool:
        # Resolve real path and check if inside allowed_base
        try:
            real_path = os.path.realpath(path)
            return real_path.startswith(self.allowed_base + os.sep) or real_path == self.allowed_base
        except Exception:
            return False

    def execute(self, params: dict) -> str:
        action = params.get("action", "")
        target = params.get("path", "")
        content = params.get("content", None)

        # Build full path safely
        if target.startswith("~"):
            target = os.path.expanduser(target)
        elif not target.startswith("/"):
            target = os.path.join(self.allowed_base, target)

        if not self._is_allowed_path(target):
            return f"[Error] Path not allowed: {target}"

        try:
            if action == "read":
                if not os.path.isfile(target):
                    return f"[Error] Not a file: {target}"
                with open(target, "r") as f:
                    data = f.read(4096)  # read at most 4KB
                return data if data else "[File is empty]"

            elif action == "write":
                if content is None:
                    return "[Error] No content provided."
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w") as f:
                    f.write(content)
                return f"File written successfully: {target}"

            elif action == "list":
                if not os.path.isdir(target):
                    return f"[Error] Not a directory: {target}"
                items = os.listdir(target)
                return "\n".join(items) if items else "[Directory is empty]"

            elif action == "exists":
                return "true" if os.path.exists(target) else "false"

            elif action == "mkdir":
                os.makedirs(target, exist_ok=True)
                return f"Directory created: {target}"

            elif action == "delete":
                if os.path.isfile(target):
                    os.remove(target)
                    return f"File deleted: {target}"
                elif os.path.isdir(target):
                    os.rmdir(target)  # only empty dir
                    return f"Directory deleted: {target}"
                else:
                    return "[Error] Path does not exist."

            else:
                return f"[Error] Unknown action: {action}"
        except Exception as e:
            return f"[Error] {str(e)}"
