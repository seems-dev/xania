from __future__ import annotations

import time
from typing import Any, Protocol

from xania.renderer.component import Component


class SessionStore(Protocol):
    def get(self, session_id: str, component_name: str) -> Component | None: ...
    def set(self, session_id: str, component_name: str, component: Component) -> None: ...
    def delete(self, session_id: str) -> None: ...


class InMemorySessionStore:
    """Dev-friendly, single-process session store with TTL-based expiry."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[tuple[str, str], tuple[Component, float]] = {}
        self._ttl = ttl_seconds
        
    def get(self, session_id: str, component_name: str) -> Component | None:
        self._cleanup()
        key = (session_id, component_name)
        if key in self._store:
            comp, exp = self._store[key]
            if time.time() < exp:
                self._store[key] = (comp, time.time() + self._ttl) # Touch
                return comp
            else:
                del self._store[key]
        return None

    def set(self, session_id: str, component_name: str, component: Component) -> None:
        self._cleanup()
        self._store[(session_id, component_name)] = (component, time.time() + self._ttl)

    def delete(self, session_id: str) -> None:
        keys_to_delete = [k for k in self._store.keys() if k[0] == session_id]
        for k in keys_to_delete:
            del self._store[k]
            
    def _cleanup(self) -> None:
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v[1]]
        for k in expired:
            del self._store[k]


class CookieSessionStore:
    """
    Stateless: state lives in signed cookie, server is stateless.
    (This requires the state to be passed in from the client and serialized/deserialized)
    For now, we'll keep it simple and just define the protocol. The actual
    state update logic will rely on the `state` field in EventRequest.
    """
    pass

__all__ = ["SessionStore", "InMemorySessionStore", "CookieSessionStore"]
