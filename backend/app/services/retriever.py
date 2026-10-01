"""Multimodal retrieval with result fusion.

Supports:
  - text-only query
  - image-only query
  - text + image query

Fusion: final_score = text_score * text_weight + clip_score * image_weight

Cross-modal retrieval is real:
  - text -> CLIP text encoder -> image collection  (text finds figures)
  - image -> CLIP image encoder -> image collection (image finds figures)
  - image -> CLIP -> image captions -> text model -> text collection
    (two-hop: an image query retrieves semantically related TEXT)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from PIL import Image

from app.config import settings
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.utils.logger import get_logger

logger = get_logger(__name__)

QueryType = Literal["text", "image", "text+image"]


@dataclass
class RetrievalResult:
    id: str
    document_id: str
    document_name: str
    page_number: int
    content_type: str  # "text" | "image"
    score: float
    content: str
    image_url: str | None = None
    caption: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievalOutput:
    query_type: QueryType
    results: list[RetrievalResult]
    text_hits: int
    image_hits: int
    retrieval_ms: float
    text_weight: float
    image_weight: float


class MultimodalRetriever:
    def __init__(
        self,
        top_k_text: int | None = None,
        top_k_images: int | None = None,
        text_weight: float | None = None,
        image_weight: float | None = None,
        score_threshold: float | None = None,
    ) -> None:
        self.top_k_text = top_k_text or settings.top_k_text
        self.top_k_images = top_k_images or settings.top_k_images
        self.text_weight = (
            settings.text_retrieval_weight if text_weight is None else text_weight
        )
        self.image_weight = (
            settings.image_retrieval_weight if image_weight is None else image_weight
        )
        self.score_threshold = (
            settings.score_threshold if score_threshold is None else score_threshold
        )

    def retrieve(
        self,
        text: str | None = None,
        image: Image.Image | bytes | None = None,
    ) -> RetrievalOutput:
        start = time.perf_counter()
        has_text = bool(text and text.strip())
        has_image = image is not None

        if has_text and has_image:
            query_type: QueryType = "text+image"
        elif has_image:
            query_type = "image"
        elif has_text:
            query_type = "text"
        else:
            raise ValueError("At least one of text or image must be provided")

        text_results: list[RetrievalResult] = []
        image_results: list[RetrievalResult] = []

        if has_text:
            # text -> text model -> text collection
            text_results = self._retrieve_text(text.strip())
            # text -> CLIP text encoder -> image collection (cross-modal)
            clip_image_hits = self._retrieve_images_via_clip_text(text.strip())
            image_results = self._merge(image_results, clip_image_hits)

        if has_image:
            # image -> CLIP image encoder -> image collection
            clip_hits = self._retrieve_images_via_clip_image(image, text.strip() if has_text else None)
            image_results = self._merge(image_results, clip_hits)
            # two-hop: image -> CLIP -> captions -> text model -> text collection
            hop_text = self._retrieve_text_via_image_captions(clip_hits)
            text_results = self._merge(text_results, hop_text)

        # Apply threshold and cap
        text_results = [r for r in text_results if r.score >= self.score_threshold][
            : self.top_k_text
        ]
        image_results = [r for r in image_results if r.score >= self.score_threshold][
            : self.top_k_images
        ]

        elapsed = (time.perf_counter() - start) * 1000.0
        logger.info(
            "Retrieval: type=%s | text_hits=%d | image_hits=%d | %.1fms",
            query_type,
            len(text_results),
            len(image_results),
            elapsed,
        )
        return RetrievalOutput(
            query_type=query_type,
            results=text_results + image_results,
            text_hits=len(text_results),
            image_hits=len(image_results),
            retrieval_ms=elapsed,
            text_weight=self.text_weight,
            image_weight=self.image_weight,
        )

    # ---------------- Text retrieval ----------------

    def _retrieve_text(self, text: str) -> list[RetrievalResult]:
        """Text query -> text embedding model -> text collection."""
        vec = embedding_service.embed_chunks([text])[0]
        hits = vector_store.search_text(vec, limit=self.top_k_text * 2)
        return [self._to_result(h, "text") for h in hits]

    def _retrieve_text_via_image_captions(
        self, image_hits: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        """Two-hop cross-modal: image query -> CLIP image hits -> their captions
        -> text embedding model -> text collection.

        This lets an image-only query retrieve semantically related TEXT.
        """
        captions = [r.caption for r in image_hits if r.caption]
        if not captions:
            return []
        vecs = embedding_service.embed_chunks(captions)
        out: list[RetrievalResult] = []
        for cap, vec in zip(captions, vecs):
            hits = vector_store.search_text(vec, limit=2)
            out.extend(self._to_result(h, "text") for h in hits)
        return out

    # ---------------- Image retrieval ----------------

    def _retrieve_images_via_clip_text(self, text: str) -> list[RetrievalResult]:
        """Text query -> CLIP text encoder -> image collection (cross-modal)."""
        vec = embedding_service.embed_query_text(text)
        hits = vector_store.search_images(vec, limit=self.top_k_images * 2)
        return [self._to_result(h, "image") for h in hits]

    def _retrieve_images_via_clip_image(
        self, image: Image.Image | bytes, text: str | None
    ) -> list[RetrievalResult]:
        """Image query -> CLIP image encoder -> image collection.

        If text is also present, blend the CLIP text and image vectors so the
        query is truly multimodal.
        """
        img_vec = embedding_service.embed_query_image(image)
        if text:
            txt_vec = embedding_service.embed_query_text(text)
            blended = img_vec + txt_vec
            norm = np.linalg.norm(blended)
            if norm > 0:
                blended = blended / norm
            img_vec = blended
        hits = vector_store.search_images(img_vec, limit=self.top_k_images * 2)
        return [self._to_result(h, "image") for h in hits]

    # ---------------- Fusion ----------------

    def _merge(
        self, primary: list[RetrievalResult], secondary: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        """Merge two hit lists, deduping by id and taking max score."""
        by_id: dict[str, RetrievalResult] = {}
        for r in primary:
            by_id[r.id] = r
        for r in secondary:
            if r.id in by_id:
                by_id[r.id] = max(by_id[r.id], r, key=lambda x: x.score)
            else:
                by_id[r.id] = r
        return sorted(by_id.values(), key=lambda x: x.score, reverse=True)

    def _to_result(self, hit: dict, content_type: str) -> RetrievalResult:
        p = hit["payload"]
        image_url = None
        if content_type == "image":
            image_url = f"/api/images/{p.get('image_id', hit['id'])}"
        return RetrievalResult(
            id=hit["id"],
            document_id=p.get("document_id", ""),
            document_name=p.get("document_name", "Unknown"),
            page_number=p.get("page_number", 0),
            content_type=content_type,
            score=hit["score"],
            content=p.get("content") or p.get("caption") or "",
            image_url=image_url,
            caption=p.get("caption"),
            metadata=p,
        )


retriever = MultimodalRetriever()
