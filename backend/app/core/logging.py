import logging
import re
import sys
from typing import Any

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "access_token",
    "hashed_password",
    "key",
    "authorization",
}


class SensitiveDataFilter(logging.Filter):
    """Redacts sensitive values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # Redact Authorization Bearer tokens
            record.msg = re.sub(
                r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*",
                r"\1[REDACTED_TOKEN]",
                record.msg,
                flags=re.IGNORECASE,
            )
            # Redact password patterns
            record.msg = re.sub(
                r"('?password'?\s*[:=]\s*)'?[^',}\s]+'?",
                r"\1'[REDACTED]'",
                record.msg,
                flags=re.IGNORECASE,
            )
        return True


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively redacts sensitive keys in dictionaries before logging or audit."""
    clean = {}
    for k, v in data.items():
        if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
            clean[k] = "[REDACTED]"
        elif isinstance(v, dict):
            clean[k] = redact_dict(v)
        elif isinstance(v, list):
            clean[k] = [redact_dict(i) if isinstance(i, dict) else i for i in v]
        else:
            clean[k] = v
    return clean


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("labstock")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
