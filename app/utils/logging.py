from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: Path | None = None, level: str = "INFO") -> None:
    fmt = "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
    logger.remove()
    logger.add(sys.stderr, level=level, format=fmt)
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / "quark-{time:YYYYMMDD}.log",
            level="DEBUG",
            rotation="1 day",
            retention="14 days",
            format=fmt,
            encoding="utf-8",
        )