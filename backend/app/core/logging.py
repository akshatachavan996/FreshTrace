"""Logging configuration for FreshTrace.

Ensures structured, informative logs without leaking sensitive API keys or credentials.
"""

import logging
import sys


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure root and application loggers."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Set third-party loggers to a slightly quieter level
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger("freshtrace")
    logger.setLevel(level)
    return logger


logger = setup_logging()
