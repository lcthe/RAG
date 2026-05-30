"""API-compatible LLM service supporting multiple providers."""
import os, time, sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from openai import AsyncOpenAI
from web_app.backend.app.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
)


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0


class BaseLLM(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    async def chat(self, messages: list[dict], temperature: float = 0.7) -> LLMResponse: ...


class OpenAICompatibleLLM(BaseLLM):
    """Generic OpenAI-compatible API client."""

    def __init__(self, api_key: str, base_url: str, model: str, provider_name: str = "openai"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/") + "/v1" if "/v1" not in base_url else base_url
        self._model = model
        self._provider = provider_name
        self._client: AsyncOpenAI | None = None

    @property
    def model_name(self) -> str:
        return self._model

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        return self._client

    async def chat(self, messages: list[dict], temperature: float = 0.7) -> LLMResponse:
        start = time.time()
        client = self._get_client()
        r = await client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
        )
        return LLMResponse(
            content=r.choices[0].message.content or "",
            model=self._model,
            tokens_used=r.usage.total_tokens if r.usage else 0,
            latency_ms=(time.time() - start) * 1000,
        )


class MockLLM(BaseLLM):
    """Fallback mock LLM when no API key is configured."""

    @property
    def model_name(self) -> str:
        return "mock-llm"

    async def chat(self, messages: list[dict], temperature: float = 0.7) -> LLMResponse:
        start = time.time()
        question = ""
        context = ""
        for m in messages:
            if m["role"] == "user":
                question = m["content"]
            if m["role"] == "system":
                context = m["content"]
        if not context or "[未检索到相关内容]" in context:
            answer = "根据现有知识库，暂时无法回答该问题。"
        else:
            lines = [l.strip() for l in context.split("\\n") if l.strip()]
            answer = "根据知识库信息:\\n\\n" + "\\n".join(lines[:5])
        return LLMResponse(
            content=answer,
            model=self.model_name,
            latency_ms=(time.time() - start) * 1000,
        )


# ---- Factory ----

def get_llm(provider: str | None = None) -> BaseLLM:
    provider = provider or LLM_PROVIDER

    if provider == "openai" and OPENAI_API_KEY:
        return OpenAICompatibleLLM(OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, "openai")

    if provider == "deepseek" and DEEPSEEK_API_KEY:
        return OpenAICompatibleLLM(DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, "deepseek")

    if provider == "ollama" and OLLAMA_BASE_URL:
        return OpenAICompatibleLLM("ollama", OLLAMA_BASE_URL, OLLAMA_MODEL, "ollama")

    if provider == "auto":
        if OPENAI_API_KEY:
            return OpenAICompatibleLLM(OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, "openai")
        if DEEPSEEK_API_KEY:
            return OpenAICompatibleLLM(DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, "deepseek")
        print("[INFO] No API key found, using MockLLM")
        return MockLLM()

    if provider == "mock" or not provider:
        return MockLLM()

    raise ValueError(f"Unsupported LLM provider: {provider}")
