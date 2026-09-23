from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable

class ISRCache:
    _cache: dict[str, tuple[float, str]] = {}

    @classmethod
    def get(cls, key: str, revalidate_seconds: int) -> str | None:
        if key in cls._cache:
            timestamp, html = cls._cache[key]
            if time.time() - timestamp < revalidate_seconds:
                return html
            else:
                del cls._cache[key]
        return None

    @classmethod
    def set(cls, key: str, html: str) -> None:
        cls._cache[key] = (time.time(), html)
        
    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

def isr(revalidate: int = 60) -> Callable:
    """Decorator to mark a page component for Incremental Static Regeneration."""
    def decorator(cls: Any) -> Any:
        cls._isr_revalidate = revalidate
        return cls
    return decorator
