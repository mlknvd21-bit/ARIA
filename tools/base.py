from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> str:
        """Execute the tool and return result string."""
        pass

    def schema(self) -> Dict:
        """Return JSON schema for the tool's parameters (optional)."""
        return {}
