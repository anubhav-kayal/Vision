"""Conservative structured answer generation over retrieved evidence."""

from __future__ import annotations

from typing import Protocol

from pydantic import ValidationError

from backend.app.models import AnswerStatus, GroundedAnswer, GroundedSource
from ingestion.retrieval import RetrievedChunk


class ModelProvider(Protocol):
    """Minimal provider boundary for an LLM that returns JSON text."""

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return a JSON-encoded grounded answer."""


SYSTEM_PROMPT = """You are a conservative industrial maintenance knowledge assistant.
Use only the supplied evidence. Do not invent machine facts, specifications, procedures,
safety instructions, or fault codes. If the evidence does not support the requested answer,
return INSUFFICIENT_KNOWLEDGE. Every factual claim must be supported by one or more supplied
sources. Return only a JSON object matching the requested schema. Do not reveal hidden
chain-of-thought; provide only a concise evidence summary.

Allowed statuses: SUPPORTED, PARTIALLY_SUPPORTED, INSUFFICIENT_KNOWLEDGE.
"""


def build_grounded_prompt(query: str, retrieved: list[RetrievedChunk]) -> str:
    """Build a bounded prompt containing only the retrieved evidence."""

    evidence = []
    for result in retrieved:
        evidence.append(
            "\n".join(
                [
                    f"SOURCE_ID: {result.chunk_id}",
                    f"DOCUMENT_ID: {result.document_id}",
                    f"PDF_PAGE: {result.page}",
                    f"PRINTED_PAGE: {result.printed_page}",
                    f"SECTION: {result.section}",
                    f"TEXT: {result.text}",
                ]
            )
        )
    context = "\n\n---\n\n".join(evidence)
    return f"""Question:
{query}

Retrieved evidence:
{context}

Return JSON with this shape:
{{
  "status": "SUPPORTED | PARTIALLY_SUPPORTED | INSUFFICIENT_KNOWLEDGE",
  "answer": "concise answer or conservative refusal",
  "sources": [
    {{
      "chunk_id": "SOURCE_ID from supplied evidence",
      "document_id": "DOCUMENT_ID from supplied evidence",
      "page": "PRINTED_PAGE or PDF_PAGE",
      "section": "SECTION",
      "supporting_text": "exact excerpt from supplied evidence"
    }}
  ],
  "evidence_summary": "brief explanation of what the evidence supports"
}}
"""


class GroundedAnswerGenerator:
    """Generate and validate an answer against the exact retrieved context."""

    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def answer(self, query: str, retrieved: list[RetrievedChunk]) -> GroundedAnswer:
        if not query.strip():
            raise ValueError("query must not be empty")
        if not retrieved:
            return self._insufficient("No supporting evidence was retrieved.")

        raw = self.provider.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_grounded_prompt(query, retrieved),
        )
        try:
            candidate = GroundedAnswer.model_validate_json(raw)
        except (ValidationError, ValueError):
            return self._insufficient("The model response did not match the grounded schema.")

        if not self._sources_are_grounded(candidate.sources, retrieved):
            return self._insufficient("The model cited evidence outside the retrieved context.")
        if candidate.status is AnswerStatus.INSUFFICIENT_KNOWLEDGE and candidate.sources:
            return self._insufficient("An insufficient-knowledge response must not cite unsupported sources.")
        return candidate

    @staticmethod
    def _sources_are_grounded(
        sources: list[GroundedSource], retrieved: list[RetrievedChunk]
    ) -> bool:
        by_chunk = {result.chunk_id: result for result in retrieved}
        for source in sources:
            result = by_chunk.get(source.chunk_id) if source.chunk_id else None
            if result is None:
                result = next(
                    (
                        candidate
                        for candidate in retrieved
                        if candidate.document_id == source.document_id
                        and str(candidate.printed_page or candidate.page) == str(source.page)
                    ),
                    None,
                )
            if result is None:
                return False
            if source.document_id != result.document_id:
                return False
            if str(source.page) not in {str(result.page), str(result.printed_page)}:
                return False
            if source.section and source.section != result.section:
                return False
            if source.supporting_text not in result.text:
                return False
        return True

    @staticmethod
    def _insufficient(reason: str) -> GroundedAnswer:
        return GroundedAnswer(
            status=AnswerStatus.INSUFFICIENT_KNOWLEDGE,
            answer="INSUFFICIENT_KNOWLEDGE: The supplied documentation does not support a reliable answer.",
            evidence_summary=reason,
        )
