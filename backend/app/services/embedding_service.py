"""Embedding provider abstraction.

- BaseEmbeddingProvider: common interface
- TextEmbeddingProvider: dedicated sentence-transformer for long text chunks
- CLIPProvider: CLIP for cross-modal text<->image embeddings

All providers return normalized float32 vectors so cosine similarity == dot product.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseEmbeddingProvider(ABC):
    """Interface for all embedding providers."""

    model_name: str
    dimension: int

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        """Embed a batch of texts. Returns (n, dim) float32 array."""
        raise NotImplementedError

    def embed_text(self, text: str) -> np.ndarray:
        return self.embed_texts([text])[0]


class TextEmbeddingProvider(BaseEmbeddingProvider):
    """Dedicated text embedding model for long document chunks.

    Uses sentence-transformers (all-MiniLM-L6-v2 by default) which is
    optimized for semantic textual similarity over paragraphs/chunks.
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.model_name = model_name or settings.text_embedding_model
        self.device = device or settings.embedding_device
        self.batch_size = batch_size or settings.embedding_batch_size
        self._model = None
        self.dimension = 384  # all-MiniLM-L6-v2

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading text embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name, device=self.device)
            self.dimension = int(self._model.get_sentence_embedding_dimension())
        return self._model

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        model = self._load()
        vecs = model.encode(
            list(texts),
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype=np.float32)


class CLIPProvider(BaseEmbeddingProvider):
    """CLIP-based provider for cross-modal embeddings.

    Embeds both images and short text into the SAME vector space, enabling:
      - image -> image similarity
      - text -> image similarity
      - image -> text similarity

    Uses sentence-transformers' CLIP implementation (clip-ViT-B-32).
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.model_name = model_name or settings.clip_model
        self.device = device or settings.embedding_device
        self.batch_size = batch_size or settings.embedding_batch_size
        self._model = None
        self.dimension = 512  # clip-ViT-B-32

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading CLIP model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name, device=self.device)
            self.dimension = self._infer_dimension()
        return self._model

    def _infer_dimension(self) -> int:
        """CLIP models may return None from get_sentence_embedding_dimension()."""
        dim = self._model.get_sentence_embedding_dimension()
        if dim is not None:
            return int(dim)
        # Try to read the projection dimension from the text model config
        try:
            for module in self._model:
                cfg = getattr(module, "config", None)
                proj = getattr(cfg, "projection_dim", None)
                if proj:
                    return int(proj)
        except Exception:
            pass
        # Fallback: run a tiny encode to measure the output width
        vec = self._model.encode(
            ["test"], convert_to_numpy=True, show_progress_bar=False
        )
        return int(vec.shape[1])

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        """Embed short texts / cross-modal queries into CLIP space."""
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        model = self._load()
        vecs = model.encode(
            list(texts),
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype=np.float32)

    def embed_images(self, images: Sequence[Image.Image | str | Path | bytes]) -> np.ndarray:
        """Embed images into CLIP space (same space as embed_texts)."""
        if not images:
            return np.zeros((0, self.dimension), dtype=np.float32)
        model = self._load()
        loaded = [self._to_pil(img) for img in images]
        vecs = model.encode(
            loaded,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype=np.float32)

    def embed_image(self, image: Image.Image | str | Path | bytes) -> np.ndarray:
        return self.embed_images([image])[0]

    @staticmethod
    def _to_pil(image: Image.Image | str | Path | bytes) -> Image.Image:
        if isinstance(image, Image.Image):
            img = image
        elif isinstance(image, (str, Path)):
            img = Image.open(image)
        elif isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        else:
            raise TypeError(f"Unsupported image type: {type(image)}")
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img


class EmbeddingService:
    """Facade that owns the text and CLIP providers."""

    def __init__(self) -> None:
        self._text: TextEmbeddingProvider | None = None
        self._clip: CLIPProvider | None = None

    @property
    def text(self) -> TextEmbeddingProvider:
        if self._text is None:
            self._text = TextEmbeddingProvider()
        return self._text

    @property
    def clip(self) -> CLIPProvider:
        if self._clip is None:
            self._clip = CLIPProvider()
        return self._clip

    def embed_chunks(self, texts: Sequence[str]) -> np.ndarray:
        return self.text.embed_texts(texts)

    def embed_query_text(self, text: str) -> np.ndarray:
        """Short cross-modal query text -> CLIP space."""
        return self.clip.embed_text(text)

    def embed_query_image(self, image: Image.Image | bytes) -> np.ndarray:
        return self.clip.embed_image(image)

    def embed_document_images(self, paths: Sequence[Path]) -> np.ndarray:
        return self.clip.embed_images(paths)


embedding_service = EmbeddingService()
