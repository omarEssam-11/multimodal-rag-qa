"""BM25 lexical index for hybrid search.

Maintains an in-memory BM25 index over text chunks, persisted to disk.
Combined with vector search via Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Sequence

from rank_bm25 import BM25Okapi

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"\w+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Service:
    """BM25 index over text chunks with disk persistence."""

    def __init__(self, index_path: Path | None = None) -> None:
        self.index_path = index_path or (settings.upload_dir / "bm25_index.json")
        self._bm25: BM25Okapi | None = None
        self._doc_ids: list[str] = []
        self._documents: list[list[str]] = []
        self._load()

    def build(self, doc_ids: Sequence[str], texts: Sequence[str]) -> None:
        """Build the BM25 index from chunk ids and their text content."""
        self._doc_ids = list(doc_ids)
        self._documents = [_tokenize(t) for t in texts]
        if not self._documents:
            self._bm25 = None
            return
        self._bm25 = BM25Okapi(self._documents)
        self._save()
        logger.info("BM25 index built: %d chunks", len(self._doc_ids))

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Return top matching doc ids with BM25 scores."""
        if self._bm25 is None or not self._doc_ids:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        # get_top_n returns indices sorted by score desc
        top_indices = self._bm25.get_top_n(_tokenize(query), self._doc_ids, n=limit)
        # Build result with scores
        results = []
        for idx, doc in enumerate(top_indices):
            # find the score for this doc
            doc_idx = self._doc_ids.index(doc) if doc in self._doc_ids else -1
            if doc_idx >= 0:
                results.append({
                    "id": doc,
                    "score": float(scores[doc_idx]),
                    "payload": {"chunk_id": doc},
                })
        return results

    def clear(self) -> None:
        self._bm25 = None
        self._doc_ids = []
        self._documents = []
        if self.index_path.exists():
            self.index_path.unlink()

    def _save(self) -> None:
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.index_path.write_text(
                json.dumps({"doc_ids": self._doc_ids}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Failed to save BM25 index: %s", e)

    def _load(self) -> None:
        # BM25 index is rebuilt on each ingestion; we only persist doc_ids
        # for reference. The actual index is rebuilt from Qdrant payloads.
        pass


bm25_service = BM25Service()
