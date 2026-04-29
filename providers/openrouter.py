import httpx
from providers.base import BaseProvider
from utils.logger import get_logger

logger = get_logger(__name__)

class OpenRouterProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = config.get('model', 'openai/gpt-3.5-turbo')

    def complete(self, prompt: str, history: list) -> str:
        messages = [{"role": "system", "content": "You are ARIA (Advanced Reasoning & Intelligence Assistant), created by Pakistani developer Malik Naveed."}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)

    def chat(self, messages: list) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "ARIA Assistant"
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
            choice = data.get('choices', [{}])[0]
            msg = choice.get('message', {})
            content = msg.get('content', '').strip()
            if not content and 'error' in data:
                return f"[Error] {data['error'].get('message', 'Unknown')}"
            return content if content else "[No response content]"
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return f"[Error: API returned status {e.response.status_code}]"
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return f"[Error: Could not connect to OpenRouter. {str(e)}]"
