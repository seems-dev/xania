from __future__ import annotations

from typing import Any, Sequence
from xania.components import (
    A,
    Button as BaseButton,
    Component,
    Div,
    Element,
    Form as BaseForm,
    H1,
    H2,
    H3,
    H4,
    Input as BaseInput,
    Label as BaseLabel,
    P,
    Span,
    Table as BaseTable,
    Tbody,
    Td,
    Th,
    Thead,
    Tr,
)


# ── Cards ─────────────────────────────────────────────────────────────────────

def Card(*children: Any, class_name: str = "", **kwargs: Any) -> Div:
    """Card container with modern rounded borders, dark backdrop, and subtle shadow."""
    cls = f"bg-zinc-900 border border-zinc-800 rounded-2xl shadow-xl overflow-hidden p-6 {class_name}".strip()
    return Div(*children, class_name=cls, **kwargs)


def CardHeader(*children: Any, class_name: str = "", **kwargs: Any) -> Div:
    """Header region of a card containing titles, badges, or action buttons."""
    cls = f"flex flex-col space-y-1.5 pb-4 {class_name}".strip()
    return Div(*children, class_name=cls, **kwargs)


def CardTitle(title: str, class_name: str = "", **kwargs: Any) -> H3:
    """Card primary title styled with high contrast."""
    cls = f"text-lg font-bold text-zinc-100 tracking-tight {class_name}".strip()
    return H3(title, class_name=cls, **kwargs)


def CardDescription(desc: str, class_name: str = "", **kwargs: Any) -> P:
    """Card secondary descriptive subtitle."""
    cls = f"text-xs text-zinc-400 {class_name}".strip()
    return P(desc, class_name=cls, **kwargs)


def CardContent(*children: Any, class_name: str = "", **kwargs: Any) -> Div:
    """Main body content area of a card."""
    cls = f"space-y-4 {class_name}".strip()
    return Div(*children, class_name=cls, **kwargs)


def CardFooter(*children: Any, class_name: str = "", **kwargs: Any) -> Div:
    """Footer bar of a card for actions, timestamps, or links."""
    cls = f"flex items-center justify-between pt-4 border-t border-zinc-800/80 mt-4 {class_name}".strip()
    return Div(*children, class_name=cls, **kwargs)


# ── Buttons ───────────────────────────────────────────────────────────────────

def Button(
    text: str,
    variant: str = "primary",
    size: str = "md",
    class_name: str = "",
    **kwargs: Any,
) -> BaseButton:
    """Interactive button styled with standard modern presets."""
    variants = {
        "primary": "bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-600 hover:to-rose-700 text-white shadow-lg shadow-pink-500/25",
        "secondary": "bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700",
        "danger": "bg-rose-600 hover:bg-rose-700 text-white shadow-lg shadow-rose-600/25",
        "success": "bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-600/25",
        "outline": "bg-transparent border border-zinc-700 hover:border-zinc-500 text-zinc-200",
        "ghost": "bg-transparent hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100",
    }
    sizes = {
        "sm": "px-3 py-1.5 text-xs rounded-lg",
        "md": "px-4 py-2 text-xs font-semibold rounded-xl",
        "lg": "px-6 py-3 text-sm font-semibold rounded-xl",
    }
    v_cls = variants.get(variant, variants["primary"])
    s_cls = sizes.get(size, sizes["md"])
    cls = f"inline-flex items-center justify-center transition font-medium focus:outline-none cursor-pointer {v_cls} {s_cls} {class_name}".strip()
    return BaseButton(text, class_name=cls, **kwargs)


# ── Badges ────────────────────────────────────────────────────────────────────

def Badge(
    text: str,
    variant: str = "neutral",
    class_name: str = "",
    **kwargs: Any,
) -> Span:
    """Rounded pill badge for status indicators, categories, and counts."""
    variants = {
        "success": "bg-emerald-950/80 text-emerald-400 border border-emerald-800/60",
        "warning": "bg-amber-950/80 text-amber-400 border border-amber-800/60",
        "danger": "bg-rose-950/80 text-rose-400 border border-rose-800/60",
        "info": "bg-blue-950/80 text-blue-400 border border-blue-800/60",
        "purple": "bg-purple-950/80 text-purple-400 border border-purple-800/60",
        "neutral": "bg-zinc-800/80 text-zinc-300 border border-zinc-700/60",
    }
    v_cls = variants.get(variant, variants["neutral"])
    cls = f"inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {v_cls} {class_name}".strip()
    return Span(text, class_name=cls, **kwargs)


# ── Inputs & Form Controls ────────────────────────────────────────────────────

def Input(
    placeholder: str = "",
    type: str = "text",
    debounce: int | None = 300,
    class_name: str = "",
    **kwargs: Any,
) -> BaseInput:
    """Single-line text input with sleek dark styling and automatic client debouncing."""
    cls = f"block w-full px-3 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 text-xs focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition {class_name}".strip()
    if debounce is not None and "data_debounce" not in kwargs and "data-debounce" not in kwargs:
        kwargs["data_debounce"] = str(debounce)
    return BaseInput(placeholder=placeholder, type=type, class_name=cls, **kwargs)


def Label(text: str, class_name: str = "", **kwargs: Any) -> BaseLabel:
    """Form label with crisp typography."""
    cls = f"block text-xs font-medium text-zinc-300 mb-1 {class_name}".strip()
    return BaseLabel(text, class_name=cls, **kwargs)


# ── Metric & Stat Cards ───────────────────────────────────────────────────────

def StatCard(
    title: str,
    value: str | int,
    change: str | None = None,
    icon: str | None = None,
    class_name: str = "",
    **kwargs: Any,
) -> Div:
    """Dashboard KPI card showing metric value, optional trend badge, and icon."""
    header_children: list[Any] = [
        P(title, class_name="text-xs font-medium text-zinc-400"),
    ]
    if icon:
        header_children.append(Span(icon, class_name="text-lg opacity-80"))

    content_children: list[Any] = [
        H2(str(value), class_name="text-2xl font-bold text-zinc-100 tracking-tight mt-2"),
    ]
    if change:
        is_pos = not change.startswith("-")
        badge_variant = "success" if is_pos else "danger"
        content_children.append(
            Div(
                Badge(change, variant=badge_variant),
                Span(" vs last period", class_name="text-xs text-zinc-500 ml-2"),
                class_name="flex items-center mt-2",
            )
        )

    return Card(
        Div(*header_children, class_name="flex items-center justify-between"),
        Div(*content_children),
        class_name=class_name,
        **kwargs,
    )


# ── Alerts & Notices ──────────────────────────────────────────────────────────

def Alert(
    message: str,
    title: str | None = None,
    variant: str = "info",
    class_name: str = "",
    **kwargs: Any,
) -> Div:
    """Callout box for success, info, warning, or error messages."""
    variants = {
        "info": "bg-blue-950/60 border-blue-800/60 text-blue-300",
        "success": "bg-emerald-950/60 border-emerald-800/60 text-emerald-300",
        "warning": "bg-amber-950/60 border-amber-800/60 text-amber-300",
        "error": "bg-rose-950/60 border-rose-800/60 text-rose-300",
    }
    v_cls = variants.get(variant, variants["info"])
    cls = f"p-4 rounded-xl border text-xs {v_cls} {class_name}".strip()

    children: list[Any] = []
    if title:
        children.append(H4(title, class_name="font-semibold mb-1"))
    children.append(P(message))

    return Div(*children, class_name=cls, **kwargs)


# ── Data Tables ───────────────────────────────────────────────────────────────

def Table(*children: Any, class_name: str = "", **kwargs: Any) -> Div:
    """Responsive table wrapper with rounded border and scroll container."""
    cls = f"w-full overflow-x-auto rounded-xl border border-zinc-800 {class_name}".strip()
    return Div(
        BaseTable(*children, class_name="w-full text-left border-collapse", **kwargs),
        class_name=cls,
    )


def TableHeader(*cells: str, class_name: str = "", **kwargs: Any) -> Thead:
    """Table header row defining column titles."""
    th_cells = [
        Th(cell, class_name="px-4 py-3 text-xs font-semibold text-zinc-400 bg-zinc-950/80 border-b border-zinc-800 uppercase tracking-wider")
        for cell in cells
    ]
    return Thead(Tr(*th_cells, class_name=class_name, **kwargs))


def TableRow(*cells: Any, class_name: str = "", **kwargs: Any) -> Tr:
    """Standard table row with subtle hover effect."""
    td_cells = [
        Td(cell, class_name="px-4 py-3.5 text-xs text-zinc-200 border-b border-zinc-800/60")
        for cell in cells
    ]
    return Tr(*td_cells, class_name=f"hover:bg-zinc-800/30 transition {class_name}".strip(), **kwargs)


# ── Layout & Navbar ───────────────────────────────────────────────────────────

def Navbar(
    brand: str,
    links: list[tuple[str, str]] | None = None,
    class_name: str = "",
    **kwargs: Any,
) -> Div:
    """Modern header navigation bar with glassmorphic backdrop."""
    nav_links = []
    if links:
        for title, href in links:
            nav_links.append(
                A(title, href=href, class_name="text-xs text-zinc-400 hover:text-pink-400 transition font-medium px-2 py-1")
            )

    return Div(
        Div(
            Div(
                Span("⚡", class_name="text-pink-500 mr-2 text-lg font-bold"),
                Span(brand, class_name="font-bold text-sm text-zinc-100 tracking-tight"),
                class_name="flex items-center",
            ),
            Div(*nav_links, class_name="flex items-center space-x-3") if nav_links else Div(),
            class_name="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between",
        ),
        class_name=f"w-full bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800 sticky top-0 z-50 {class_name}".strip(),
        **kwargs,
    )


# ── SVG Data Visualizations (Zero-JS Charts) ──────────────────────────────────

def LineChart(
    data: Sequence[float],
    width: int = 400,
    height: int = 120,
    stroke_color: str = "#ec4899",
    fill_color: str = "rgba(236, 72, 153, 0.12)",
    class_name: str = "",
    **kwargs: Any,
) -> Div:
    """Pure SVG responsive line chart / sparkline with smooth bezier curve paths."""
    if not data or len(data) < 2:
        return Div(P("Not enough data points", class_name="text-xs text-zinc-500 p-4"), class_name=class_name)

    min_val = min(data)
    max_val = max(data)
    val_range = max(max_val - min_val, 1e-6)

    padding = 10
    usable_width = width - (padding * 2)
    usable_height = height - (padding * 2)

    step = usable_width / (len(data) - 1)
    points = []
    for i, val in enumerate(data):
        x = padding + (i * step)
        y = height - padding - ((val - min_val) / val_range * usable_height)
        points.append((round(x, 1), round(y, 1)))

    d_line = f"M {points[0][0]},{points[0][1]} " + " ".join(f"L {p[0]},{p[1]}" for p in points[1:])
    d_area = f"{d_line} L {points[-1][0]},{height - padding} L {points[0][0]},{height - padding} Z"

    svg = Element(
        "svg",
        Element("path", d=d_area, fill=fill_color),
        Element("path", d=d_line, fill="none", stroke=stroke_color, stroke_width="2.5", stroke_linecap="round", stroke_linejoin="round"),
        viewBox=f"0 0 {width} {height}",
        class_name="w-full h-auto overflow-visible",
        preserveAspectRatio="none",
    )
    return Div(svg, class_name=f"w-full overflow-hidden rounded-xl {class_name}".strip(), **kwargs)


def BarChart(
    data: Sequence[tuple[str, float]],
    height: int = 140,
    bar_color: str = "#8b5cf6",
    class_name: str = "",
    **kwargs: Any,
) -> Div:
    """Pure SVG responsive bar chart with category labels."""
    if not data:
        return Div(P("No data for chart", class_name="text-xs text-zinc-500 p-4"), class_name=class_name)

    max_val = max(v for _, v in data)
    max_val = max(max_val, 1e-6)

    bar_elements = []
    for label, val in data:
        pct = max(min((val / max_val) * 100, 100), 2)
        bar_elements.append(
            Div(
                Div(
                    Div(
                        style=f"height: {pct:.1f}%; background-color: {bar_color};",
                        class_name="w-full rounded-t-md transition-all duration-300 group-hover:brightness-125",
                    ),
                    class_name="w-full h-28 flex items-end justify-center group relative",
                ),
                Span(label, class_name="text-[10px] text-zinc-400 font-mono mt-2 truncate w-full text-center block"),
                class_name="flex-1 flex flex-col items-center min-w-0 px-1",
            )
        )

    return Div(
        Div(*bar_elements, class_name="flex items-end justify-between w-full h-full pt-4"),
        class_name=f"w-full bg-zinc-900/60 border border-zinc-800 p-4 rounded-xl {class_name}".strip(),
        **kwargs,
    )


# ── Dialogs & Modals ──────────────────────────────────────────────────────────

def Modal(
    title: str,
    *children: Any,
    is_open_bind: str = "isOpen",
    close_action: str | None = None,
    class_name: str = "",
    **kwargs: Any,
) -> Div:
    """Accessible dialog modal with backdrop blur and customizable action slot."""
    close_attr = {"@click": f"{is_open_bind} = false"}
    if close_action:
        close_attr["@click"] += f"; {close_action}"

    header = Div(
        H3(title, class_name="text-sm font-bold text-zinc-100 tracking-tight"),
        BaseButton("✕", **close_attr, class_name="text-zinc-400 hover:text-zinc-100 text-xs p-1 rounded-md transition"),
        class_name="flex items-center justify-between px-6 py-4 border-b border-zinc-800",
    )
    body = Div(*children, class_name="p-6 space-y-4")

    content = Div(
        header,
        body,
        **{"@click.stop": ""},
        class_name=f"bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden {class_name}".strip(),
    )

    return Div(
        content,
        **{
            "x-show": is_open_bind,
            "x-cloak": True,
            "@keydown.escape.window": f"{is_open_bind} = false",
        },
        class_name="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm",
        **kwargs,
    )


MetricCard = StatCard


# ── Lucide React Icons ────────────────────────────────────────────────────────

class LucideIcon(Component):
    """Declarative wrapper for Lucide React icon components.
    
    Usage:
        LucideIcon("Heart", size=20, class_name="text-rose-500")
        LucideIcon("ArrowRight", size=16)
    """
    library = "lucide-react"

    def __init__(self, name: str, *children: Any, **props: Any):
        super().__init__(*children, **props)
        self.tag = name


