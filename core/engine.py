from core.history import ConversationHistory
from core.agent_loop import AgentLoop
from core.memory import SemanticMemory
from utils.logger import get_logger

logger = get_logger(__name__)

class Engine:
    def __init__(self, provider, history: ConversationHistory, memory: SemanticMemory = None, manager=None):
        self.provider = provider
        self.history = history
        self.memory = memory
        self.manager = manager
        self.agent = AgentLoop(provider, history, memory, manager)

    def process(self, user_input: str) -> str:
        return self.agent.run(user_input)
