from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from xania.components.component import Component
from xania.compiler.templates import RenderUtils


class PageDef:
    """Represents a compiled SPA route page."""

    def __init__(self, route: str, component: Union[Component, Callable[[], Component]], title: str = "Xania App"):
        self.route = route
        self.component_fn = component
        self.title = title

    @property
    def component(self) -> Component:
        if callable(self.component_fn):
            return self.component_fn()
        return self.component_fn

    @property
    def file_stem(self) -> str:
        clean = self.route.strip("/").replace("/", "_").replace("-", "_")
        return f"page_{clean}" if clean else "page_index"


class SpaCompiler:
    """Compiles Xania Python apps into production-ready Vite + React SPA trees."""

    def __init__(self, pages: Optional[List[PageDef]] = None):
        self.pages: List[PageDef] = pages or []
        self.libraries: Dict[str, str] = {
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "react-router-dom": "^6.26.0",
            "clsx": "^2.1.1",
            "tailwind-merge": "^2.5.2",
            "lucide-react": "^0.439.0",
        }

    def add_page(self, route: str, component: Union[Component, Callable[[], Component]], title: str = "Xania App") -> None:
        self.pages.append(PageDef(route=route, component=component, title=title))

    def _generate_page_jsx(self, page: PageDef) -> str:
        comp = page.component
        imports_map = comp._get_all_imports()

        import_lines = [
            'import React from "react";',
            'import { useXaniaState } from "../context";',
        ]

        for lib, tags in sorted(imports_map.items()):
            if lib == "react":
                continue
            default_import = None
            named_imports = []
            for item in sorted(tags, key=lambda x: x[0] if isinstance(x, tuple) else x):
                if isinstance(item, tuple):
                    tag_name, is_def, alias_name = item
                    if is_def:
                        default_import = alias_name or tag_name
                    else:
                        named_imports.append(f"{tag_name} as {alias_name}" if alias_name else tag_name)
                else:
                    named_imports.append(item)

            chunks = []
            if default_import:
                chunks.append(default_import)
            if named_imports:
                chunks.append(f"{{ {', '.join(sorted(list(set(named_imports))))} }}")
            if chunks:
                import_lines.append(f'import {", ".join(chunks)} from "{lib}";')

        jsx_body = RenderUtils.render(comp, depth=2)

        return f"""{chr(10).join(import_lines)}

export default function {page.file_stem.capitalize()}() {{
  const {{ state, sendEvent }} = useXaniaState();

  return (
    {jsx_body}
  );
}}
"""

    def _generate_routes_jsx(self) -> str:
        import_lines = [
            'import React from "react";',
            'import { createBrowserRouter } from "react-router-dom";',
        ]
        route_entries = []

        for page in self.pages:
            var_name = page.file_stem.capitalize()
            import_lines.append(f'import {var_name} from "./pages/{page.file_stem}";')
            route_entries.append(f'  {{ path: "{page.route}", element: <{var_name} /> }},')

        return f"""{chr(10).join(import_lines)}

export const router = createBrowserRouter([
{chr(10).join(route_entries)}
]);
"""

    def _generate_package_json(self, target_dir: Path) -> dict[str, Any]:
        # Collect third party libs across all pages
        for page in self.pages:
            imports_map = page.component._get_all_imports()
            for lib in imports_map:
                if lib and lib != "react" and not lib.startswith("."):
                    # Check if version is specified e.g. "package@^1.0.0"
                    if "@" in lib and not lib.startswith("@"):
                        pkg_name, version = lib.split("@", 1)
                        self.libraries[pkg_name] = f"^{version}"
                    elif lib.startswith("@") and "@" in lib[1:]:
                        idx = lib.find("@", 1)
                        pkg_name = lib[:idx]
                        version = lib[idx+1:]
                        self.libraries[pkg_name] = f"^{version}"
                    elif lib not in self.libraries:
                        self.libraries[lib] = "latest"

        return {
            "name": "xania-spa-app",
            "private": True,
            "version": "4.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": self.libraries,
            "devDependencies": {
                "@vitejs/plugin-react": "^4.3.1",
                "vite": "^5.4.2",
                "tailwindcss": "^3.4.10",
                "autoprefixer": "^10.4.20",
                "postcss": "^8.4.41"
            }
        }

    def compile(self, output_dir: Union[str, Path]) -> Path:
        out = Path(output_dir)
        src_dir = out / "src"
        pages_dir = src_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        # Write pages
        for page in self.pages:
            page_path = pages_dir / f"{page.file_stem}.jsx"
            page_path.write_text(self._generate_page_jsx(page))

        # Write routes
        routes_path = src_dir / "routes.jsx"
        routes_path.write_text(self._generate_routes_jsx())

        # Update package.json
        pkg_json_path = out / "package.json"
        pkg_data = self._generate_package_json(out)
        pkg_json_path.write_text(json.dumps(pkg_data, indent=2))

        return out
