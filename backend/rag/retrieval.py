"""
Retrieval with a confidence-threshold fallback.

Enforces the M0 decision (Instruction 17 — no ungrounded answers): if the
best retrieved chunk's similarity score is below CONFIDENCE_THRESHOLD, we
signal insufficient_context=True so the calling agent can respond honestly
rather than letting the LLM improvise from weak or irrelevant context.

Every retrieval logs which chunks were returned and their scores, so
Milestone 10 (evaluation) has real data instead of having to guess.
"""
from dataclasses import dataclass, field

from rag.embeddings import EmbeddingProvider
from rag.vector_store import VectorStore
from core.logging import get_logger

logger = get_logger(__name__)

CONFIDENCE_THRESHOLD = 0.55  # cosine similarity; revisit once real TechMart docs give us calibration data


@dataclass
class RetrievalResult:
    query: str
    chunks: list[dict]
    insufficient_context: bool
    top_score: float = field(default=0.0)


def retrieve(
    query: str,
    embedding_provider: EmbeddingProvider,
    store: VectorStore,
    top_k: int = 4,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
) -> RetrievalResult:
    query_vector = embedding_provider.embed([query])[0]
    chunks = store.search(query_vector, top_k=top_k)

    top_score = chunks[0]["score"] if chunks else 0.0
    insufficient = top_score < confidence_threshold

    logger.info(
        "retrieval_logged",
        extra={
            "query": query,
            "top_score": top_score,
            "insufficient_context": insufficient,
            "chunk_sources": [c["source"] for c in chunks],
        },
    )

    return RetrievalResult(query=query, chunks=chunks, insufficient_context=insufficient, top_score=top_score)
