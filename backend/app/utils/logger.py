"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from app.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handler.addFilter(RequestIdFilter())
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.propagate = False
    return logger


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def set_request_id(rid: str | None = None) -> str:
    rid = rid or new_request_id()
    request_id_var.set(rid)
    return rid


def log_query_event(
    logger: logging.Logger,
    *,
    request_id: str,
    query_type: str,
    retrieval_ms: float,
    n_text: int,
    n_images: int,
    generation_ms: float,
    model: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """Log a structured query event for observability."""
    logger.info(
        "query_event | id=%s | type=%s | retrieval_ms=%.1f | text_hits=%d | image_hits=%d | "
        "generation_ms=%.1f | model=%s | %s",
        request_id,
        query_type,
        retrieval_ms,
        n_text,
        n_images,
        generation_ms,
        model,
        " ".join(f"{k}={v}" for k, v in (extra or {}).items()),
    )
