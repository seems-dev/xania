from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Union
from xania.components.base import Var, EventHandler


def to_react_prop(key: str) -> str:
    """Map pythonic kwargs to standard React JSX attribute names."""
    special_mapping = {
        "class_name": "className",
        "for_": "htmlFor",
        "html_for": "htmlFor",
        "on_click": "onClick",
        "on_change": "onChange",
        "on_submit": "onSubmit",
        "on_keydown": "onKeyDown",
        "on_keyup": "onKeyUp",
        "on_mouseenter": "onMouseEnter",
        "on_mouseleave": "onMouseLeave",
        "tab_index": "tabIndex",
        "auto_focus": "autoFocus",
        "auto_complete": "autoComplete",
        "read_only": "readOnly",
        "src_set": "srcSet",
        "view_box": "viewBox",
    }
    if key in special_mapping:
        return special_mapping[key]

    # Convert snake_case on_event to onEvent
    if key.startswith("on_"):
        parts = key.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])

    # Convert data_* and aria_* to data-* and aria-*
    if key.startswith("data_") or key.startswith("aria_"):
        return key.replace("_", "-")

    # Standard camelCase conversion for React props
    parts = key.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class Component:
    """Universal Base Component for the Xania SPA metamodel.
    
    Allows direct evaluation of declarative component trees and wrapping of arbitrary
    npm / React components (Radix, Lucide, Framer Motion, Tailwind) in pure Python.
    """

    library: str = ""         # npm package name (e.g., "lucide-react", "@radix-ui/themes")
    tag: str = "div"          # JSX element name
    is_default: bool = False  # True if default export (e.g., import Foo from "foo")
    alias: str = ""           # Optional import alias

    def __init__(self, *children: Any, **props: Any):
        self.children: List[Any] = list(children)
        self.props: Dict[str, Any] = {}
        self.custom_attrs: Dict[str, Any] = {}

        for k, v in props.items():
            react_prop = to_react_prop(k)
            # Event handlers
            if react_prop.startswith("on") and (callable(v) or isinstance(v, (str, EventHandler))):
                self.props[react_prop] = v if isinstance(v, EventHandler) else EventHandler(v)
            elif isinstance(v, Var):
                self.props[react_prop] = v
            else:
                self.props[react_prop] = Var.create(v)

    @property
    def attrs(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.props.items():
            if k == "className":
                raw = v._var_data.default_value if isinstance(v, Var) and v._var_data and v._var_data.default_value is not None else (v.to_js().strip('"') if isinstance(v, Var) else str(v))
                result["class_name"] = raw
            elif isinstance(v, EventHandler):
                continue
            elif isinstance(v, Var):
                val = v._var_data.default_value if v._var_data and v._var_data.default_value is not None else v.to_js().strip('"')
                result[k] = val
            else:
                result[k] = v
        return result

    def to_html(self) -> str:
        from xania.engine.serializer import serialize
        return serialize(self)

    @classmethod
    def create(cls, *children: Any, **props: Any) -> Component:
        """Factory method to instantiate a component."""
        return cls(*children, **props)

    def _get_all_imports(self) -> Dict[str, Set[Any]]:
        """Traverse the entire component subtree and collect required npm imports."""
        imports: Dict[str, Set[Any]] = {}
        if self.library:
            imports.setdefault(self.library, set()).add((self.tag, self.is_default, self.alias))

        for child in self.children:
            if isinstance(child, Component):
                child_imports = child._get_all_imports()
                for lib, tags in child_imports.items():
                    imports.setdefault(lib, set()).update(tags)

        # Check imports needed by props (Vars with VarData)
        for prop_val in self.props.values():
            if isinstance(prop_val, Var) and prop_val._var_data.imports:
                for lib, tags in prop_val._var_data.imports.items():
                    for t in tags:
                        item = t if isinstance(t, tuple) else (t, False, "")
                        imports.setdefault(lib, set()).add(item)

        return imports

    def _get_all_hooks(self) -> Set[str]:
        """Collect React hooks declared in the subtree."""
        hooks: Set[str] = set()
        for child in self.children:
            if isinstance(child, Component):
                hooks.update(child._get_all_hooks())
        for prop_val in self.props.values():
            if isinstance(prop_val, Var) and prop_val._var_data.hooks:
                hooks.update(prop_val._var_data.hooks)
        return hooks

    def __repr__(self) -> str:
        return f"<{self.tag} props={list(self.props.keys())} children={len(self.children)}>"


class Fragment(Component):
    """React.Fragment container."""
    tag = "Fragment"
    library = "react"
    is_default = False


# Helper factory for creating simple standard HTML tag components
def make_element(tag_name: str) -> type[Component]:
    return type(
        tag_name.capitalize(),
        (Component,),
        {"tag": tag_name, "library": ""},
    )


# Standard HTML5 Components
Div = make_element("div")
Span = make_element("span")
H1 = make_element("h1")
H2 = make_element("h2")
H3 = make_element("h3")
H4 = make_element("h4")
H5 = make_element("h5")
H6 = make_element("h6")
P = make_element("p")
Button = make_element("button")
Input = make_element("input")
Textarea = make_element("textarea")
Form = make_element("form")
Label = make_element("label")
Ul = make_element("ul")
Ol = make_element("ol")
Li = make_element("li")
A = make_element("a")
Img = make_element("img")
Nav = make_element("nav")
Header = make_element("header")
Footer = make_element("footer")
Section = make_element("section")
Main = make_element("main")
Aside = make_element("aside")
Table = make_element("table")
Thead = make_element("thead")
Tbody = make_element("tbody")
Tr = make_element("tr")
Th = make_element("th")
Td = make_element("td")
Select = make_element("select")
Option = make_element("option")
Video = make_element("video")
Audio = make_element("audio")
Canvas = make_element("canvas")
Iframe = make_element("iframe")
Svg = make_element("svg")
Path = make_element("path")


def Element(tag: str, *children: Any, **props: Any) -> Component:
    """Create a dynamic Component with an arbitrary JSX tag."""
    comp = Component(*children, **props)
    comp.tag = tag
    return comp


class Link(Component):
    """Client-side navigation link for React Router SPA."""
    library = "react-router-dom"
    tag = "Link"

    def __init__(self, *children: Any, to: str = "/", href: Optional[str] = None, **props: Any):
        target = href if href is not None else to
        super().__init__(*children, to=target, **props)


