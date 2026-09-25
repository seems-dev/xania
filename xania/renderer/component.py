from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from xania.renderer.elements import Element
from xania.renderer.render import render as render_html
from xania.renderer.state import State, useRef, useState


@dataclass
class Component:
    """
    Production-oriented base component.

    - `id`: stable DOM container id (no random ids scattered)
    - `state`: persisted server-side (per component instance; can be replaced with session storage later)
    """

    id: str
    state: State = field(default_factory=State)
    _mounted: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Component.id must be non-empty")
        # Initialize state only once.
        if not self.state._data:  # type: ignore[attr-defined]
            self.state = State(**self.initial_state())

    def initial_state(self) -> dict[str, Any]:
        return {}

    def render(self, state: State) -> Element | str:
        raise NotImplementedError
        
    def mount(self) -> None:
        """Called once when the component is first rendered to a user session.
        
        Can be defined as `async def mount(self)` for async I/O operations.
        Synchronous mount() will be run in a thread pool to avoid blocking
        the async event loop.
        """
        pass

    def update(self, old_state: dict[str, Any]) -> None:
        """Called before re-render when state has changed.
        
        `old_state` is a shallow JSON snapshot (dict) of the previous state,
        NOT a deep copy of the State object. See State Serialization Rules.
        
        Can be defined as `async def update(self, old_state)` for async I/O.
        """
        pass

    def unmount(self) -> None:
        """Called when the component is removed (navigation away, session expiry).
        
        Use this to clean up database connections, background tasks, etc.
        Can be defined as `async def unmount(self)` for async cleanup.
        """
        pass

    async def handle(self, action: str, payload: dict[str, Any]) -> None:
        handler = getattr(self, f"on_{action}", None)
        if handler:
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                await handler(self.state, payload)
            else:
                handler(self.state, payload)

    def action(self, name: str | Any, **payload: Any) -> str:
        """Generate an onclick JS string automatically.

        Usage:
            Button("Click me", onclick=self.action("increment"))
            Button("Increment", onclick=self.action(self.on_increment))
            Button("Delete", onclick=self.action(self.on_delete, item_id=42))
        """
        import json as _json
        if callable(name):
            method_name = getattr(name, "__name__", "")
            if not method_name or method_name == "<lambda>":
                raise TypeError("Anonymous lambdas cannot be used with self.action(). Pass a named method or action string.")
            if method_name.startswith("on_"):
                method_name = method_name[3:]
            name = method_name

        if payload:
            return f"App.dispatch(this,'{name}',{_json.dumps(payload)})"
        return f"App.dispatch(this,'{name}')"

    def to_html(self) -> str:
        self.state.reset_hooks()
        return render_html(self.render(self.state))
        
    def to_state_dict(self) -> dict[str, Any]:
        """Serialize component state for session storage."""
        return self.state.to_dict()

    def load_state_dict(self, data: dict[str, Any]) -> None:
        """Restore component state from session storage."""
        self.state = State(**data)


__all__ = ["Component", "useState", "useRef"]
