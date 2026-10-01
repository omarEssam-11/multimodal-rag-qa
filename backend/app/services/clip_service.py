"""CLIP service — thin domain wrapper around CLIPProvider.

Exists as a separate module so the rest of the app depends on a stable
interface and the underlying CLIP implementation can be swapped without
touching callers.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from app.services.embedding_service import CLIPProvider, embedding_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CLIPService:
    """High-level CLIP operations used by ingestion and retrieval."""

    def __init__(self, provider: CLIPProvider | None = None) -> None:
        self.provider = provider or embedding_service.clip

    def embed_image_file(self, path: Path) -> np.ndarray:
        return self.provider.embed_image(path)

    def embed_image_bytes(self, data: bytes) -> np.ndarray:
        return self.provider.embed_image(data)

    def embed_images_batch(self, paths: list[Path]) -> np.ndarray:
        return self.provider.embed_images(paths)

    def embed_short_text(self, text: str) -> np.ndarray:
        """Embed a short query/caption into CLIP space."""
        return self.provider.embed_text(text)

    def image_to_image_score(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two CLIP vectors (both normalized)."""
        return float(np.dot(a, b))

    def text_to_image_score(self, text_vec: np.ndarray, image_vec: np.ndarray) -> float:
        return float(np.dot(text_vec, image_vec))

    def is_ready(self) -> bool:
        try:
            _ = self.provider.dimension
            return True
        except Exception:
            return False


clip_service = CLIPService()
