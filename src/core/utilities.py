"""Shared utility functions for the ClipCognition application."""

import functools
import logging
import time

logger = logging.getLogger(__name__)


def timer(func):
    """Print the run timespan of the decorated function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time
        logger.info("Finished %r in %.4f seconds", func.__name__, elapsed_time)
        return result

    return wrapper
