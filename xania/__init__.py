from __future__ import annotations

__version__ = "4.0.4"

# Reactive SPA Architecture (Xania 4.0)
from xania.components.base import Var, VarData, EventHandler
from xania.components.component import (
    Component,
    Fragment,
    to_react_prop,
    make_element,
    Div,
    Span,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    P,
    Button,
    Input,
    Textarea,
    Form,
    Label,
    Ul,
    Ol,
    Li,
    A,
    Img,
    Nav,
    Header,
    Footer,
    Section,
    Main,
    Aside,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Select,
    Option,
    Video,
    Audio,
    Canvas,
    Iframe,
    Link,
)
from xania.components.control_flow import (
    Cond,
    cond,
    Foreach,
    foreach,
    Match,
    match,
)
from xania.state.state import BaseState, StateMeta, StateRegistry, default_registry
from xania.compiler.compiler import SpaCompiler, PageDef
from xania.compiler.templates import RenderUtils

# Standard Modern UI Primitives
from xania.ui.components import (
    Alert,
    Badge,
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
    LucideIcon,
    StatCard,
    TableHeader,
    TableRow,
)

# Optional Server & Legacy Web Mount
try:
    from xania.server.app import XaniaServer, create_app
except ImportError:
    XaniaServer = None
    create_app = None

try:
    from xania.web.serve import mount_spa
except ImportError:
    mount_spa = None

__all__ = [
    # Metamodel & Reactivity
    "Var",
    "VarData",
    "EventHandler",
    "Component",
    "Fragment",
    "to_react_prop",
    "make_element",
    # Elements
    "Div",
    "Span",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "P",
    "Button",
    "Input",
    "Textarea",
    "Form",
    "Label",
    "Ul",
    "Ol",
    "Li",
    "A",
    "Link",
    "Img",
    "Nav",
    "Header",
    "Footer",
    "Section",
    "Main",
    "Aside",
    "Table",
    "Thead",
    "Tbody",
    "Tr",
    "Th",
    "Td",
    "Select",
    "Option",
    "Video",
    "Audio",
    "Canvas",
    "Iframe",
    # Control Flow
    "Cond",
    "cond",
    "Foreach",
    "foreach",
    "Match",
    "match",
    # State Engine
    "BaseState",
    "StateMeta",
    "StateRegistry",
    "default_registry",
    # Compiler
    "SpaCompiler",
    "PageDef",
    "RenderUtils",
    # Standard UI
    "LucideIcon",
    "Card",
    "CardHeader",
    "CardTitle",
    "CardDescription",
    "CardContent",
    "CardFooter",
    "Badge",
    "StatCard",
    "Alert",
    "TableHeader",
    "TableRow",
    # Server & Serving
    "XaniaServer",
    "create_app",
    "mount_spa",
]
