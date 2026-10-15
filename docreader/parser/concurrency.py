import logging
import threading
from contextlib import contextmanager
from typing import Dict, Iterator

logger = logging.getLogger(__name__)

_LIMITERS: Dict[str, threading.BoundedSemaphore] = {}
_LIMITERS_LOCK = threading.Lock()


def _get_limiter(name: str, max_workers: int) -> threading.BoundedSemaphore:
    with _LIMITERS_LOCK:
        limiter = _LIMITERS.get(name)
        if limiter is None:
            limiter = threading.BoundedSemaphore(max_workers)
            _LIMITERS[name] = limiter
        return limiter


@contextmanager
def parser_worker_limit(name: str, max_workers: int) -> Iterator[None]:
    """限制进程内高开销解析操作的并发数量。

    CPU/GPU 资源充足且确认后端支持安全并发时，可设置 max_workers <= 0 禁用限流。
    """

    if max_workers <= 0:
        yield
        return

    limiter = _get_limiter(name, max_workers)
    logger.debug("Waiting for %s parser slot (max_workers=%d)", name, max_workers)
    limiter.acquire()
    try:
        yield
    finally:
        limiter.release()
