from __future__ import annotations

from html import escape
from typing import Any

from xania.renderer.elements import Element, VoidElement


def _escape_attr(value: Any) -> str:
    # Escape for HTML attributes surrounded with double quotes.
    return escape(str(value), quote=True)


def _normalize_attr_name(name: str) -> str:
    if name == "class_name" or name == "class_":
        return "class"
    if name == "for_":
        return "for"
    if name == "http_equiv":
        return "http-equiv"
    if name == "inner_html":
        return "innerHTML"
        
    if name.startswith("_at_"):
        return "@" + name[4:].replace("__", ".").replace("_", "-")
        
    if name.startswith("x_bind_"):
        return "x-bind:" + name[7:].replace("__", ".").replace("_", "-")
        
    if name.startswith("x_on_"):
        return "x-on:" + name[5:].replace("__", ".").replace("_", "-")
        
    if name.startswith("x_transition_"):
        suffix = name[13:]
        for prefix in ("enter_start", "enter_end", "leave_start", "leave_end", "enter", "leave"):
            if suffix.startswith(prefix):
                rest = suffix[len(prefix):]
                return f"x-transition:{prefix.replace('_', '-')}" + rest.replace("__", ".").replace("_", "-")
        return "x-transition:" + suffix.replace("__", ".").replace("_", "-")

    return name.replace("__", ".").replace("_", "-")


def serialize(node: Element | str | None) -> str:
    """
    Convert VDOM nodes into HTML.

    - Escapes text nodes
    - Escapes attribute values
    - Normalizes python-friendly attribute names (class_name -> class, etc.)
    """
    if node is None:
        return ""

    if isinstance(node, str):
        return escape(node)

    from xania.renderer.elements import LazyElement, ProviderElement
    
    if isinstance(node, LazyElement):
        # Evaluate the component and serialize the resulting tree
        return serialize(node.func(*node.args, **node.kwargs))
        
    if isinstance(node, ProviderElement):
        # Push context, serialize children, pop context
        stack = node.context._var.get()
        if stack is None:
            stack = []
        new_stack = stack + [node.value]
        token = node.context._var.set(new_stack)
        try:
            children_html = "".join(serialize(c if isinstance(c, (Element, str)) else str(c)) for c in node.children if c is not None)
            return f'<div style="display: contents;">{children_html}</div>'
        finally:
            node.context._var.reset(token)

    if isinstance(node, VoidElement):
        attrs = _serialize_attrs(node.attrs)
        return f"<{node.tag}{attrs} />"

    attrs = _serialize_attrs(node.attrs)
    children_html = "".join(serialize(c if isinstance(c, (Element, str)) else str(c)) for c in node.children if c is not None)
    return f"<{node.tag}{attrs}>{children_html}</{node.tag}>"


def _serialize_attrs(attrs: dict[str, Any]) -> str:
    parts: list[str] = []
    for k, v in attrs.items():
        name = _normalize_attr_name(k)
        if v is None or v is False:
            continue
        if v is True:
            parts.append(name)
            continue
        parts.append(f'{name}="{_escape_attr(v)}"')
    return (" " + " ".join(parts)) if parts else ""


__all__ = ["serialize", "_normalize_attr_name", "_serialize_attrs"]
