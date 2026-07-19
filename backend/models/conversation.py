"""
Conversation/session schemas.
"""
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    routed_agents: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionSummary(BaseModel):
    session_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    preview: str = ""


class SessionListData(BaseModel):
    sessions: list[SessionSummary]


class ConversationHistoryData(BaseModel):
    session_id: str
    messages: list[Message]
