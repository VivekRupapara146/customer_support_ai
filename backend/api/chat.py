"""
Chat endpoint — Milestone 3 proof of concept.

Only the FAQ agent is implemented so far. If the router selects an agent
that isn't in the registry yet, we degrade gracefully (skip it, note it)
rather than crashing — the remaining milestones fill in the registry.
"""
import uuid

from fastapi import APIRouter, Depends, Request, HTTPException, status, Path
from pydantic import BaseModel, Field

from auth.jwt_handler import get_current_subject
from core.rate_limit import limiter
from core.config import settings
from core.logging import get_logger
from database.mongo import get_db
from database.conversations import append_message, get_history
from models.response import APIResponse
from models.conversation import Message, ConversationHistoryData
from router.rule_based import route as route_rule_based, AGENT_KEYWORDS
from router.llm_based import route as route_llm_based
from router.trained_classifier import route as route_trained_classifier
from router.types import RouteDecision
from agents.base_agent import BaseAgent, AgentResponse
from agents.rag_agent import RAGAgent
from prompts.support_prompts import AGENT_SYSTEM_PROMPTS
from aggregator import aggregate
from llm.provider import GeminiLLMProvider
from rag.embeddings import GeminiEmbeddingProvider
from rag.vector_store import VectorStore
from rag.ingestion import ingest_directory

logger = get_logger(__name__)
router_ = APIRouter(prefix="/chat", tags=["chat"])

SESSION_ID_PATTERN = r"^[a-zA-Z0-9\-]{1,64}$"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, pattern=SESSION_ID_PATTERN)


class ChatResponseData(BaseModel):
    reply: str
    routed_agents: list[str]
    session_id: str


# --- Agent registry -------------------------------------------------------
# Lazily built on first request so a missing GEMINI_API_KEY doesn't crash
# app startup — it only matters once /chat is actually called.
_registry: dict[str, BaseAgent] | None = None
_llm_provider = None


def get_llm_provider():
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = GeminiLLMProvider()
    return _llm_provider


def get_agent_registry() -> dict[str, BaseAgent]:
    global _registry
    if _registry is None:
        llm = get_llm_provider()
        embedding_provider = GeminiEmbeddingProvider()
        store = ingest_directory("knowledge_base", embedding_provider, embedding_dim=3072)
        _registry = {
            name: RAGAgent(
                name=name,
                system_prompt=AGENT_SYSTEM_PROMPTS[name],
                llm=llm,
                embedding_provider=embedding_provider,
                store=store,
            )
            for name in AGENT_KEYWORDS.keys()
        }
    return _registry


def _get_route_decision(message: str) -> RouteDecision:
    if settings.active_router == "llm_based":
        return route_llm_based(message, get_llm_provider())
    if settings.active_router == "trained_classifier":
        return route_trained_classifier(message)
    return route_rule_based(message)


@router_.post("", response_model=APIResponse[ChatResponseData])
@limiter.limit(settings.rate_limit_default)
async def chat(request: Request, payload: ChatRequest, subject: str = Depends(get_current_subject)):
    session_id = payload.session_id or str(uuid.uuid4())
    db = get_db()

    decision = _get_route_decision(payload.message)
    registry = get_agent_registry()

    responses: list[AgentResponse] = []
    unhandled: list[str] = []

    for agent_name in decision.agents:
        agent = registry.get(agent_name)
        if agent is None:
            unhandled.append(agent_name)
            continue
        responses.append(agent.respond(payload.message))

    if unhandled:
        logger.info(f"Query routed to not-yet-implemented agents: {unhandled}")

    reply = aggregate(responses) if responses else (
        "That request needs a specialist we haven't wired up yet in this milestone — "
        "coming in a later build."
    )

    await append_message(db, session_id, subject, Message(role="user", content=payload.message))
    await append_message(
        db, session_id, subject, Message(role="assistant", content=reply, routed_agents=decision.agents)
    )

    return APIResponse(
        success=True,
        data=ChatResponseData(reply=reply, routed_agents=decision.agents, session_id=session_id),
    )


@router_.get("/history/{session_id}", response_model=APIResponse[ConversationHistoryData])
async def chat_history(
    session_id: str = Path(pattern=SESSION_ID_PATTERN),
    subject: str = Depends(get_current_subject),
):
    db = get_db()
    messages = await get_history(db, session_id, subject)
    if messages is None:
        # Same response whether the session doesn't exist or belongs to someone
        # else — never reveals which, to avoid leaking session existence (Instruction 7).
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return APIResponse(success=True, data=ConversationHistoryData(session_id=session_id, messages=messages))
