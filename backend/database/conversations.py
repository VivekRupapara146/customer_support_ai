"""
Conversation storage: one document per session_id, embedded messages array.

Security: every read/write filters on {session_id, owner} together, so a
user can never read or append to a session_id that isn't theirs, even if
they guess a valid one (least privilege / Instruction 7).

Scalability: message array is capped at MAX_MESSAGES_PER_SESSION via
$slice, so a very long-running session can't grow the document unbounded
(Instruction 10).
"""
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from models.conversation import Message
from core.logging import get_logger

logger = get_logger(__name__)

COLLECTION = "conversations"
MAX_MESSAGES_PER_SESSION = 50


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db[COLLECTION].create_index([("session_id", 1), ("owner", 1)], unique=True)


async def append_message(db: AsyncIOMotorDatabase, session_id: str, owner: str, message: Message) -> None:
    await db[COLLECTION].update_one(
        {"session_id": session_id, "owner": owner},
        {
            "$push": {"messages": {"$each": [message.model_dump()], "$slice": -MAX_MESSAGES_PER_SESSION}},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )


async def get_history(db: AsyncIOMotorDatabase, session_id: str, owner: str) -> list[Message] | None:
    """Returns None if the session doesn't exist OR doesn't belong to this owner —
    callers should treat both cases identically (404), never revealing which."""
    doc = await db[COLLECTION].find_one({"session_id": session_id, "owner": owner})
    if doc is None:
        return None
    return [Message(**m) for m in doc.get("messages", [])]
