"""
Generic RAG-grounded agent. All 5 domains (FAQ, Billing, Technical, Product,
Complaint) currently share the same knowledge base and retrieval logic —
only the name (for aggregator labeling) and system prompt persona differ.
Avoids 5 near-duplicate agent classes (Instruction 6).

KNOWN LIMITATION: retrieval is not yet domain-filtered — every agent draws
from the same shared FAISS index. Domain-specific document partitioning
can be added later if the knowledge base grows large enough to need it.
"""
from agents.base_agent import BaseAgent, AgentResponse
from llm.provider import LLMProvider
from rag.embeddings import EmbeddingProvider
from rag.vector_store import VectorStore
from rag.retrieval import retrieve, CONFIDENCE_THRESHOLD
from rag.domain_sources import get_allowed_sources
from prompts.support_prompts import INSUFFICIENT_CONTEXT_FALLBACK, build_rag_prompt


class RAGAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: LLMProvider,
        embedding_provider: EmbeddingProvider,
        store: VectorStore,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ):
        self.name = name
        self._system_prompt = system_prompt
        self._llm = llm
        self._embedding_provider = embedding_provider
        self._store = store
        self._confidence_threshold = confidence_threshold
        # None means "no domain mapping, search everything" — a graceful
        # fallback, not a silent failure, if a new domain is ever added
        # without updating rag/domain_sources.py.
        self._allowed_sources = get_allowed_sources(name)

    def respond(self, query: str) -> AgentResponse:
        result = retrieve(
            query, self._embedding_provider, self._store,
            confidence_threshold=self._confidence_threshold,
            allowed_sources=self._allowed_sources,
        )

        if result.insufficient_context:
            return AgentResponse(agent_name=self.name, text=INSUFFICIENT_CONTEXT_FALLBACK, grounded=False)

        prompt = build_rag_prompt(query, result.chunks)
        answer = self._llm.generate(prompt, system_prompt=self._system_prompt)
        return AgentResponse(agent_name=self.name, text=answer, grounded=True)
