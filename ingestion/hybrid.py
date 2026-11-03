"""Deterministic reciprocal-rank fusion over interchangeable retrieval channels."""

from typing import Protocol
from ingestion.retrieval import RetrievedChunk


class RetrievalChannel(Protocol):
    def retrieve(self, query, *, top_k=5, asset_context=None) -> list[RetrievedChunk]: ...


class EmbeddingProvider(Protocol):
    model: str
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HybridIndex:
    strategy = "hybrid_rrf"

    def __init__(self, lexical, semantic=None, *, min_lexical_score=0.1):
        if not 0 <= min_lexical_score <= 1:
            raise ValueError("invalid lexical threshold")
        self.lexical, self.semantic = lexical, semantic
        self.threshold = min_lexical_score

    def retrieve(self, query, *, top_k=5, asset_context=None):
        if not query.strip() or top_k <= 0:
            raise ValueError("nonempty query and positive top_k required")
        lexical = self.lexical.retrieve(query, top_k=top_k * 4, asset_context=asset_context)
        lexical = [item for item in lexical if item.score >= self.threshold]
        # A semantic match alone does not establish applicability or sufficient evidence.
        if not lexical:
            return []
        channels = [lexical]
        if self.semantic:
            allowed = {item.chunk_id for item in lexical}
            channels.append([item for item in self.semantic.retrieve(
                query, top_k=top_k * 4, asset_context=asset_context,
            ) if item.chunk_id in allowed])
        scores, results = {}, {}
        for channel in channels:
            for rank, item in enumerate(channel, 1):
                results[item.chunk_id] = item
                scores[item.chunk_id] = scores.get(item.chunk_id, 0) + 1 / (60 + rank)
        ordered = sorted(scores, key=lambda key: (-scores[key], key))[:top_k]
        return [results[key].model_copy(update={"score": scores[key]}) for key in ordered]
