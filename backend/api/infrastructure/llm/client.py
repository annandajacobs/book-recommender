import httpx

from api.core.config import settings


class LlmClient:
    def __init__(self, model: str | None = None):
        self.base_url = settings.ollama_base_url
        self.model = model or settings.llm_model

    def chat_json(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.2},
        }
        with httpx.Client(timeout=180.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
        data = response.json()
        return data["message"]["content"]