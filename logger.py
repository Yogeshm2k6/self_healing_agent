"""
logger.py  (Bonus Feature)
---------------------------
Sets up a unified logging system using Python's built-in `logging` module
enriched with Rich's colourful console handler.

Every module in the project can do:

    from logger import get_logger
    log = get_logger(__name__)
    log.info("Agent started")
    log.error("Something broke")

Log output goes to:
  • Console  – colourised via Rich
  • File     – agent.log  (plain text, always appended)
"""

import logging
import sys
from pathlib import Path

from rich.logging import RichHandler

_LOG_FILE = Path(__file__).parent / "agent.log"
_INITIALIZED = False


def _setup_root_logger() -> None:
    """Configure the root logger once (idempotent)."""
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # ── Rich console handler ──────────────────────────────────────────────
    console_handler = RichHandler(
        level=logging.INFO,
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
        markup=True,
    )
    root.addHandler(console_handler)

    # ── File handler ─────────────────────────────────────────────────────
    file_handler = logging.FileHandler(str(_LOG_FILE), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger, initialising the root logger on first call.

    Parameters
    ----------
    name : typically __name__ of the calling module
    """
    _setup_root_logger()
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log = get_logger("test")
    log.debug("Debug message (file only)")
    log.info("Info message")
    log.warning("Warning message")
    log.error("Error message")
