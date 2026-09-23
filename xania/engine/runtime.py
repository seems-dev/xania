from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from xania.renderer.component import Component


@dataclass(frozen=True)
class RuntimeConfig:
    title: str = "App"
    tailwind: bool = True


def html_shell(components: Iterable[tuple[str, Component]], config: RuntimeConfig | None = None, metadata: dict[str, str] | None = None) -> str:
    """
    Return a full HTML document with component mount points.

    - No inline JS.
    - The runtime is served from `/static/runtime.js`.
    - Each mount point is a single div with stable id + data-component name.
    """
    cfg = config or RuntimeConfig()
    meta = metadata or {}

    title = meta.get("title", cfg.title)
    desc = meta.get("description", "")
    og_img = meta.get("og:image", "")

    meta_tags = ""
    if desc:
        meta_tags += f'    <meta name="description" content="{desc}" />\n'
    if og_img:
        meta_tags += f'    <meta property="og:image" content="{og_img}" />\n'

    mounts = "\n".join(
        f'    <div id="{c.id}" data-component="{name}">{c.to_html()}</div>' for name, c in components
    )

    tw = (
        '    <script src="https://cdn.tailwindcss.com"></script>\n'
        if cfg.tailwind
        else ""
    )

    from xania.web.config import get_settings
    is_dev = str(get_settings().is_dev).lower()

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
{meta_tags}{tw}  </head>
  <body>
{mounts}
    <script>window.XaniaConfig={{serverEvents:true, dev:{is_dev}}};</script>
    <!-- Alpine.js for client-side interactivity -->
    <script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/intersect@3.x.x/dist/cdn.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="/static/runtime.js?v=6"></script>
  </body>
</html>"""


__all__ = ["RuntimeConfig", "html_shell"]
