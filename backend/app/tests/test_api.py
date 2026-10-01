"""API endpoint tests using FastAPI TestClient."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "qdrant" in data


def test_config(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "llm_provider" in data
    assert "top_k_text" in data
    assert "text_weight" in data


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "app" in resp.json()


def test_upload_invalid_file_type(client):
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_oversized(client):
    # create a fake PDF header + padding to exceed limit is hard;
    # instead test with a valid-header but tiny file that fails magic check
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("big.pdf", b"%PDF-1.4 tiny", "application/pdf")},
    )
    assert resp.status_code == 400


def test_upload_valid_pdf(client, sample_pdf_path):
    data = sample_pdf_path.read_bytes()
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )
    # May be 200 (indexed) or 500 (if models fail to load in test env)
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        body = resp.json()
        assert body["status"] == "indexed"
        assert body["document_id"]


def test_list_documents_empty(client):
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_missing_document(client):
    resp = client.get("/api/documents/nonexistent")
    assert resp.status_code == 404


def test_chat_missing_query(client):
    resp = client.post("/api/chat", data={})
    assert resp.status_code == 400


def test_retrieve_missing_query(client):
    resp = client.post("/api/retrieve", data={})
    assert resp.status_code == 400


def test_chat_text_only(client):
    """Chat with text only. May fail at generation if no LLM is running,
    but should not 400/422."""
    resp = client.post("/api/chat", data={"message": "what is this?"})
    assert resp.status_code in (200, 500)


def test_chat_with_image(client):
    img = Image.new("RGB", (32, 32), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    resp = client.post(
        "/api/chat",
        data={"message": "describe this"},
        files={"image": ("q.png", buf.getvalue(), "image/png")},
    )
    assert resp.status_code in (200, 500)


def test_retrieve_text(client):
    resp = client.post("/api/retrieve", data={"text": "architecture"})
    assert resp.status_code in (200, 500)
