"""LLM/VLM provider abstraction.

- BaseLLMProvider: interface
- OllamaProvider: local models via Ollama (supports vision models like llava)
- OpenAICompatibleProvider: any OpenAI-compatible endpoint (OpenRouter, etc.)

The provider builds a multimodal message (text + images) and returns a
grounded answer. Retrieval is fully separated from generation.
"""

from __future__ import annotations

import base64
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import httpx
from PIL import Image

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    pass


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str
    images: list[str] = field(default_factory=list)  # base64 data URLs


class BaseLLMProvider(ABC):
    model: str

    @abstractmethod
    def generate(
        self,
        messages: Sequence[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        raise NotImplementedError

    def _image_to_data_url(self, image: Image.Image | Path | bytes | str) -> str:
        if isinstance(image, (str, Path)):
            p = Path(image)
            data = p.read_bytes()
            ext = p.suffix.lstrip(".")
            mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
            return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        if isinstance(image, bytes):
            return f"data:image/png;base64,{base64.b64encode(image).decode()}"
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

    @staticmethod
    def _data_url_to_b64(data_url: str) -> str:
        """Strip the data URL prefix, leaving raw base64 for Ollama."""
        if data_url.startswith("data:"):
            return data_url.split(",", 1)[1]
        return data_url

    def _supports_vision(self) -> bool:
        """Heuristic: only known vision models can accept image inputs."""
        vision_keywords = ("llava", "vision", "vl", "bakllava", "moondream", "llava-phi3")
        return any(k in self.model.lower() for k in vision_keywords)


class OllamaProvider(BaseLLMProvider):
    """Local vision-language models served by Ollama (e.g. llava:7b)."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.llm_model

    def generate(
        self,
        messages: Sequence[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        ollama_messages = []
        for m in messages:
            # Ollama uses a separate `images` field with RAW base64 (no data URL prefix).
            msg: dict = {"role": m.role, "content": m.content}
            if m.images and self._supports_vision():
                msg["images"] = [self._data_url_to_b64(img) for img in m.images]
            ollama_messages.append(msg)

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else settings.llm_temperature,
                "num_predict": max_tokens or settings.llm_max_tokens,
            },
        }
        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=settings.llm_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Ollama error {e.response.status_code}: {e.response.text[:300]}") from e
        except httpx.RequestError as e:
            raise LLMError(f"Cannot reach Ollama at {self.base_url}: {e}") from e


class OpenAICompatibleProvider(BaseLLMProvider):
    """Any OpenAI-compatible chat-completions endpoint (OpenRouter, etc.)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.model = model or settings.openai_model

    def generate(
        self,
        messages: Sequence[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if not self.api_key:
            raise LLMError("OPENAI_API_KEY is not set")

        chat_messages = []
        for m in messages:
            content: str | list[dict] = m.content
            if m.images:
                parts = [{"type": "text", "text": m.content}]
                for img in m.images:
                    parts.append({"type": "image_url", "image_url": {"url": img}})
                content = parts
            chat_messages.append({"role": m.role, "content": content})

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "temperature": temperature if temperature is not None else settings.llm_temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=settings.llm_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            raise LLMError(f"LLM API error {e.response.status_code}: {e.response.text[:300]}") from e
        except (httpx.RequestError, KeyError) as e:
            raise LLMError(f"LLM request failed: {e}") from e


def images_in(messages: Sequence[ChatMessage]) -> list[str]:
    out: list[str] = []
    for m in messages:
        out.extend(m.images)
    return out


def get_llm_provider() -> BaseLLMProvider:
    if settings.llm_provider == "ollama":
        return OllamaProvider()
    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleProvider()
    raise LLMError(f"Unknown LLM provider: {settings.llm_provider}")
