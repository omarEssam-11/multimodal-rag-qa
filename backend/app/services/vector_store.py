"""Qdrant vector store abstraction.

Supports two modes:
  - local: embedded Qdrant (no Docker needed), persisted to disk
  - remote: Qdrant server (e.g. via docker-compose)

Two collections are used:
  - text collection: embeddings from the dedicated text model
  - image collection: embeddings from CLIP
"""

from __future__ import annotations

import uuid
from typing import Any, Sequence

import numpy as np
from qdrant_client import QdrantClient, models
from qdrant_client.http import models as rest

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Fixed namespace so string IDs map deterministically to UUIDs
_ID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _to_uuid(point_id: str) -> str:
    """Deterministically convert a string point ID to a valid UUID string."""
    try:
        # already a UUID?
        uuid.UUID(point_id)
        return point_id
    except (ValueError, AttributeError):
        return str(uuid.uuid5(_ID_NAMESPACE, point_id))


class VectorStoreError(Exception):
    pass


class VectorStore:
    def __init__(self) -> None:
        self._client: QdrantClient | None = None
        self._text_dim: int | None = None
        self._image_dim: int | None = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = self._connect()
        return self._client

    def _connect(self) -> QdrantClient:
        if settings.qdrant_mode == "remote":
            logger.info("Connecting to Qdrant at %s:%s", settings.qdrant_host, settings.qdrant_port)
            return QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key or None,
            )
        # local embedded mode
        path = str(settings.qdrant_path)
        logger.info("Using embedded Qdrant at %s", path)
        return QdrantClient(path=path)

    def health_check(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.warning("Qdrant health check failed: %s", e)
            return False

    def initialize(self, text_dim: int, image_dim: int) -> None:
        """Create collections if they don't exist."""
        self._text_dim = text_dim
        self._image_dim = image_dim
        existing = {c.name for c in self.client.get_collections().collections}

        if settings.qdrant_collection_text not in existing:
            self.client.create_collection(
                collection_name=settings.qdrant_collection_text,
                vectors_config=models.VectorParams(
                    size=text_dim, distance=models.Distance.COSINE
                ),
            )
            logger.info("Created text collection (dim=%d)", text_dim)

        if settings.qdrant_collection_images not in existing:
            self.client.create_collection(
                collection_name=settings.qdrant_collection_images,
                vectors_config=models.VectorParams(
                    size=image_dim, distance=models.Distance.COSINE
                ),
            )
            logger.info("Created image collection (dim=%d)", image_dim)

    # ---------------- Text vectors ----------------

    def upsert_text(
        self,
        ids: Sequence[str],
        vectors: np.ndarray,
        payloads: Sequence[dict[str, Any]],
    ) -> None:
        if len(ids) == 0:
            return
        points = [
            rest.PointStruct(id=_to_uuid(idx), vector=vec.tolist(), payload=pl)
            for idx, vec, pl in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=settings.qdrant_collection_text, points=points)

    def search_text(
        self, query_vector: np.ndarray, limit: int = 5, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        query_filter = self._build_filter(filters)
        try:
            results = self.client.query_points(
                collection_name=settings.qdrant_collection_text,
                query=query_vector.tolist(),
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
            ).points
        except Exception as e:
            raise VectorStoreError(f"Text search failed: {e}") from e
        return [
            {
                "id": (p.payload or {}).get("chunk_id") or str(p.id),
                "score": float(p.score),
                "payload": p.payload or {},
            }
            for p in results
        ]

    # ---------------- Image vectors ----------------

    def upsert_images(
        self,
        ids: Sequence[str],
        vectors: np.ndarray,
        payloads: Sequence[dict[str, Any]],
    ) -> None:
        if len(ids) == 0:
            return
        points = [
            rest.PointStruct(id=_to_uuid(idx), vector=vec.tolist(), payload=pl)
            for idx, vec, pl in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=settings.qdrant_collection_images, points=points)

    def search_images(
        self, query_vector: np.ndarray, limit: int = 5, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        query_filter = self._build_filter(filters)
        try:
            results = self.client.query_points(
                collection_name=settings.qdrant_collection_images,
                query=query_vector.tolist(),
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
            ).points
        except Exception as e:
            raise VectorStoreError(f"Image search failed: {e}") from e
        return [
            {
                "id": (p.payload or {}).get("image_id") or str(p.id),
                "score": float(p.score),
                "payload": p.payload or {},
            }
            for p in results
        ]

    # ---------------- Maintenance ----------------

    def delete_document(self, document_id: str) -> None:
        for coll in (settings.qdrant_collection_text, settings.qdrant_collection_images):
            try:
                self.client.delete(
                    collection_name=coll,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="document_id",
                                    match=models.MatchValue(value=document_id),
                                )
                            ]
                        )
                    ),
                )
            except Exception as e:
                logger.warning("Failed to delete points from %s: %s", coll, e)

    def count(self, collection: str) -> int:
        try:
            info = self.client.get_collection(collection=collection)
            return info.points_count or 0
        except Exception:
            return 0

    def _build_filter(self, filters: dict | None) -> rest.Filter | None:
        if not filters:
            return None
        must = []
        for key, value in filters.items():
            if isinstance(value, list):
                must.append(
                    models.FieldCondition(key=key, match=models.MatchAny(any=value))
                )
            else:
                must.append(
                    models.FieldCondition(key=key, match=models.MatchValue(value=value))
                )
        return models.Filter(must=must) if must else None


vector_store = VectorStore()
