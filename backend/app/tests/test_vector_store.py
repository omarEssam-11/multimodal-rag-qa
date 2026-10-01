"""Tests for Qdrant vector store operations (local embedded mode)."""

from __future__ import annotations

import numpy as np
import pytest

from app.services.vector_store import VectorStore, VectorStoreError


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Each test gets an isolated embedded-Qdrant storage dir."""
    from app.config import settings

    monkeypatch.setattr(settings, "qdrant_path", tmp_path / "qdrant")
    vs = VectorStore()
    vs._client = None  # force reconnect with new path
    vs.initialize(text_dim=8, image_dim=8)
    return vs


def test_initialize_creates_collections(store):
    names = {c.name for c in store.client.get_collections().collections}
    from app.config import settings

    assert settings.qdrant_collection_text in names
    assert settings.qdrant_collection_images in names


def test_upsert_and_search_text(store):
    ids = ["a", "b", "c"]
    vecs = np.array(
        [[1, 0, 0, 0, 0, 0, 0, 0], [0.9, 0.1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]],
        dtype=np.float32,
    )
    payloads = [
        {"document_id": "d1", "document_name": "p.pdf", "page_number": 1, "content": "alpha"},
        {"document_id": "d1", "document_name": "p.pdf", "page_number": 2, "content": "beta"},
        {"document_id": "d2", "document_name": "q.pdf", "page_number": 1, "content": "gamma"},
    ]
    store.upsert_text(ids, vecs, payloads)

    q = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
    hits = store.search_text(q, limit=2)
    assert len(hits) == 2
    assert hits[0]["payload"]["content"] == "alpha"
    assert hits[0]["score"] > 0.99


def test_search_text_with_filter(store):
    ids = ["a", "b"]
    vecs = np.array([[1, 0, 0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0]], dtype=np.float32)
    payloads = [
        {"document_id": "d1", "document_name": "p.pdf", "page_number": 1},
        {"document_id": "d2", "document_name": "q.pdf", "page_number": 1},
    ]
    store.upsert_text(ids, vecs, payloads)
    q = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
    hits = store.search_text(q, limit=5, filters={"document_id": "d2"})
    assert len(hits) == 1
    assert hits[0]["payload"]["document_id"] == "d2"


def test_upsert_and_search_images(store):
    ids = ["img1", "img2"]
    vecs = np.array([[0, 0, 1, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0]], dtype=np.float32)
    payloads = [
        {"document_id": "d1", "image_id": "img1", "page_number": 3, "caption": "Figure 1"},
        {"document_id": "d1", "image_id": "img2", "page_number": 4},
    ]
    store.upsert_images(ids, vecs, payloads)
    q = np.array([0, 0, 1, 0, 0, 0, 0, 0], dtype=np.float32)
    hits = store.search_images(q, limit=1)
    assert hits[0]["payload"]["image_id"] == "img1"
    assert hits[0]["payload"]["caption"] == "Figure 1"


def test_delete_document(store):
    ids = ["a", "b"]
    vecs = np.array([[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]], dtype=np.float32)
    payloads = [{"document_id": "d1"}, {"document_id": "d1"}]
    store.upsert_text(ids, vecs, payloads)
    store.delete_document("d1")
    q = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
    hits = store.search_text(q, limit=5)
    assert len(hits) == 0


def test_health_check(store):
    assert store.health_check() is True
