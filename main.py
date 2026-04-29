import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.loader import Config
from core.history import ConversationHistory
from core.memory import SemanticMemory
from core.engine import Engine
from core.builder import Builder
from core.swarm import Swarm
from ui.cli import CLI
from providers.manager import ProviderManager
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    if "--web" in sys.argv:
        from ui.web.server import create_web_app
        app, manager, memory = create_web_app()
        print("Starting ARIA Web GUI on http://0.0.0.0:8000")
        app.run(host='0.0.0.0', port=8000, debug=False)
    else:
        config = Config()
        try:
            manager = ProviderManager()
            provider = manager.get_active_provider()
        except Exception as e:
            logger.error(f"Failed to initialize providers: {e}")
            sys.exit(1)

        memory = SemanticMemory()
        history = ConversationHistory()
        engine = Engine(provider, history, memory, manager)
        builder = Builder(manager)
        swarm = Swarm(manager, memory)  # Swarm instance
        cli = CLI(engine, manager, memory, builder, swarm)
        cli.run()

if __name__ == "__main__":
    main()
