"""Security helpers: filename sanitization, file validation, safe image serving."""

from __future__ import annotations

import hashlib
import mimetypes
import re
import uuid
from pathlib import Path

from app.config import settings

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

# Magic bytes for common image formats we accept as query images
_IMAGE_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",  # RIFF....WEBP
    b"BM": "image/bmp",
}

_PDF_MAGIC = b"%PDF-"


def sanitize_filename(name: str) -> str:
    """Return a filesystem-safe version of a filename, preserving the extension."""
    name = Path(name).name  # strip any path components
    name = _SAFE_NAME_RE.sub("_", name).strip("._")
    if not name:
        name = "file"
    return name[:120]


def new_doc_id() -> str:
    return uuid.uuid4().hex[:16]


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_valid_pdf(data: bytes) -> bool:
    return data[:5] == _PDF_MAGIC


def sniff_image_type(data: bytes) -> str | None:
    """Return a MIME type if data looks like a supported image, else None."""
    for magic, mime in _IMAGE_MAGIC.items():
        if data.startswith(magic):
            if magic == b"RIFF":
                if data[8:12] == b"WEBP":
                    return mime
                return None
            return mime
    return None


def is_allowed_image(data: bytes) -> bool:
    return sniff_image_type(data) is not None


def safe_image_path(document_id: str, image_id: str, ext: str) -> Path:
    """Build a safe path for an extracted image, confined to the images dir."""
    ext = ext.lstrip(".")
    if ext not in {"png", "jpg", "jpeg", "webp", "gif", "bmp"}:
        ext = "png"
    return settings.extracted_images_dir / document_id / f"{image_id}.{ext}"


def safe_upload_path(filename: str) -> Path:
    """Build a safe path for an uploaded file, confined to the uploads dir."""
    safe = sanitize_filename(filename)
    return settings.upload_dir / safe


def is_within_directory(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"
