"""Logging configuration."""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler

from config.settings import get_settings


def setup_logging() -> None:
    """Configure structured logging."""
    settings = get_settings()

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # JSON formatter for structured logging
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }

            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)

            # Handle extra context fields
            for key, value in record.__dict__.items():
                if key not in ('name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process', 'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info', 'asctime'):
                    log_data[key] = value

            return json.dumps(log_data)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        "logs/loanapproval.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(getattr(logging, settings.log_level))
    json_formatter = JsonFormatter()
    file_handler.setFormatter(json_formatter)

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a logger with structured context support."""
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, {})
