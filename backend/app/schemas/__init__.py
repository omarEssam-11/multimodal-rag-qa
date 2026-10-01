"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------- Documents ----------------

class DocumentResponse(BaseModel):
    document_id: str
    document_name: str
    status: str
    num_pages: int = 0
    num_images: int = 0
    num_chunks: int = 0
    file_size: int = 0
    created_at: str = ""
    updated_at: str = ""
    error: str | None = None


class UploadResponse(BaseModel):
    document_id: str
    document_name: str
    status: str
    message: str


class StatusResponse(BaseModel):
    document_id: str
    status: str
    num_pages: int = 0
    num_images: int = 0
    num_chunks: int = 0
    error: str | None = None


# ---------------- Chat ----------------

class ChatRequest(BaseModel):
    message: str | None = None
    session_id: str | None = None
    image_base64: str | None = None  # optional, for JSON clients


class SourceRef(BaseModel):
    document: str
    page: int
    type: str
    score: float
    content: str = ""
    image_url: str | None = None
    caption: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    query_type: str
    retrieval_ms: float
    generation_ms: float
    model: str
    text_hits: int
    image_hits: int
    pipeline: list[str] = Field(default_factory=list)
    session_id: str | None = None


# ---------------- Retrieve ----------------

class RetrieveRequest(BaseModel):
    text: str | None = None
    image_base64: str | None = None


class RetrieveResponse(BaseModel):
    query_type: str
    results: list[SourceRef]
    text_hits: int
    image_hits: int
    retrieval_ms: float


# ---------------- System ----------------

class HealthResponse(BaseModel):
    status: str
    qdrant: bool
    embedding_models: bool
    llm_provider: str
    llm_model: str


class ConfigResponse(BaseModel):
    llm_provider: str
    llm_model: str
    temperature: float
    top_k_text: int
    top_k_images: int
    text_weight: float
    image_weight: float
    chunk_size: int
    chunk_overlap: int
    clip_model: str
    text_embedding_model: str
    max_history_messages: int
