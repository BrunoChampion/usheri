import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "agent.jsonl"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.getMessage()),
        }
        for key in (
            "session_id",
            "tool_name",
            "arguments",
            "result_summary",
            "content",
            "turn_number",
            "num_tool_calls",
            "duration_ms",
            "error_type",
            "traceback",
        ):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str | None = None) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger = logging.getLogger("usheri")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(console_handler)
    return logger


def log_event(
    event: str,
    session_id: str | None = None,
    **kwargs: object,
) -> None:
    logger = logging.getLogger("usheri")
    extra = {"event": event, "session_id": session_id, **kwargs}
    logger.info(event, extra=extra)
