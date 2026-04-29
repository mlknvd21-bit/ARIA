from tools.base import BaseTool
from core.memory import SemanticMemory
from utils.logger import get_logger

logger = get_logger(__name__)

class MemoryTool(BaseTool):
    def __init__(self, memory: SemanticMemory):
        super().__init__(
            name="memory",
            description="Store, recall, search, forget, or list memories. Actions: remember key=value, recall key, search query, forget key, list."
        )
        self.memory = memory

    def execute(self, params: dict) -> str:
        action = params.get("action", "").strip().lower()
        key = params.get("key", "").strip()
        value = params.get("value", "").strip()

        if action == "remember":
            if not key or not value:
                return "[Error] Both key and value required for 'remember'."
            self.memory.remember(key, value)
            return f"Stored: {key} = {value}"

        elif action == "recall":
            if not key:
                return "[Error] Key required for 'recall'."
            result = self.memory.recall(key)
            return result if result else f"No memory found for '{key}'."

        elif action == "search":
            query = params.get("query", key)  # either 'key' or 'query' can be used
            if not query:
                return "[Error] Query required for search."
            results = self.memory.search(query)
            if not results:
                return f"No memories found for '{query}'."
            return "\n".join([f"{k}: {v}" for k, v in results])

        elif action == "forget":
            if not key:
                return "[Error] Key required for 'forget'."
            self.memory.forget(key)
            return f"Forgot: {key}"

        elif action == "list":
            keys = self.memory.all_keys()
            if not keys:
                return "No memories stored yet."
            return "\n".join(keys)

        else:
            return f"[Error] Unknown action: {action}. Allowed: remember, recall, search, forget, list."
