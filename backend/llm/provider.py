"""
LLM provider abstraction. Agents depend on this interface, not on Gemini
directly — swappable to Groq/Llama 3 later as a config change (M0 decision).
"""
from abc import ABC, abstractmethod

from google import genai

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError


class GeminiLLMProvider(LLMProvider):
    def __init__(self, model: str = "gemini-3.1-flash-lite"):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set — cannot initialize GeminiLLMProvider")
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = model

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            config = {"system_instruction": system_prompt} if system_prompt else {}
            response = self._client.models.generate_content(
                model=self._model, contents=prompt, config=config
            )
            return response.text
        except Exception as exc:
            logger.error(f"Gemini generation call failed: {exc}")
            raise
