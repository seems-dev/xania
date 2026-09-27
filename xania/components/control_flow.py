from __future__ import annotations

from typing import Any, Callable, List, Optional, Tuple, Union
from xania.components.base import Var
from xania.components.component import Component


class Cond(Component):
    """Conditional rendering component.
    
    Compiles to JavaScript ternary expression:
    (condition ? true_view : false_view)
    """

    def __init__(self, condition: Union[Var, Any], true_view: Any, false_view: Optional[Any] = None, **kwargs):
        super().__init__(**kwargs)
        self.condition = Var.create(condition) if not isinstance(condition, Var) else condition
        self.true_view = true_view
        self.false_view = false_view if false_view is not None else ""

    def _get_all_imports(self):
        imports = super()._get_all_imports()
        if isinstance(self.true_view, Component):
            for lib, tags in self.true_view._get_all_imports().items():
                imports.setdefault(lib, set()).update(tags)
        if isinstance(self.false_view, Component):
            for lib, tags in self.false_view._get_all_imports().items():
                imports.setdefault(lib, set()).update(tags)
        return imports


def cond(condition: Union[Var, Any], true_view: Any, false_view: Optional[Any] = None, **kwargs) -> Cond:
    """Helper to conditionally render components based on a reactive Var."""
    return Cond(condition, true_view, false_view, **kwargs)


class Foreach(Component):
    """Dynamic array iteration component.
    
    Compiles to:
    (iterable ?? []).map((item, index) => render_fn(item, index))
    """

    def __init__(self, iterable: Union[Var, Any], render_fn: Callable[[Var, Optional[Var]], Any]):
        super().__init__()
        self.iterable = Var.create(iterable) if not isinstance(iterable, Var) else iterable
        self.render_fn = render_fn
        # Create dummy item and index vars to evaluate render_fn once at compile time
        self.item_var = Var("item")
        self.index_var = Var("index")
        try:
            self.rendered_child = render_fn(self.item_var, self.index_var)
        except TypeError:
            self.rendered_child = render_fn(self.item_var)  # type: ignore

    def _get_all_imports(self):
        imports = super()._get_all_imports()
        if isinstance(self.rendered_child, Component):
            for lib, tags in self.rendered_child._get_all_imports().items():
                imports.setdefault(lib, set()).update(tags)
        return imports


def foreach(iterable: Union[Var, Any], render_fn: Callable[..., Any]) -> Foreach:
    """Helper to dynamically map over an iterable state array in React."""
    return Foreach(iterable, render_fn)


class Match(Component):
    """Switch/Match conditional rendering component."""

    def __init__(self, condition: Union[Var, Any], *cases: Tuple[Any, Any], default: Optional[Any] = None):
        super().__init__()
        self.condition = Var.create(condition) if not isinstance(condition, Var) else condition
        self.cases = cases
        self.default = default

    def _get_all_imports(self):
        imports = super()._get_all_imports()
        for _, view in self.cases:
            if isinstance(view, Component):
                for lib, tags in view._get_all_imports().items():
                    imports.setdefault(lib, set()).update(tags)
        if isinstance(self.default, Component):
            for lib, tags in self.default._get_all_imports().items():
                imports.setdefault(lib, set()).update(tags)
        return imports


def match(condition: Union[Var, Any], *cases: Tuple[Any, Any], default: Optional[Any] = None) -> Match:
    """Helper to match a state variable against multiple cases."""
    return Match(condition, *cases, default=default)
