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

    def handle(self, action: str, payload: dict[str, Any]) -> None:
        handler = getattr(self, f"on_{action}", None)
        if handler:
            handler(self.state, payload)

    def action(self, name: str, **payload: Any) -> str:
        """Generate an onclick JS string automatically.

        Usage:
            Button("Click me", onclick=self.action("increment"))
        """
        import json as _json
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
