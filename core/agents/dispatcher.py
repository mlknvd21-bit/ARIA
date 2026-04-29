import json
from utils.logger import get_logger
from utils.rate_limiter import RateLimiter

logger = get_logger(__name__)

class Dispatcher:
    def __init__(self, provider):
        self.provider = provider
        self.rate_limiter = RateLimiter(min_interval=0.7)

    def decompose(self, task: str) -> list:
        prompt = f"""Break the following complex task into 2-3 small, independent subtasks.
Each subtask should be a single sentence that can be solved without knowing the others.
Return your answer ONLY as a valid JSON array of objects, like this:
[
  {{"subtask": "Find current weather in Lahore"}},
  {{"subtask": "Identify two famous foods of Lahore"}},
  {{"subtask": "Provide names of those foods in Urdu"}}
]

IMPORTANT CONTEXT:
- If the task mentions "mausam" or "weather", always make one subtask to find the current weather using real-time data.
- If the task mentions "khanay" (foods/dishes), always treat it as food/cuisine, NEVER as caves/mines.
- The original task may be in Roman Urdu; understand the meaning accordingly.

Task: {task}"""

        messages = [
            {"role": "system", "content": "You are a task decomposition expert. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]

        self.rate_limiter.wait_sync()
        response = self.provider.chat(messages)

        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                subtasks = json.loads(json_str)
                if isinstance(subtasks, list) and len(subtasks) > 0:
                    valid = [s for s in subtasks if isinstance(s, dict) and "subtask" in s]
                    if valid:
                        logger.info(f"Decomposed into {len(valid)} subtasks.")
                        return valid
            logger.warning("Decomposition parsing failed, using original task as single subtask.")
            return [{"subtask": task}]
        except Exception as e:
            logger.error(f"Decomposition error: {e}")
            return [{"subtask": task}]

    def _is_urdu_or_roman_urdu(self, task: str) -> bool:
        """Detect if the task is likely in Urdu or Roman Urdu."""
        # Simple heuristic: check for common Urdu/Roman Urdu words
        urdu_words = ["mausam", "khanay", "khao", "peeno", "aaj", "kal", "abhi",
                      "yeh", "woh", "ka", "ki", "kya", "hai", "hain", "hun", "ho",
                      "batao", "sunao", "dikhao", "chahiye", "zaroor", "shukriya"]
        lower_task = task.lower()
        return any(word in lower_task for word in urdu_words)

    def synthesize(self, results: list, original_task: str = "") -> str:
        """Combine worker results into a final answer, in Urdu if original task was Urdu."""
        if not results:
            return "کوئی نتیجہ دستیاب نہیں ہے۔"

        results_text = "\n---\n".join([f"Result {i+1}: {r}" for i, r in enumerate(results)])
        
        language_instruction = ""
        if self._is_urdu_or_roman_urdu(original_task):
            language_instruction = "IMPORTANT: The original task was in Roman Urdu/Urdu. Write the final answer in Urdu (using Urdu script, الفاظ اردو میں لکھیں)."

        prompt = f"""Combine the following partial results into a single, well-organized, helpful answer.
Write in a natural, conversational tone. If any result is missing or incomplete, acknowledge it briefly.
{language_instruction}

Partial results:
{results_text}

Final answer:"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant that synthesizes multiple results into one coherent answer."},
            {"role": "user", "content": prompt}
        ]

        self.rate_limiter.wait_sync()
        response = self.provider.chat(messages)
        return response.strip() if response else "ترکیب ناکام رہی۔"
