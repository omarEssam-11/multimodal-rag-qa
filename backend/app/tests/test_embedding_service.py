"""Tests for embedding providers (text + CLIP).

These load real pretrained models and are slow. They are marked with
`@pytest.mark.slow` and skipped unless RUN_SLOW_TESTS=1 is set, so the
default test run stays fast. They still run in CI / when explicitly requested.
"""

from __future__ import annotations

import os

import numpy as np
import pytest
from PIL import Image

RUN_SLOW = os.environ.get("RUN_SLOW_TESTS") == "1"
pytestmark = pytest.mark.slow if not RUN_SLOW else pytest.mark.skipif(False, reason="running slow")


def test_text_embedding_shape():
    from app.services.embedding_service import TextEmbeddingProvider

    prov = TextEmbeddingProvider()
    vecs = prov.embed_texts(["hello world", "transformer architecture"])
    assert vecs.shape[0] == 2
    assert vecs.shape[1] == prov.dimension
    assert vecs.dtype == np.float32
    # normalized
    norms = np.linalg.norm(vecs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)


def test_text_embedding_semantic_similarity():
    from app.services.embedding_service import TextEmbeddingProvider

    prov = TextEmbeddingProvider()
    v1 = prov.embed_text("the cat sat on the mat")
    v2 = prov.embed_text("a feline rested on the rug")
    v3 = prov.embed_text("quantum computing uses qubits")
    sim_12 = float(np.dot(v1, v2))
    sim_13 = float(np.dot(v1, v3))
    assert sim_12 > sim_13


def test_clip_text_embedding():
    from app.services.embedding_service import CLIPProvider

    prov = CLIPProvider()
    vec = prov.embed_text("a diagram of a neural network")
    assert vec.shape == (prov.dimension,)
    assert vec.dtype == np.float32
    assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-3)


def test_clip_image_embedding():
    from app.services.embedding_service import CLIPProvider

    prov = CLIPProvider()
    img = Image.new("RGB", (64, 64), color=(200, 50, 50))
    vec = prov.embed_image(img)
    assert vec.shape == (prov.dimension,)
    assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-3)


def test_clip_cross_modal_similarity():
    """CLIP text and image of the same concept should be more similar than unrelated."""
    from app.services.embedding_service import CLIPProvider

    prov = CLIPProvider()
    text_vec = prov.embed_text("a red square")
    img_match = Image.new("RGB", (64, 64), color=(200, 30, 30))
    img_unrelated = Image.new("RGB", (64, 64), color=(30, 30, 200))
    v_match = prov.embed_image(img_match)
    v_unrelated = prov.embed_image(img_unrelated)
    sim_match = float(np.dot(text_vec, v_match))
    sim_unrelated = float(np.dot(text_vec, v_unrelated))
    assert sim_match > sim_unrelated


def test_clip_image_batch():
    from app.services.embedding_service import CLIPProvider

    prov = CLIPProvider()
    imgs = [Image.new("RGB", (32, 32), color=(i * 40, 100, 100)) for i in range(3)]
    vecs = prov.embed_images(imgs)
    assert vecs.shape[0] == 3
    assert vecs.shape[1] == prov.dimension


def test_clip_bytes_input():
    from app.services.embedding_service import CLIPProvider

    prov = CLIPProvider()
    img = Image.new("RGB", (32, 32), color=(10, 200, 10))
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    vec = prov.embed_image(buf.getvalue())
    assert vec.shape == (prov.dimension,)
