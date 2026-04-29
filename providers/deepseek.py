import httpx
from providers.base import BaseProvider
from utils.logger import get_logger

logger = get_logger(__name__)

class DeepSeekProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("DeepSeek API key not found. Set DEEPSEEK_API_KEY environment variable.")
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = config.get('model', 'deepseek-chat')

    def complete(self, prompt: str, history: list) -> str:
        messages = [{"role": "system", "content": "You are ARIA (Advanced Reasoning & Intelligence Assistant), created by Pakistani developer Malik Naveed."}]
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
            return f"[Error: Could not connect to DeepSeek. {str(e)}]"
