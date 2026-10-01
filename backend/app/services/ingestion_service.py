"""Document ingestion pipeline: PDF -> text+images -> embeddings -> Qdrant."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from app.config import settings
from app.services.bm25_service import bm25_service
from app.services.embedding_service import embedding_service
from app.services.pdf_processor import PDFProcessor, PDFProcessingError
from app.services.text_chunker import TextChunker
from app.services.vector_store import vector_store
from app.utils.logger import get_logger
from app.utils.security import content_hash, is_valid_pdf, new_doc_id, safe_upload_path

logger = get_logger(__name__)

IndexingStatus = Literal["pending", "processing", "indexed", "failed"]


@dataclass
class DocumentRecord:
    document_id: str
    document_name: str
    status: IndexingStatus
    num_pages: int = 0
    num_images: int = 0
    num_chunks: int = 0
    file_size: int = 0
    content_hash: str = ""
    created_at: str = ""
    updated_at: str = ""
    error: str | None = None
    metadata: dict = field(default_factory=dict)


class DocumentStore:
    """Simple JSON-file backed document metadata store."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (settings.upload_dir / "documents.json")
        self._docs: dict[str, DocumentRecord] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                for d in data:
                    self._docs[d["document_id"]] = DocumentRecord(**d)
            except Exception as e:
                logger.warning("Failed to load document store: %s", e)

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(
                    [self._to_dict(d) for d in self._docs.values()],
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to save document store: %s", e)

    @staticmethod
    def _to_dict(d: DocumentRecord) -> dict:
        return {
            "document_id": d.document_id,
            "document_name": d.document_name,
            "status": d.status,
            "num_pages": d.num_pages,
            "num_images": d.num_images,
            "num_chunks": d.num_chunks,
            "file_size": d.file_size,
            "content_hash": d.content_hash,
            "created_at": d.created_at,
            "updated_at": d.updated_at,
            "error": d.error,
            "metadata": d.metadata,
        }

    def get(self, document_id: str) -> DocumentRecord | None:
        return self._docs.get(document_id)

    def get_all(self) -> list[DocumentRecord]:
        return list(self._docs.values())

    def upsert(self, record: DocumentRecord) -> None:
        self._docs[record.document_id] = record
        self._save()

    def delete(self, document_id: str) -> bool:
        if document_id in self._docs:
            del self._docs[document_id]
            self._save()
            return True
        return False


document_store = DocumentStore()


class IngestionService:
    def __init__(self) -> None:
        self.pdf_processor = PDFProcessor()
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size, overlap=settings.chunk_overlap
        )

    def validate_upload(self, data: bytes, filename: str) -> None:
        if not filename.lower().endswith(".pdf"):
            raise PDFProcessingError("Only PDF files are allowed")
        if len(data) > settings.max_upload_bytes:
            raise PDFProcessingError(
                f"File exceeds maximum size of {settings.max_upload_mb} MB"
            )
        if len(data) < 100:
            raise PDFProcessingError("File is too small to be a valid PDF")
        if not is_valid_pdf(data):
            raise PDFProcessingError("File does not look like a valid PDF")

    def ingest(self, data: bytes, filename: str) -> DocumentRecord:
        """Full ingestion pipeline. Returns the document record."""
        self.validate_upload(data, filename)

        # duplicate detection by content hash
        chash = content_hash(data)
        for existing in document_store.get_all():
            if existing.content_hash == chash and existing.status == "indexed":
                raise PDFProcessingError(
                    f"Duplicate document: already indexed as '{existing.document_name}'"
                )
        return self._ingest_internal(data, filename, content_hash=chash)

    def _ingest_internal(
        self, data: bytes, filename: str, content_hash: str | None = None
    ) -> DocumentRecord:
        chash = content_hash or content_hash(data)
        document_id = new_doc_id()
        safe_name = filename
        upload_path = safe_upload_path(f"{document_id}_{safe_name}")

        record = DocumentRecord(
            document_id=document_id,
            document_name=safe_name,
            status="processing",
            file_size=len(data),
            content_hash=chash,
            created_at=self._now(),
            updated_at=self._now(),
        )
        document_store.upsert(record)

        try:
            # 1. Save original
            upload_path.parent.mkdir(parents=True, exist_ok=True)
            upload_path.write_bytes(data)

            # 2. Process PDF
            processed = self.pdf_processor.process(
                upload_path, document_id, safe_name
            )

            # 3. Chunk text
            all_chunks = []
            for page in processed.pages:
                chunks = self.chunker.chunk_page(
                    page.text, page.page_number, document_id, safe_name
                )
                all_chunks.extend(chunks)

            # 4. Build BM25 index (for hybrid search)
            if all_chunks:
                bm25_service.build(
                    ids=[c.chunk_id for c in all_chunks],
                    texts=[c.content for c in all_chunks],
                )

            # 5. Embed text chunks
            text_vectors = None
            if all_chunks:
                texts = [c.content for c in all_chunks]
                text_vectors = embedding_service.embed_chunks(texts)

            # 5. Embed images with CLIP
            image_vectors = None
            if processed.images:
                image_paths = [img.image_path for img in processed.images]
                image_vectors = embedding_service.embed_document_images(image_paths)

            # 6. Ensure collections exist
            text_dim = int(text_vectors.shape[1]) if text_vectors is not None else 384
            image_dim = int(image_vectors.shape[1]) if image_vectors is not None else 512
            vector_store.initialize(text_dim=text_dim, image_dim=image_dim)

            # 7. Upsert text vectors
            if all_chunks and text_vectors is not None:
                vector_store.upsert_text(
                    ids=[c.chunk_id for c in all_chunks],
                    vectors=text_vectors,
                    payloads=[c.metadata for c in all_chunks],
                )

            # 8. Upsert image vectors
            if processed.images and image_vectors is not None:
                vector_store.upsert_images(
                    ids=[img.image_id for img in processed.images],
                    vectors=image_vectors,
                    payloads=[img.metadata for img in processed.images],
                )

            # 9. Update record
            record.status = "indexed"
            record.num_pages = processed.num_pages
            record.num_images = len(processed.images)
            record.num_chunks = len(all_chunks)
            record.updated_at = self._now()
            record.metadata = {
                "upload_path": str(upload_path),
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
            }
            document_store.upsert(record)

            logger.info(
                "Ingestion complete: %s | pages=%d | images=%d | chunks=%d",
                safe_name,
                record.num_pages,
                record.num_images,
                record.num_chunks,
            )
            return record

        except Exception as e:
            record.status = "failed"
            record.error = str(e)
            record.updated_at = self._now()
            document_store.upsert(record)
            logger.error("Ingestion failed for %s: %s", safe_name, e)
            raise

    def reindex(self, document_id: str) -> DocumentRecord:
        record = document_store.get(document_id)
        if not record:
            raise PDFProcessingError(f"Document not found: {document_id}")
        upload_path = Path(record.metadata.get("upload_path", ""))
        if not upload_path.exists():
            raise PDFProcessingError("Original file no longer exists")
        data = upload_path.read_bytes()
        # delete old vectors
        vector_store.delete_document(document_id)
        # bypass duplicate-content guard: ingest with a fresh document_id
        return self._ingest_internal(data, record.document_name, content_hash=record.content_hash)

    def delete_document(self, document_id: str) -> None:
        record = document_store.get(document_id)
        if not record:
            raise PDFProcessingError(f"Document not found: {document_id}")
        # delete vectors
        vector_store.delete_document(document_id)
        # delete extracted images
        img_dir = settings.extracted_images_dir / document_id
        if img_dir.exists():
            import shutil

            shutil.rmtree(img_dir, ignore_errors=True)
        # delete original
        upload_path = Path(record.metadata.get("upload_path", ""))
        if upload_path and str(upload_path) not in ("", ".") and upload_path.exists():
            try:
                upload_path.unlink()
            except OSError as e:
                logger.warning("Could not delete upload file %s: %s", upload_path, e)
        document_store.delete(document_id)

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()


ingestion_service = IngestionService()
