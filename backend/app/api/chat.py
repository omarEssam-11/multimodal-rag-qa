"""Chat endpoint: text-only, image-only, and text+image queries."""

from __future__ import annotations

import base64
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import ChatResponse
from app.services.rag_service import rag_service
from app.utils.logger import get_logger, set_request_id

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    message: str | None = Form(default=None),
    session_id: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
):
    rid = set_request_id()
    image_bytes = None
    if image is not None:
        image_bytes = await image.read()

    if not message and image_bytes is None:
        raise HTTPException(status_code=400, detail="Provide a message and/or an image")

    session_id = session_id or uuid.uuid4().hex[:12]

    try:
        response = rag_service.answer(
            text=message,
            image=image_bytes,
            session_id=session_id,
            request_id=rid,
        )
        return ChatResponse(
            answer=response.answer,
            sources=response.sources,
            query_type=response.query_type,
            retrieval_ms=response.retrieval_ms,
            generation_ms=response.generation_ms,
            model=response.model,
            text_hits=response.text_hits,
            image_hits=response.image_hits,
            pipeline=response.pipeline,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
