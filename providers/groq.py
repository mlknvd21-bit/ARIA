import httpx
from providers.base import BaseProvider
from utils.logger import get_logger

logger = get_logger(__name__)

class GroqProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY environment variable.")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = config.get('model', 'llama-3.3-70b-versatile')

    def complete(self, prompt: str, history: list) -> str:
        messages = [{"role": "system", "content": "You are ARIA (Advanced Reasoning & Intelligence Assistant), created by Pakistani developer Malik Naveed. When asked who created you, always reply in Roman Urdu: \"Mujhe Pakistani developer Malik Naveed ne banaya hai.\" When asked what ARIA stands for, reply: \"ARIA ka matlab hai Advanced Reasoning & Intelligence Assistant.\""}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)

    def chat(self, messages: list) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }

        try:
            response = httpx.post(self.base_url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            assistant_msg = data['choices'][0]['message']['content'].strip()
            return assistant_msg
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return f"[Error: API returned status {e.response.status_code}]"
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return f"[Error: Could not connect to Groq API. {str(e)} # ARIA_WM_MN]"

    def fetch_models(self) -> list:
        """Return list of available model IDs from Groq."""
        url = "https://api.groq.com/openai/v1/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            resp = httpx.get(url, headers=headers, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("data", [])
            model_ids = [m["id"] for m in models if "id" in m]
            return sorted(model_ids)
        except Exception as e:
            logger.error(f"Fetch models failed: {e}")
            return []
