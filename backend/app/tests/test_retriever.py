"""Tests for multimodal retrieval and result fusion."""

from __future__ import annotations

import os

import numpy as np
import pytest
from PIL import Image

RUN_SLOW = os.environ.get("RUN_SLOW_TESTS") == "1"


def test_retriever_requires_query():
    from app.services.retriever import MultimodalRetriever

    r = MultimodalRetriever()
    with pytest.raises(ValueError):
        r.retrieve()


def test_retriever_text_only_query_type():
    """Without heavy models we can still verify query-type classification
    by monkeypatching the embedding/vector layers."""
    from app.services import retriever as ret_mod

    r = ret_mod.MultimodalRetriever()

    # monkeypatch to avoid model loading
    calls = {}

    def fake_retrieve_text(text):
        calls["text"] = text
        return []

    def fake_retrieve_images(img, text):
        calls["img"] = img
        return []

    r._retrieve_text = fake_retrieve_text
    r._retrieve_images_via_clip_text = lambda t: []
    r._retrieve_images_via_clip_image = lambda img, text: []
    r._retrieve_text_via_image_captions = lambda hits: []

    out = r.retrieve(text="hello")
    assert out.query_type == "text"
    assert calls["text"] == "hello"


def test_retriever_image_only_query_type():
    from app.services import retriever as ret_mod

    r = ret_mod.MultimodalRetriever()
    r._retrieve_text = lambda t: []
    r._retrieve_images_via_clip_text = lambda t: []
    r._retrieve_images_via_clip_image = lambda img, text: []
    r._retrieve_text_via_image_captions = lambda hits: []

    out = r.retrieve(image=Image.new("RGB", (16, 16)))
    assert out.query_type == "image"


def test_retriever_text_plus_image_query_type():
    from app.services import retriever as ret_mod

    r = ret_mod.MultimodalRetriever()
    r._retrieve_text = lambda t: []
    r._retrieve_images_via_clip_text = lambda t: []
    r._retrieve_images_via_clip_image = lambda img, text: []
    r._retrieve_text_via_image_captions = lambda hits: []

    out = r.retrieve(text="describe", image=Image.new("RGB", (16, 16)))
    assert out.query_type == "text+image"


def test_fusion_merge_dedupes():
    from app.services.retriever import MultimodalRetriever, RetrievalResult

    r = MultimodalRetriever()
    a = RetrievalResult(
        id="x", document_id="d", document_name="p.pdf", page_number=1,
        content_type="text", score=0.5, content="a",
    )
    b = RetrievalResult(
        id="x", document_id="d", document_name="p.pdf", page_number=1,
        content_type="text", score=0.9, content="a",
    )
    c = RetrievalResult(
        id="y", document_id="d", document_name="p.pdf", page_number=2,
        content_type="text", score=0.3, content="c",
    )
    merged = r._merge([a], [b, c])
    assert len(merged) == 2
    # deduped by id, max score kept
    x = [m for m in merged if m.id == "x"][0]
    assert x.score == 0.9


def test_score_threshold_filters():
    from app.services.retriever import MultimodalRetriever, RetrievalResult

    r = MultimodalRetriever(score_threshold=0.5)
    r._retrieve_text = lambda t: [
        RetrievalResult(id="a", document_id="d", document_name="p", page_number=1, content_type="text", score=0.8, content="x"),
        RetrievalResult(id="b", document_id="d", document_name="p", page_number=1, content_type="text", score=0.2, content="y"),
    ]
    r._retrieve_images_via_clip_text = lambda t: []
    r._retrieve_images_via_clip_image = lambda img, text: []
    r._retrieve_text_via_image_captions = lambda hits: []
    out = r.retrieve(text="q")
    assert all(res.score >= 0.5 for res in out.results)


@pytest.mark.skipif(not RUN_SLOW, reason="requires model downloads")
def test_end_to_end_text_retrieval():
    """Full pipeline: embed text, store, retrieve. Slow."""
    from app.services.embedding_service import embedding_service
    from app.services.vector_store import vector_store
    from app.services.retriever import MultimodalRetriever

    vector_store.initialize(text_dim=384, image_dim=512)
    texts = ["the cat sat on the mat", "quantum computing uses qubits", "a recipe for pancakes"]
    vecs = embedding_service.embed_chunks(texts)
    vector_store.upsert_text(
        ids=[f"slow-{i}" for i in range(len(texts))],
        vectors=vecs,
        payloads=[{"document_id": "d", "document_name": "p.pdf", "page_number": i + 1, "content": t} for i, t in enumerate(texts)],
    )
    r = MultimodalRetriever()
    out = r.retrieve(text="feline on a rug")
    assert out.query_type == "text"
    assert out.text_hits >= 1
    assert out.results[0].content_type == "text"
