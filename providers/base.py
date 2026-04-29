from abc import ABC, abstractmethod
from typing import List, Dict

class BaseProvider(ABC):
    def __init__(self, config: Dict):
        self.config = config

    @abstractmethod
    def complete(self, prompt: str, history: List[Dict]) -> str:
        """Returns the assistant's response as a string."""
        pass

    @abstractmethod
    def chat(self, messages: List[Dict]) -> str:
        """Send a list of messages and return the assistant's response."""
        pass

    @abstractmethod
    def fetch_models(self) -> List[str]:
        """Return list of available model IDs from this provider."""
        pass
