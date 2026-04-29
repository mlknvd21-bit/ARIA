import time
from core.agents.dispatcher import Dispatcher
from core.agents.worker import Worker
from core.agents.critic import Critic
from core.memory import SemanticMemory
from providers.manager import ProviderManager
from utils.logger import get_logger

logger = get_logger(__name__)

class Swarm:
    """Orchestrates multi-agent decomposition, execution, and synthesis."""
    def __init__(self, provider_manager: ProviderManager, memory: SemanticMemory = None):
        self.provider_manager = provider_manager
        self.memory = memory
        # Use active provider for all agents
        self.provider = provider_manager.get_active_provider()

    def run(self, task: str) -> str:
        """Main entry point for swarm execution."""
        start_time = time.time()
        max_time = 45  # seconds

        # Phase 1: Decompose
        logger.info("Swarm: Decomposing task...")
        dispatcher = Dispatcher(self.provider)
        subtasks = dispatcher.decompose(task)
        print(f"📋 Dispatcher: Task broken into {len(subtasks)} subtasks.")

        # Phase 2: Execute each subtask with a Worker
        results = []
        for i, sub in enumerate(subtasks):
            # Check timeout
            if time.time() - start_time > max_time:
                print(f"⏰ Timeout reached. Skipping remaining subtasks.")
                results.append(f"[Timeout: Subtask not executed] {sub['subtask']}")
                continue

            worker_task = sub["subtask"]
            print(f"⚙️  Worker {i+1}/{len(subtasks)}: Solving '{worker_task[:60]}...'")
            worker = Worker(self.provider, self.memory)
            result = worker.execute(worker_task)
            results.append(result)
            print(f"   Worker {i+1} done.")

        # If only one subtask, skip critic and synthesis
        if len(subtasks) <= 1:
            return results[0] if results else "No results."

        # Phase 3: Critic review
        print("🔍 Critic: Reviewing results...")
        critic = Critic(self.provider)
        decision = critic.review(subtasks, results)

        # If retry requested, re-execute the specific subtask
        if decision.get("status") == "retry":
            retry_idx = decision.get("retry_index", 0)
            feedback = decision.get("feedback", "Improve the answer.")
            if 0 <= retry_idx < len(subtasks):
                print(f"🔄 Retrying subtask {retry_idx+1} with feedback: {feedback}")
                improved_task = f"{subtasks[retry_idx]['subtask']}\n\nAdditional feedback: {feedback}"
                worker = Worker(self.provider, self.memory)
                results[retry_idx] = worker.execute(improved_task)

        # Phase 4: Synthesize final answer
        print("🧠 Dispatcher: Synthesizing final answer...")
        final_answer = dispatcher.synthesize(results)

        elapsed = time.time() - start_time
        print(f"✅ Swarm completed in {elapsed:.1f}s")
        return final_answer
