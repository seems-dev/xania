from __future__ import annotations
from typing import Any


# ─────────────────────────────────────────────
#  Core
# ─────────────────────────────────────────────

class Element:
    def __init__(self, tag: str, *children: Any, **attrs: Any) -> None:
        self.tag = tag
        
        flat_children = []
        for child in children:
            if isinstance(child, (list, tuple)):
                flat_children.extend(child)
            else:
                flat_children.append(child)
                
        self.children: tuple[Any, ...] = tuple(flat_children)
        self.attrs: dict[str, Any] = attrs

    def render_attrs(self) -> str:
        attrs_str = ""
        for key, value in self.attrs.items():
            if key == "class_name":
                key = "class"
            elif key == "for_":
                key = "for"
            elif key == "http_equiv":
                key = "http-equiv"
            
            if key.startswith("_at_"):
                key = "@" + key[4:]
            else:
                key = key.replace("_", "-")
                
            if isinstance(value, bool):
                if value:
                    attrs_str += f" {key}"
            else:
                attrs_str += f' {key}="{value}"'
        return attrs_str

    def __repr__(self) -> str:
        return f"Element(tag={self.tag!r}, children={self.children!r}, attrs={self.attrs!r})"

class LazyElement(Element):
    """Holds a reference to a functional component and its arguments for lazy evaluation."""
    def __init__(self, func: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__("")  # No tag
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def evaluate(self) -> Any:
        return self.func(*self.args, **self.kwargs)

    def to_dict(self) -> dict[str, Any]:
        result = self.evaluate()
        if isinstance(result, Element):
            return result.to_dict()
        return {"tag": "", "children": [str(result)]}

class ProviderElement(Element):
    """Evaluates children inside a Context.Provider."""
    def __init__(self, context: Any, value: Any, children: Any) -> None:
        super().__init__("") # No tag
        self.context = context
        self.value = value
        self.children = tuple(children) if isinstance(children, (list, tuple)) else (children,)

    def to_dict(self) -> dict[str, Any]:
        stack = self.context._var.get()
        if stack is None:
            stack = []
        new_stack = stack + [self.value]
        token = self.context._var.set(new_stack)
        try:
            children = []
            for child in self.children:
                if isinstance(child, Element):
                    children.append(child.to_dict())
                elif child is not None:
                    children.append(str(child))
            
            # Since ProviderElement shouldn't appear in the DOM as a tag,
            # we can return a transparent wrapper dict that differ.py can flatten,
            # or we can just flatten it here! But wait, `to_dict` returns a single dict.
            # If we flatten it here, a Provider returning multiple children would break the `dict` signature.
            # Let's return a special `<provider>` dict that differ.py can handle, or just a `div` for simplicity.
            # No, if we return `{"tag": "fragment", "children": children}`, differ.py might need to handle it.
            # For now, let's just make ProviderElement a logical `<div class="provider-wrapper" style="display:contents;">`
            # to keep VDOM diffing easy without refactoring differ.py to handle fragments!
            return {"tag": "div", "attrs": {"style": "display: contents;"}, "children": children}
        finally:
            self.context._var.reset(token)

def component(func: Any = None):
    """Decorator to make functional components evaluate lazily."""
    if func is None:
        return component
    
    import functools
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> LazyElement:
        return LazyElement(func, *args, **kwargs)
    return wrapper

    def to_dict(self) -> dict[str, Any]:
        """Convert Element tree → dict so Render can consume it."""
        children = []
        for child in self.children:
            if isinstance(child, Element):
                children.append(child.to_dict())
            elif child is not None:
                children.append(str(child))

        result: dict[str, Any] = {"tag": self.tag}

        if self.attrs:
            raw_attrs: dict[str, Any] = {}
            for k, v in self.attrs.items():
                if k == "class_name":
                    k = "class"
                elif k == "for_":
                    k = "for"
                elif k == "http_equiv":
                    k = "http-equiv"
                    
                if k.startswith("_at_"):
                    raw_attrs["@" + k[4:]] = v
                else:
                    raw_attrs[k.replace("_", "-")] = v
            result["attrs"] = raw_attrs

        if children:
            result["children"] = children

        return result

    def render(self) -> str:
        children_html = ""
        for child in self.children:
            if isinstance(child, Element):
                children_html += child.render()
            elif child is not None:
                children_html += str(child)
        return f"<{self.tag}{self.render_attrs()}>{children_html}</{self.tag}>"

    def __repr__(self) -> str:
        return f"Element(tag={self.tag!r}, children={self.children!r}, attrs={self.attrs!r})"


class VoidElement(Element):
    """Self-closing tags: <img />, <input />, <br /> etc."""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"tag": self.tag, "void": True}
        if self.attrs:
            raw_attrs: dict[str, Any] = {}
            for k, v in self.attrs.items():
                if k == "class_name":
                    k = "class"
                elif k == "for_":
                    k = "for"
                    
                if k.startswith("_at_"):
                    raw_attrs["@" + k[4:]] = v
                else:
                    raw_attrs[k.replace("_", "-")] = v
            result["attrs"] = raw_attrs
        return result

    def render(self) -> str:
        return f"<{self.tag}{self.render_attrs()} />"


# ─────────────────────────────────────────────
#  Void tags set
# ─────────────────────────────────────────────

VOID_TAGS: frozenset[str] = frozenset({
    "area", "base", "br", "col", "embed",
    "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr"
})


# ─────────────────────────────────────────────
#  Dict → Element converter
# ─────────────────────────────────────────────

def dict_to_element(node: dict | str) -> Element | str:
    if isinstance(node, str):
        return node

    tag: str = node["tag"]
    attrs: dict[str, Any] = node.get("attrs", {})
    children: list = node.get("children", [])

    normalized_attrs: dict[str, Any] = {
        "class_name" if k == "class" else k: v
        for k, v in attrs.items()
    }

    if tag in VOID_TAGS:
        return VoidElement(tag, **normalized_attrs)

    converted_children = [dict_to_element(child) for child in children]
    return Element(tag, *converted_children, **normalized_attrs)


# ─────────────────────────────────────────────
#  Block elements
# ─────────────────────────────────────────────

def Div(*children: Any, **attrs: Any) -> Element:
    return Element("div", *children, **attrs)

def Section(*children: Any, **attrs: Any) -> Element:
    return Element("section", *children, **attrs)

def Article(*children: Any, **attrs: Any) -> Element:
    return Element("article", *children, **attrs)

def Aside(*children: Any, **attrs: Any) -> Element:
    return Element("aside", *children, **attrs)

def Header(*children: Any, **attrs: Any) -> Element:
    return Element("header", *children, **attrs)

def Footer(*children: Any, **attrs: Any) -> Element:
    return Element("footer", *children, **attrs)

def Main(*children: Any, **attrs: Any) -> Element:
    return Element("main", *children, **attrs)

def Nav(*children: Any, **attrs: Any) -> Element:
    return Element("nav", *children, **attrs)

def Ul(*children: Any, **attrs: Any) -> Element:
    return Element("ul", *children, **attrs)

def Ol(*children: Any, **attrs: Any) -> Element:
    return Element("ol", *children, **attrs)

def Li(*children: Any, **attrs: Any) -> Element:
    return Element("li", *children, **attrs)

def Table(*children: Any, **attrs: Any) -> Element:
    return Element("table", *children, **attrs)

def Thead(*children: Any, **attrs: Any) -> Element:
    return Element("thead", *children, **attrs)

def Tbody(*children: Any, **attrs: Any) -> Element:
    return Element("tbody", *children, **attrs)

def Tr(*children: Any, **attrs: Any) -> Element:
    return Element("tr", *children, **attrs)

def Th(*children: Any, **attrs: Any) -> Element:
    return Element("th", *children, **attrs)

def Td(*children: Any, **attrs: Any) -> Element:
    return Element("td", *children, **attrs)

def Form(*children: Any, **attrs: Any) -> Element:
    """
    Form element.
    
    Submitting a Form is automatically intercepted and sent over WebSocket.
    Set `data_action` to route to a component handler.
    Example:
    ```python
    Form(
        Input(name="email"),
        Button("Submit", type="submit"),
        data_action="create_user" # Calls on_create_user(state, payload)
    )
    ```
    """
    return Element("form", *children, **attrs)

def Select(*children: Any, **attrs: Any) -> Element:
    return Element("select", *children, **attrs)

def Option(*children: Any, **attrs: Any) -> Element:
    return Element("option", *children, **attrs)

def Textarea(*children: Any, **attrs: Any) -> Element:
    return Element("textarea", *children, **attrs)

def Label(*children: Any, **attrs: Any) -> Element:
    return Element("label", *children, **attrs)

def Fieldset(*children: Any, **attrs: Any) -> Element:
    return Element("fieldset", *children, **attrs)

def Legend(*children: Any, **attrs: Any) -> Element:
    return Element("legend", *children, **attrs)

def Details(*children: Any, **attrs: Any) -> Element:
    return Element("details", *children, **attrs)

def Summary(*children: Any, **attrs: Any) -> Element:
    return Element("summary", *children, **attrs)

def Dialog(*children: Any, **attrs: Any) -> Element:
    return Element("dialog", *children, **attrs)

def Script(*children: Any, **attrs: Any) -> Element:
    return Element("script", *children, **attrs)

def Style(*children: Any, **attrs: Any) -> Element:
    return Element("style", *children, **attrs)

# ─────────────────────────────────────────────
#  Headings & text
# ─────────────────────────────────────────────

def H1(*children: Any, **attrs: Any) -> Element:
    return Element("h1", *children, **attrs)

def H2(*children: Any, **attrs: Any) -> Element:
    return Element("h2", *children, **attrs)

def H3(*children: Any, **attrs: Any) -> Element:
    return Element("h3", *children, **attrs)

def H4(*children: Any, **attrs: Any) -> Element:
    return Element("h4", *children, **attrs)

def H5(*children: Any, **attrs: Any) -> Element:
    return Element("h5", *children, **attrs)

def H6(*children: Any, **attrs: Any) -> Element:
    return Element("h6", *children, **attrs)

def P(*children: Any, **attrs: Any) -> Element:
    return Element("p", *children, **attrs)

def Span(*children: Any, **attrs: Any) -> Element:
    return Element("span", *children, **attrs)

def A(*children: Any, **attrs: Any) -> Element:
    return Element("a", *children, **attrs)

def Strong(*children: Any, **attrs: Any) -> Element:
    return Element("strong", *children, **attrs)

def Em(*children: Any, **attrs: Any) -> Element:
    return Element("em", *children, **attrs)

def B(*children: Any, **attrs: Any) -> Element:
    return Element("b", *children, **attrs)

def I(*children: Any, **attrs: Any) -> Element:
    return Element("i", *children, **attrs)

def U(*children: Any, **attrs: Any) -> Element:
    return Element("u", *children, **attrs)

def S(*children: Any, **attrs: Any) -> Element:
    return Element("s", *children, **attrs)

def Code(*children: Any, **attrs: Any) -> Element:
    return Element("code", *children, **attrs)

def Pre(*children: Any, **attrs: Any) -> Element:
    return Element("pre", *children, **attrs)

def Blockquote(*children: Any, **attrs: Any) -> Element:
    return Element("blockquote", *children, **attrs)

def Small(*children: Any, **attrs: Any) -> Element:
    return Element("small", *children, **attrs)

def Mark(*children: Any, **attrs: Any) -> Element:
    return Element("mark", *children, **attrs)

def Sub(*children: Any, **attrs: Any) -> Element:
    return Element("sub", *children, **attrs)

def Sup(*children: Any, **attrs: Any) -> Element:
    return Element("sup", *children, **attrs)

def Button(*children: Any, **attrs: Any) -> Element:
    """
    Button element.
    
    Optimistic UI hint:
    Use `data_optimistic` to provide JSON hints for immediate UI updates.
    Example:
    ```python
    Button("Like", onclick=self.action("like"), data_optimistic='{"text": "Liked!", "class_add": "text-red-500"}')
    ```
    """
    return Element("button", *children, **attrs)

# ─────────────────────────────────────────────
#  Void / self-closing elements
# ─────────────────────────────────────────────

def Img(**attrs: Any) -> VoidElement:
    return VoidElement("img", **attrs)

def Input(**attrs: Any) -> VoidElement:
    return VoidElement("input", **attrs)

def Br(**attrs: Any) -> VoidElement:
    return VoidElement("br", **attrs)

def Hr(**attrs: Any) -> VoidElement:
    return VoidElement("hr", **attrs)

def Link(**attrs: Any) -> VoidElement:
    return VoidElement("link", **attrs)

def Meta(**attrs: Any) -> VoidElement:
    return VoidElement("meta", **attrs)

def Slot(*children: Any, name: str = "children", **attrs: Any) -> Element:
    """A placeholder for children passed from a parent layout."""
    attrs["data-xania-slot"] = name
    return Element("div", *children, **attrs)



def tw(*classes: str) -> str:
    """
    Merge Tailwind classes cleanly. Filters out empty strings.

    Usage:
        tw("text-white", "bg-blue-500")               → "text-white bg-blue-500"
        tw("p-4", "mt-2" if active else "", "rounded") → "p-4 rounded"  (skips empty)
    """
    return " ".join(c for c in classes if c)