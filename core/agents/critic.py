import json
from utils.logger import get_logger
from utils.rate_limiter import RateLimiter

logger = get_logger(__name__)

class Critic:
    """Reviews results of worker agents and requests re-execution if needed."""
    def __init__(self, provider):
        self.provider = provider
        self.rate_limiter = RateLimiter(min_interval=0.7)

    def review(self, subtasks: list, results: list) -> dict:
        """
        Analyze if all subtasks are adequately solved.
        subtasks: list of dicts [{"subtask": "..."}, ...]
        results: list of strings (corresponding worker answers)
        Returns: dict with keys "status" ("complete" or "retry") and "retry_index" (optional).
        """
        if not subtasks or not results:
            return {"status": "complete"}

        # Prepare input for LLM
        pairs = []
        for i, (sub, res) in enumerate(zip(subtasks, results)):
            task_text = sub.get("subtask", "")
            pairs.append(f"Subtask {i+1}: {task_text}\nWorker Result: {res}")

        pairs_text = "\n---\n".join(pairs)

        prompt = f"""Review the following subtask results. Check if each subtask is completely and correctly solved.
If all are solved, respond with: {{"status": "complete"}}
If any subtask needs re-execution (e.g., empty, irrelevant, or wrong), respond with:
{{"status": "retry", "retry_index": <index of the failed subtask (0-based)>, "feedback": "<what needs to be improved>"}}
Only one retry at a time. Choose the most critical failure if multiple.

{pairs_text}"""

        messages = [
            {"role": "system", "content": "You are a strict quality reviewer. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]

        self.rate_limiter.wait_sync()
        response = self.provider.chat(messages)

        # Parse JSON from response
        try:
            # Locate JSON object
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                decision = json.loads(json_str)
                if isinstance(decision, dict) and "status" in decision:
                    logger.info(f"Critic decision: {decision}")
                    return decision
        except Exception as e:
            logger.error(f"Critic parsing error: {e}")

        # Default: consider complete
        return {"status": "complete"}
