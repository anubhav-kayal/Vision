"""Deterministic local TF-IDF retrieval over document chunks."""

from __future__ import annotations

import math
import re
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from ingestion.models import DocumentChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "with",
}


class RetrievedChunk(BaseModel):
    """A ranked result with enough provenance for inspection and later answering."""

    model_config = ConfigDict(extra="forbid")

    score: float
    chunk_id: str
    document_id: str
    page: int
    printed_page: str | None = None
    section: str | None = None
    text: str = Field(min_length=1)
    metadata: dict[str, str | None]


def tokenize(text: str) -> list[str]:
    """Normalize text into simple content tokens for the baseline index."""

    return [token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOPWORDS]


class TfidfIndex:
    """Small in-memory sparse TF-IDF index.

    This is intentionally a baseline, not a semantic embedding model. It provides
    deterministic vector retrieval that can be compared before adding embeddings.
    """

    strategy = "tfidf_vector"

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            raise ValueError("cannot index an empty chunk collection")
        self.chunks = chunks
        self._idf = self._build_idf(chunks)
        self._vectors = [self._vectorize(chunk.text) for chunk in chunks]
        self._norms = [self._norm(vector) for vector in self._vectors]

    @staticmethod
    def _build_idf(chunks: list[DocumentChunk]) -> dict[str, float]:
        document_frequency: Counter[str] = Counter()
        for chunk in chunks:
            document_frequency.update(set(tokenize(chunk.text)))
        count = len(chunks)
        return {
            token: math.log((1 + count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }

    def _vectorize(self, text: str) -> dict[str, float]:
        counts = Counter(tokenize(text))
        total = sum(counts.values()) or 1
        return {
            token: (frequency / total) * self._idf[token]
            for token, frequency in counts.items()
            if token in self._idf
        }

    @staticmethod
    def _norm(vector: dict[str, float]) -> float:
        return math.sqrt(sum(value * value for value in vector.values()))

    @staticmethod
    def _dot(left: dict[str, float], right: dict[str, float]) -> float:
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(token, 0.0) for token, value in left.items())

    def retrieve(self, query: str, *, top_k: int = 5) -> list[RetrievedChunk]:
        """Return top-k cosine-ranked chunks, excluding zero-overlap results."""

        if not query.strip():
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        query_vector = self._vectorize(query)
        query_norm = self._norm(query_vector)
        if query_norm == 0:
            return []

        scored: list[tuple[float, int]] = []
        for index, vector in enumerate(self._vectors):
            denominator = query_norm * self._norms[index]
            if denominator == 0:
                continue
            score = self._dot(query_vector, vector) / denominator
            if score > 0:
                scored.append((score, index))
        scored.sort(key=lambda pair: (-pair[0], self.chunks[pair[1]].chunk_id))
        return [self._result(score, self.chunks[index]) for score, index in scored[:top_k]]

    @staticmethod
    def _result(score: float, chunk: DocumentChunk) -> RetrievedChunk:
        return RetrievedChunk(
            score=round(score, 6),
            chunk_id=chunk.chunk_id,
            document_id=chunk.document.document_id,
            page=chunk.pdf_page_number,
            printed_page=chunk.printed_page_label,
            section=chunk.section,
            text=chunk.text,
            metadata={
                "manufacturer": chunk.document.manufacturer,
                "equipment_family": chunk.document.equipment_family,
                "model": chunk.document.model,
                "document_type": chunk.document.document_type,
                "revision": chunk.document.revision,
                "authority_level": chunk.document.authority_level.value,
            },
        )
