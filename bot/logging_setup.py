"""Structured logging utilities."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import orjson


class OrjsonFormatter(logging.Formatter):
    """Formatter that outputs JSON using orjson."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        data = {
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return orjson.dumps(data).decode()


def setup_logging(log_dir: str = "logs") -> None:
    """Configure root logger with JSON formatter."""
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(path / "bot.log", maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(OrjsonFormatter())

    logging.basicConfig(level=logging.INFO, handlers=[handler])
