"""Standalone retrieval endpoint (no generation) for transparency/debugging."""

from __future__ import annotations

import base64

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import RetrieveResponse, SourceRef
from app.services.retriever import retriever
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/retrieve", tags=["retrieve"])


@router.post("", response_model=RetrieveResponse)
async def retrieve(
    text: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
):
    image_bytes = None
    if image is not None:
        image_bytes = await image.read()

    if not text and image_bytes is None:
        raise HTTPException(status_code=400, detail="Provide text and/or an image")

    try:
        output = retriever.retrieve(text=text, image=image_bytes)
        results = [
            SourceRef(
                document=r.document_name,
                page=r.page_number,
                type=r.content_type,
                score=round(r.score, 4),
                content=r.content[:500] if r.content else "",
                image_url=r.image_url,
                caption=r.caption,
            )
            for r in output.results
        ]
        return RetrieveResponse(
            query_type=output.query_type,
            results=results,
            text_hits=output.text_hits,
            image_hits=output.image_hits,
            retrieval_ms=output.retrieval_ms,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Retrieval failed")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
