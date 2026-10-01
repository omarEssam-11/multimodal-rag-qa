"""Document upload, listing, status, reindex, delete endpoints."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import DocumentResponse, StatusResponse, UploadResponse
from app.services.ingestion_service import ingestion_service
from app.services.pdf_processor import PDFProcessingError
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    data = await file.read()
    try:
        record = ingestion_service.ingest(data, file.filename)
        return UploadResponse(
            document_id=record.document_id,
            document_name=record.document_name,
            status=record.status,
            message=f"Document '{record.document_name}' indexed successfully",
        )
    except PDFProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@router.get("", response_model=list[DocumentResponse])
async def list_documents():
    from app.services.ingestion_service import document_store

    return [
        DocumentResponse(
            document_id=d.document_id,
            document_name=d.document_name,
            status=d.status,
            num_pages=d.num_pages,
            num_images=d.num_images,
            num_chunks=d.num_chunks,
            file_size=d.file_size,
            created_at=d.created_at,
            updated_at=d.updated_at,
            error=d.error,
        )
        for d in document_store.get_all()
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    from app.services.ingestion_service import document_store

    d = document_store.get(document_id)
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        document_id=d.document_id,
        document_name=d.document_name,
        status=d.status,
        num_pages=d.num_pages,
        num_images=d.num_images,
        num_chunks=d.num_chunks,
        file_size=d.file_size,
        created_at=d.created_at,
        updated_at=d.updated_at,
        error=d.error,
    )


@router.get("/{document_id}/status", response_model=StatusResponse)
async def document_status(document_id: str):
    from app.services.ingestion_service import document_store

    d = document_store.get(document_id)
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    return StatusResponse(
        document_id=d.document_id,
        status=d.status,
        num_pages=d.num_pages,
        num_images=d.num_images,
        num_chunks=d.num_chunks,
        error=d.error,
    )


@router.post("/{document_id}/index", response_model=DocumentResponse)
async def reindex_document(document_id: str):
    try:
        record = ingestion_service.reindex(document_id)
        return DocumentResponse(
            document_id=record.document_id,
            document_name=record.document_name,
            status=record.status,
            num_pages=record.num_pages,
            num_images=record.num_images,
            num_chunks=record.num_chunks,
            file_size=record.file_size,
            created_at=record.created_at,
            updated_at=record.updated_at,
            error=record.error,
        )
    except PDFProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Reindex failed")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    try:
        ingestion_service.delete_document(document_id)
        return {"message": "Document deleted", "document_id": document_id}
    except PDFProcessingError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Delete failed")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
