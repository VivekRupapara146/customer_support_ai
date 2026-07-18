"""
Structured logging setup.

Every module should call `get_logger(__name__)` rather than configuring
its own logger — keeps output consistent and machine-parseable.

IMPORTANT: never log secrets (API keys, JWTs, passwords, full request bodies
that may contain PII). Log identifiers/metadata, not payloads.
"""
import logging
import sys
import json
from datetime import datetime, timezone

from core.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
