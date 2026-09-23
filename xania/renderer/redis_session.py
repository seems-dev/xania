from __future__ import annotations

import json
import time
from typing import Any

try:
    import redis  # type: ignore[import-untyped, import-not-found]
except ImportError:
    redis = None  # type: ignore

from xania.renderer.component import Component
from xania.renderer.session import SessionStore


class RedisSessionStore:
    """Production-grade session store backed by Redis."""

    def __init__(self, redis_url: str, ttl_seconds: int = 3600):
        if redis is None:
            raise ImportError("Redis is not installed. Please `pip install redis`.")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = ttl_seconds

    def _make_key(self, session_id: str, component_name: str) -> str:
        return f"xania:session:{session_id}:comp:{component_name}"

    def get(self, session_id: str, component_name: str) -> Component | None:
        key = self._make_key(session_id, component_name)
        data_str = self.redis.get(key)
        if not data_str:
            return None
            
        # Touch TTL
        self.redis.expire(key, self.ttl)
        
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            return None

        # Re-hydrate the component instance
        from xania.renderer.registry import ComponentRegistry
        templates = ComponentRegistry.all_templates()
        if component_name not in templates:
            return None
            
        component_class, kwargs = templates[component_name]
        instance = component_class(**kwargs)
        if hasattr(instance, "load_state_dict"):
            instance.load_state_dict(data)
        
        return instance

    def set(self, session_id: str, component_name: str, component: Component) -> None:
        key = self._make_key(session_id, component_name)
        
        if hasattr(component, "to_state_dict"):
            data = component.to_state_dict()
        else:
            data = {}
            
        self.redis.setex(key, self.ttl, json.dumps(data))

    def delete(self, session_id: str) -> None:
        # Note: Redis doesn't support wildcard deletion natively without SCAN.
        # But we don't strictly need this if we just rely on TTL, 
        # or we could keep a set of keys per session.
        # For this minimal implementation, TTL handles cleanup.
        pass

    def delete_component(self, session_id: str, component_name: str) -> None:
        key = self._make_key(session_id, component_name)
        self.redis.delete(key)
