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
            
        return instance

    @classmethod
    def all_templates(cls) -> dict[str, Tuple[Type[Component], dict[str, Any]]]:
        return dict(cls._templates)


__all__ = ["ComponentRegistry"]
