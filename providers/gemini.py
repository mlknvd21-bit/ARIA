import httpx
from providers.base import BaseProvider
from utils.logger import get_logger

logger = get_logger(__name__)

class GeminiProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = config.get('model', 'gemini-2.0-flash')

    def _build_contents(self, messages: list) -> list:
        contents = []
        system_text = ""
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_text = content
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
        return contents, system_text

    def complete(self, prompt: str, history: list) -> str:
        msgs = [{"role": "system", "content": "You are ARIA (Advanced Reasoning & Intelligence Assistant), created by Pakistani developer Malik Naveed. When asked who created you, always reply in Roman Urdu: \"Mujhe Pakistani developer Malik Naveed ne banaya hai.\" When asked what ARIA stands for, reply: \"ARIA ka matlab hai Advanced Reasoning & Intelligence Assistant.\""}]
        msgs.extend(history)
        msgs.append({"role": "user", "content": prompt})
        return self.chat(msgs)

    def chat(self, messages: list) -> str:
        contents, system_text = self._build_contents(messages)
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": contents,
        }
        if system_text:
            payload["systemInstruction"] = {
                "parts": [{"text": system_text}]
            }

        params = {"key": self.api_key}

        try:
            response = httpx.post(url, json=payload, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return "[Error: No response from Gemini]"
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            text = "".join(part.get("text", "") for part in parts)
            return text.strip() if text else "[Gemini returned empty response]"
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini HTTP error: {e.response.status_code} - {e.response.text}")
            return f"[Error: Gemini API returned status {e.response.status_code}]"
        except Exception as e:
            logger.error(f"Gemini request failed: {str(e)}")
            return f"[Error: Could not connect to Gemini. {str(e)}]"

    def fetch_models(self) -> list:
        url = f"{self.base_url}/models"
        params = {"key": self.api_key}
        try:
            resp = httpx.get(url, params=params, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            model_ids = [m["name"].replace("models/", "") for m in models if "name" in m]
            return sorted(model_ids)
        except Exception as e:
            logger.error(f"Gemini model fetch failed: {e}")
            return []
