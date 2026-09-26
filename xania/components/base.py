from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass(frozen=True)
class VarData:
    """Metadata associated with a reactive Var expression."""
    state_name: str = ""
    field_name: str = ""
    default_value: Any = None
    imports: Dict[str, List[str]] = field(default_factory=dict)
    hooks: List[str] = field(default_factory=list)


class Var:
    """Represents a reactive JavaScript expression derived from Python state or props.
    
    Operates like Reflex's Var: overloads standard Python operators (+, -, ==, [], etc.)
    to construct JavaScript AST expressions that evaluate dynamically on the client.
    """

    def __init__(
        self,
        _js_expr: str,
        _var_data: Optional[VarData] = None,
        _type: type = Any,
    ):
        self._js_expr = _js_expr
        self._var_data = _var_data or VarData()
        self._type = _type

    @classmethod
    def create(cls, value: Any) -> Var:
        """Create a Var from any Python primitive, dictionary, list, or existing Var."""
        if isinstance(value, Var):
            return value
        if isinstance(value, str):
            # Safe JSON string escaping
            return cls(json.dumps(value), _type=str)
        if isinstance(value, bool):
            return cls("true" if value else "false", _type=bool)
        if isinstance(value, (int, float)):
            return cls(str(value), _type=type(value))
        if value is None:
            return cls("null", _type=type(None))
        if callable(value) and hasattr(value, "__self__") and hasattr(value, "__name__"):
            # Method reference on a state class e.g. State.increment
            target_class = value.__self__.__class__.__name__ if hasattr(value.__self__, "__class__") else ""
            method_name = value.__name__
            return cls(f'"{target_class}.{method_name}"', _type=Callable)
        
        # Complex data structures (dicts, lists, dataclasses, etc.)
        try:
            serialized = json.dumps(value)
            return cls(serialized, _type=type(value))
        except (TypeError, ValueError):
            return cls(str(value), _type=type(value))

    def to_js(self) -> str:
        """Return the JavaScript representation of this Var."""
        return self._js_expr

    def __str__(self) -> str:
        if self._var_data and self._var_data.default_value is not None:
            return str(self._var_data.default_value)
        return self.to_js()

    def __repr__(self) -> str:
        return f"Var({self._js_expr!r}, type={self._type})"

    # --- Operator Overloads for Reactivity ---

    def __add__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} + {other_var._js_expr})", self._var_data)

    def __radd__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({other_var._js_expr} + {self._js_expr})", self._var_data)

    def __sub__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} - {other_var._js_expr})", self._var_data)

    def __rsub__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({other_var._js_expr} - {self._js_expr})", self._var_data)

    def __mul__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} * {other_var._js_expr})", self._var_data)

    def __rmul__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({other_var._js_expr} * {self._js_expr})", self._var_data)

    def __truediv__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} / {other_var._js_expr})", self._var_data)

    def __mod__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} % {other_var._js_expr})", self._var_data)

    def __eq__(self, other: Any) -> Var:  # type: ignore[override]
        other_var = Var.create(other)
        return Var(f"({self._js_expr} === {other_var._js_expr})", self._var_data, _type=bool)

    def __ne__(self, other: Any) -> Var:  # type: ignore[override]
        other_var = Var.create(other)
        return Var(f"({self._js_expr} !== {other_var._js_expr})", self._var_data, _type=bool)

    def __gt__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} > {other_var._js_expr})", self._var_data, _type=bool)

    def __ge__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} >= {other_var._js_expr})", self._var_data, _type=bool)

    def __lt__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} < {other_var._js_expr})", self._var_data, _type=bool)

    def __le__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} <= {other_var._js_expr})", self._var_data, _type=bool)

    def __getitem__(self, key: Any) -> Var:
        key_var = Var.create(key)
        return Var(f"({self._js_expr}[{key_var._js_expr}])", self._var_data)

    def __getattr__(self, name: str) -> Var:
        if name.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return Var(f"({self._js_expr}.{name})", self._var_data)

    def __and__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} && {other_var._js_expr})", self._var_data, _type=bool)

    def __or__(self, other: Any) -> Var:
        other_var = Var.create(other)
        return Var(f"({self._js_expr} || {other_var._js_expr})", self._var_data, _type=bool)

    def __invert__(self) -> Var:
        return Var(f"(!{self._js_expr})", self._var_data, _type=bool)


class EventHandler:
    """Represents a client event handler dispatching to a server state handler or client JS."""

    def __init__(self, target: Union[str, Callable, Any], args_spec: Optional[List[str]] = None):
        self.target = target
        self.args_spec = args_spec or []

    def to_js(self) -> str:
        if isinstance(self.target, str):
            # If target contains () or arrow function, treat as raw js callback
            if "=>" in self.target or "(" in self.target:
                return self.target
            # Otherwise it's an event name to send via websocket:
            return f"(e) => sendEvent('{self.target}', e)"
        
        if callable(self.target):
            # Check for class method (State.method)
            qualname = getattr(self.target, "__qualname__", "")
            name = getattr(self.target, "__name__", "")
            return f"(e) => sendEvent('{qualname or name}', e)"
        
        return f"(e) => sendEvent('{str(self.target)}', e)"
