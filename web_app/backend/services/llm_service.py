"""LLM service using requests (avoids httpx SSL issues in Django)."""
import os, time, json, requests
from django.conf import settings

class LLMClient:
    def __init__(self):
        self._model = None
        self._api_key = None
        self._base_url = None
    
    def _ensure_init(self):
        if self._model:
            return
        provider = getattr(settings, "LLM_PROVIDER", "auto")
        if provider == "deepseek" or (provider == "auto" and settings.DEEPSEEK_API_KEY):
            self._api_key = settings.DEEPSEEK_API_KEY
            self._base_url = settings.DEEPSEEK_BASE_URL.rstrip("/") + "/v1"
            self._model = settings.DEEPSEEK_MODEL
        elif provider == "openai" or (provider == "auto" and settings.OPENAI_API_KEY):
            self._api_key = settings.OPENAI_API_KEY
            self._base_url = settings.OPENAI_BASE_URL
            self._model = settings.OPENAI_MODEL
        else:
            self._model = "mock"
        print(f"[LLM] {self._model}")
    
    @property
    def model_name(self):
        self._ensure_init()
        return self._model
    
    def chat(self, messages: list[dict], temperature: float = 0.3) -> str:
        self._ensure_init()
        if self._model == "mock":
            return "[MockLLM] No API key configured."
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        url = f"{self._base_url}/chat/completions"
        try:
            r = requests.post(url, json=data, headers=headers, timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            raise

llm_client = LLMClient()
