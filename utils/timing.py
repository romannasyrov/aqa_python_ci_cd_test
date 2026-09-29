import functools
import logging
import time

logger = logging.getLogger(__name__)

def timing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            logger.info(f"[TIMING] {func.__name__} - {elapsed:.3f}s")
    return wrapper