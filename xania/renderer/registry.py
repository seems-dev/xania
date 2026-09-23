from __future__ import annotations

from typing import Dict, Type, Callable, Any, Tuple

from xania.renderer.component import Component
from xania.renderer.session import SessionStore, InMemorySessionStore


class ComponentRegistry:
    """
    Central registry for component instances.

    Updated to handle session-scoped instances to prevent state bleeding
    across different users.
    """

    _templates: Dict[str, Tuple[Type[Component], dict[str, Any]]] = {}
    _session_store: SessionStore = InMemorySessionStore()
    _active_components: dict[str, set[str]] = {}

    @classmethod
    def configure_store(cls, store: SessionStore) -> None:
        cls._session_store = store

    @classmethod
    def register(cls, name: str, component_class: Type[Component], **default_kwargs: Any) -> None:
        cls._templates[name] = (component_class, default_kwargs)

    @classmethod
    def get(cls, name: str, session_id: str) -> Component:
        try:
            component_class, kwargs = cls._templates[name]
        except KeyError as e:
            raise KeyError(f"Component not registered: {name}") from e
            
        instance = cls._session_store.get(session_id, name)
        if instance is None:
            instance = component_class(**kwargs)
            cls._session_store.set(session_id, name, instance)
            
        if session_id not in cls._active_components:
            cls._active_components[session_id] = set()
        cls._active_components[session_id].add(name)
            
        return instance

    @classmethod
    def all_templates(cls) -> dict[str, Tuple[Type[Component], dict[str, Any]]]:
        return dict(cls._templates)
        
    @classmethod
    def remove(cls, name: str, session_id: str) -> None:
        """Remove a component from the active session and store."""
        if session_id in cls._active_components:
            cls._active_components[session_id].discard(name)
        cls._session_store.delete_component(session_id, name)



__all__ = ["ComponentRegistry"]
