from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Type
from xania.components.base import Var, VarData


class StateMeta(type):
    """Metaclass that turns class attribute accesses into reactive Var expressions."""

    def __new__(mcs, name: str, bases: tuple, namespace: dict[str, Any]):
        cls = super().__new__(mcs, name, bases, namespace)
        cls._fields = set()
        cls._defaults = {}

        # Collect annotations
        annotations = namespace.get("__annotations__", {})
        for field_name in annotations:
            if not field_name.startswith("_"):
                cls._fields.add(field_name)
                if field_name in namespace:
                    cls._defaults[field_name] = namespace[field_name]
                else:
                    cls._defaults[field_name] = None

        # Collect default values directly assigned in class body
        for k, v in namespace.items():
            if not k.startswith("_") and not callable(v) and not isinstance(v, (classmethod, staticmethod, property)):
                cls._fields.add(k)
                cls._defaults[k] = v

        return cls

    def __getattribute__(cls, name: str) -> Any:
        # Check standard attributes first
        if name.startswith("_") or name in ("mro", "register"):
            return super().__getattribute__(name)
        
        fields = super().__getattribute__("_fields") if "_fields" in cls.__dict__ else set()
        if name in fields:
            var_data = VarData(state_name=cls.__name__, field_name=name)
            return Var(f"state.{name}", _var_data=var_data)

        val = super().__getattribute__(name)
        # If it's a method on the state class, attach qualname for event dispatching
        if callable(val) and not name.startswith("_"):
            return val
        return val


class BaseState(metaclass=StateMeta):
    """Production Reactive State Engine for Xania 4.0 SPA applications.
    
    Tracks dirty state mutations dynamically and extracts minimal sparse JSON deltas
    to synchronize with the client-side React SPA over WebSocket.
    """

    _fields: Set[str] = set()
    _defaults: Dict[str, Any] = {}

    def __init__(self, **kwargs: Any):
        self._dirty_fields: Set[str] = set()
        self._queued_events: List[Dict[str, Any]] = []

        # Populate defaults
        for field, default in self._defaults.items():
            super().__setattr__(field, default)

        # Populate initial values
        for k, v in kwargs.items():
            setattr(self, k, v)

        # Clear dirty fields after initialization
        self._dirty_fields.clear()

    def __setattr__(self, name: str, value: Any) -> None:
        if not name.startswith("_"):
            old_val = getattr(self, name, None)
            if old_val != value:
                self._dirty_fields.add(name)
        super().__setattr__(name, value)

    def get_delta(self) -> Dict[str, Any]:
        """Extract only fields modified during the current event cycle."""
        delta = {field: getattr(self, field) for field in self._dirty_fields}
        self._dirty_fields.clear()
        return delta

    def get_full_state(self) -> Dict[str, Any]:
        """Extract complete serialized state for initial hydration."""
        return {field: getattr(self, field, None) for field in self._fields}

    def get_queued_events(self) -> List[Dict[str, Any]]:
        """Return and clear any special browser directives (redirects, toasts)."""
        events = list(self._queued_events)
        self._queued_events.clear()
        return events

    # --- Client Directives ---

    def redirect(self, path: str) -> None:
        """Tell the frontend React Router to navigate to a new route."""
        self._queued_events.append({"type": "redirect", "path": path})

    def toast(self, message: str, level: str = "info") -> None:
        """Trigger a client-side toast notification."""
        self._queued_events.append({"type": "toast", "message": message, "level": level})

    def console_log(self, *args: Any) -> None:
        """Send a console.log instruction to the client browser."""
        self._queued_events.append({"type": "console_log", "data": args})


class StateRegistry:
    """Session-scoped registry storing state instances per client connection."""

    def __init__(self):
        self._states: Dict[str, Dict[str, BaseState]] = {}

    def get_state(self, session_id: str, state_cls: Type[BaseState]) -> BaseState:
        session_states = self._states.setdefault(session_id, {})
        cls_name = state_cls.__name__
        if cls_name not in session_states:
            session_states[cls_name] = state_cls()
        return session_states[cls_name]

    def remove_session(self, session_id: str) -> None:
        self._states.pop(session_id, None)


# Global singleton registry for WebSocket sessions
default_registry = StateRegistry()
