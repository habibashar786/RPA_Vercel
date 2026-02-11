"""Lightweight logging wrapper compatible with the small `loguru` API

This module provides a safe, dependency-free logger object that exposes
the subset of `loguru` functionality used in the project:

- `logger.info/debug/warning/error/exception(...)`
- `logger.add(sink, level=...)` - returns handler id
- `logger.remove(handler_id)` - removes handler previously added

Design goals:
- Use the stdlib `logging` (no external dependency required)
- Thread-safe handler management
- Provide rotating file support when a file sink is added
- Minimal surface compatible with tests and local development

Note: This wrapper is intended for development environments where
`loguru` may not be installed. In production prefer installing and
using the real `loguru` package and remove this shim.
"""
from __future__ import annotations

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class LoggerShim:
    """A small logging shim exposing a loguru-like API.

    This intentionally exposes only the minimal API needed by the test
    suite and application code. It is thread-safe and keeps a registry
    of handlers so callers can add/remove them by id.
    """

    def __init__(self, name: str = "rpa_project") -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        self._lock = threading.RLock()
        self._handlers: Dict[int, logging.Handler] = {}
        # default stderr handler
        self.add(sys.stderr, level="INFO")

    def _format(self, handler: logging.Handler) -> None:
        if not handler.formatter:
            handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))

    def add(self, sink: Any, level: str = "INFO", *, rotation: Optional[int] = None, backup: int = 3) -> int:
        """Add a handler.

        Args:
            sink: A file path (str) or stream-like object (e.g., sys.stderr).
            level: Logging level name or number.
            rotation: If an integer is provided and sink is a path, use a
                RotatingFileHandler with this maxBytes value.
            backup: Number of backup files to keep for rotating handler.

        Returns:
            An integer handler id which can be passed to `remove`.
        """
        with self._lock:
            if isinstance(sink, str):
                # treat sink as file path
                if rotation:
                    handler: logging.Handler = RotatingFileHandler(sink, maxBytes=rotation, backupCount=backup)
                else:
                    handler = logging.FileHandler(sink)
            else:
                # assume stream-like
                handler = logging.StreamHandler(sink)

            # set level and formatter
            handler.setLevel(getattr(logging, str(level).upper(), logging.INFO))
            self._format(handler)
            self._logger.addHandler(handler)
            hid = id(handler)
            self._handlers[hid] = handler
            return hid

    def remove(self, handler_id: Optional[int] = None) -> None:
        """Remove a handler by id. If handler_id is None, remove all added handlers.
        """
        with self._lock:
            if handler_id is None:
                for hid, h in list(self._handlers.items()):
                    try:
                        self._logger.removeHandler(h)
                    except Exception:
                        pass
                    self._handlers.pop(hid, None)
                return

            h = self._handlers.pop(handler_id, None)
            if h is not None:
                try:
                    self._logger.removeHandler(h)
                except Exception:
                    pass

    # Basic logging API expected by the codebase
    def debug(self, *args: Any, **kwargs: Any) -> None:
        self._logger.debug("".join(map(str, args)), **kwargs)

    def info(self, *args: Any, **kwargs: Any) -> None:
        self._logger.info("".join(map(str, args)), **kwargs)

    def warning(self, *args: Any, **kwargs: Any) -> None:
        self._logger.warning("".join(map(str, args)), **kwargs)

    def error(self, *args: Any, **kwargs: Any) -> None:
        self._logger.error("".join(map(str, args)), **kwargs)

    def exception(self, *args: Any, **kwargs: Any) -> None:
        # exception should include stack info
        self._logger.exception("".join(map(str, args)), **kwargs)


# Module-level logger instance used across the project when `loguru` is not available
logger = LoggerShim()

__all__ = ["logger"]
