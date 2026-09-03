"""Structured logging configuration with automatic secret and credential sanitization."""
import logging
import re
import sys


class SensitiveDataFilter(logging.Filter):
    """
    Log filter that intercepts and scrubs sensitive patterns such as API keys,
    passwords, database URLs, and bearer tokens before log emission.
    """
    PATTERNS = [
        # OpenAI API keys (sk-...)
        (re.compile(r"sk-[a-zA-Z0-9_\-]{15,}", re.IGNORECASE), "sk-***REDACTED***"),
        # Database URLs with user:password@host
        (re.compile(r"(://[^:\s]+):([^@\s]+)@", re.IGNORECASE), r"\1:***REDACTED***@"),
        # Bearer / Token headers
        (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE), r"\1***REDACTED***"),
        # Password / secret keyword assignments in strings
        (re.compile(r"(password|secret|api_key|token)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE), r"\1='***REDACTED***'"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args:
            cleaned_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.PATTERNS:
                        arg = pattern.sub(replacement, arg)
                cleaned_args.append(arg)
            record.args = tuple(cleaned_args)
        return True


def setup_logger(name: str = "financial_analyst") -> logging.Logger:
    """Configures and returns a structured, sanitized logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
        logger.addFilter(SensitiveDataFilter())
    return logger


logger = setup_logger()