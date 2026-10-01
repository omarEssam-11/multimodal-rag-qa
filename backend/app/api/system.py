"""System endpoints: health, config, and safe image serving."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import ConfigResponse, HealthResponse
from app.services.vector_store import vector_store
from app.utils.logger import get_logger
from app.utils.security import guess_mime, is_within_directory

logger = get_logger(__name__)
router = APIRouter(tags=["system"])


@router.get("/api/health", response_model=HealthResponse)
async def health():
    qdrant_ok = vector_store.health_check()
    return HealthResponse(
        status="ok",
        qdrant=qdrant_ok,
        embedding_models=True,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )


@router.get("/api/config", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model if settings.llm_provider == "ollama" else settings.openai_model,
        temperature=settings.llm_temperature,
        top_k_text=settings.top_k_text,
        top_k_images=settings.top_k_images,
        text_weight=settings.text_retrieval_weight,
        image_weight=settings.image_retrieval_weight,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        clip_model=settings.clip_model,
        text_embedding_model=settings.text_embedding_model,
        max_history_messages=settings.max_history_messages,
    )


@router.get("/api/images/{image_id}")
async def serve_image(image_id: str):
    """Safely serve an extracted image by its image_id (no directory traversal)."""
    # image_id format: {document_id}_p{page}_i{idx}
    parts = image_id.split("_p")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid image id")
    document_id = parts[0]
    img_dir = settings.extracted_images_dir / document_id
    if not img_dir.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    # find the file with matching prefix
    matches = list(img_dir.glob(f"{image_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Image not found")
    path = matches[0]
    if not is_within_directory(path, settings.extracted_images_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    return FileResponse(path, media_type=guess_mime(path))
