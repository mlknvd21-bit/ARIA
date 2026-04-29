import subprocess
from tools.base import BaseTool
from tools.safety import SafetyGuard
from utils.logger import get_logger

logger = get_logger(__name__)

class ShellTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="shell",
            description="Execute a safe shell command. Allowed commands: ls, pwd, echo, date, head, tail, mkdir, touch, cp, mv, rmdir, etc."
        )
        self.guard = SafetyGuard()

    def execute(self, params: dict) -> str:
        command = params.get("command", "").strip()
        if not command:
            return "[Error] No command provided."

        if not self.guard.is_allowed(command):
            return f"[Error] Command not allowed for safety reasons: {command}"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/data/data/com.termux/files/home"
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                return output if output else "[Command executed successfully, no output]"
            else:
                return f"[Error] {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "[Error] Command timed out after 10 seconds."
        except Exception as e:
            return f"[Error] {str(e)}"
