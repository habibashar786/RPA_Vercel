"""Minimal shim for `loguru.logger` used in tests when `loguru` isn't installed.

This provides the small subset of API the project expects: `info`, `warning`, `error`, `debug`.
"""
import logging

_logging = logging.getLogger("project")
_logging.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logging.addHandler(_handler)

class _ShimLogger:
    def info(self, *args, **kwargs):
        _logging.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        _logging.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        _logging.error(*args, **kwargs)

    def debug(self, *args, **kwargs):
        _logging.debug(*args, **kwargs)
    
    # Minimal compatibility with loguru API used in tests
    def remove(self, *args, **kwargs):
        # no-op: tests typically call logger.remove() to reset handlers
        return None

    def add(self, *args, **kwargs):
        # no-op: accept sink/level etc. and return a dummy handler id
        return 0

logger = _ShimLogger()
__all__ = ["logger"]
