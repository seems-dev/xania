from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

import click

from xania.compiler.compiler import PageDef, SpaCompiler
from xania.components.component import Component
from xania.state.state import BaseState


@dataclass(frozen=True)
class CliConfig:
    default_app: str = "xania.web.app:app"


def _scaffold_web_dir(target_dir: Path) -> None:
    """Ensure .xania/web directory exists and is populated from the template."""
    template_dir = Path(__file__).parent / "template"
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)

    # Copy template files if not present
    for item in template_dir.glob("**/*"):
        if item.is_file():
            rel_path = item.relative_to(template_dir)
            dest_file = target_dir / rel_path
            if not dest_file.exists():
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)


def _discover_pages_and_states(app_dir: Path) -> tuple[List[PageDef], Optional[type[BaseState]]]:
    """Scan app directory for page.py files and BaseState definitions."""
    pages: List[PageDef] = []
    found_state_cls: Optional[type[BaseState]] = None

    # Check root app/page.py
    if not app_dir.exists():
        return pages, found_state_cls

    sys_path_added = False
    parent_str = str(app_dir.parent.resolve())
    if parent_str not in sys.path:
        sys.path.insert(0, parent_str)
        sys_path_added = True

    try:
        for py_file in sorted(app_dir.glob("**/page.py")):
            rel = py_file.parent.relative_to(app_dir)
            route = "/" if str(rel) == "." else f"/{rel.as_posix()}"

            # Import module dynamically
            mod_name = f"xania_app_{py_file.stem}_{int(py_file.stat().st_mtime)}"
            spec = importlib.util.spec_from_file_location(mod_name, py_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                # Look for BaseState subclass
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseState) and attr is not BaseState:
                        found_state_cls = attr

                # Look for Component class or function
                page_comp = None
                if hasattr(mod, "Page") and (isinstance(mod.Page, type) or callable(mod.Page)):
                    page_comp = mod.Page() if isinstance(mod.Page, type) else mod.Page
                elif hasattr(mod, "index") and callable(mod.index):
                    page_comp = mod.index()
                elif hasattr(mod, "page") and callable(mod.page):
                    page_comp = mod.page()

                if page_comp:
                    pages.append(PageDef(route=route, component=page_comp))
    finally:
        if sys_path_added:
            try:
                sys.path.remove(parent_str)
            except ValueError:
                pass

    return pages, found_state_cls


def _compile_project(project_root: Path) -> Path:
    """Compile Python pages into .xania/web Vite SPA."""
    web_dir = project_root / ".xania" / "web"
    _scaffold_web_dir(web_dir)

    app_dir = project_root / "app"
    pages, state_cls = _discover_pages_and_states(app_dir)

    if not pages:
        # Fallback default welcome page
        from xania.components.component import Button, Div, H1, P
        from xania.ui.components import Badge, Card

        def default_page():
            return Div(
                Card(
                    H1("Welcome to Xania 4.0 SPA", class_name="text-3xl font-extrabold text-zinc-100"),
                    P("Edit app/page.py to build your high-performance full-stack web application.", class_name="text-zinc-400 mt-2"),
                    Badge("0ms Reactivity", variant="success", class_name="mt-4"),
                    class_name="max-w-md mx-auto mt-20 text-center"
                ),
                class_name="min-h-screen bg-zinc-950 flex items-center justify-center p-6"
            )

        pages.append(PageDef(route="/", component=default_page))

    compiler = SpaCompiler(pages=pages)
    compiler.compile(web_dir)
    return web_dir


@click.group(invoke_without_command=True)
@click.option("--app", "app_path", default=None, help="ASGI app path, e.g. module:app")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.pass_context
def cli(ctx: click.Context, app_path: Optional[str], host: str, port: int) -> None:
    """Xania CLI — Full-Stack Python SPA Framework."""
    if ctx.invoked_subcommand is not None:
        return
    cfg = CliConfig()
    try:
        import uvicorn
        uvicorn.run(app_path or cfg.default_app, host=host, port=port, reload=False)
    except Exception as e:
        raise click.ClickException(f"Failed to start server: {e}") from e


@cli.command("init")
@click.argument("project_name", default="my_spa")
def init(project_name: str) -> None:
    """Create a new Xania 4.0 Full-Stack SPA project.
    
    Example:
        xania init my_app
    """
    project_path = Path.cwd() if project_name == "." else Path.cwd() / project_name
    if project_name != "." and project_path.exists():
        raise click.ClickException(f"Directory {project_name} already exists")
    project_path.mkdir(parents=True, exist_ok=True)

    app_dir = project_path / "app"
    app_dir.mkdir(exist_ok=True)

    # Create app/page.py
    page_py = app_dir / "page.py"
    page_py.write_text('''from xania import BaseState, Component, Div, H1, P, Button, Card, Badge, LucideIcon

class State(BaseState):
    count: int = 0

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

def Page():
    return Div(
        Card(
            Div(
                LucideIcon("Sparkles", class_name="w-8 h-8 text-pink-500 mb-2"),
                H1("Xania 4.0 True SPA", class_name="text-3xl font-extrabold text-zinc-100"),
                P("Full-stack Python web framework with instant 0ms client reactivity.", class_name="text-zinc-400 mt-2"),
                class_name="flex flex-col items-center"
            ),
            Div(
                Badge("FastAPI WebSocket", variant="purple", class_name="mr-2"),
                Badge("Vite + React HMR", variant="success"),
                class_name="flex justify-center mt-4"
            ),
            Div(
                H1(State.count, class_name="text-6xl font-black text-pink-500 my-6"),
                Div(
                    Button("- Decrement", on_click=State.decrement, variant="secondary", class_name="mr-3"),
                    Button("+ Increment", on_click=State.increment, variant="primary"),
                    class_name="flex justify-center"
                ),
                class_name="text-center"
            ),
            class_name="max-w-md w-full p-8 bg-zinc-900 border border-zinc-800 rounded-3xl shadow-2xl"
        ),
        class_name="min-h-screen bg-zinc-950 flex items-center justify-center p-4"
    )
''', encoding="utf-8")

    # Create root app.py for backend server
    app_py = project_path / "app.py"
    app_py.write_text('''from pathlib import Path
from xania.server import create_app
from app.page import State

# Create FastAPI WebSocket backend
dist_dir = Path(__file__).parent / ".xania" / "web" / "dist"
app = create_app(state_cls=State, dist_dir=dist_dir if dist_dir.exists() else None)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
''', encoding="utf-8")

    click.echo(f"🎉 Created Xania 4.0 SPA project: {project_name}/")
    click.echo("")
    click.echo("Next steps:")
    if project_name != ".":
        click.echo(f"  cd {project_name}")
    click.echo("  xania dev              # Start Vite SPA + FastAPI backend with instant HMR")


@cli.command("compile")
def compile_cmd() -> None:
    """Compile Python pages into .xania/web React JSX modules."""
    click.echo("Compiling Xania Python components to React SPA...")
    out = _compile_project(Path.cwd())
    click.echo(f"✅ Successfully compiled into: {out}")


@cli.command("dev")
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--frontend-port", default=3000, show_default=True, type=int)
def dev(host: str, port: int, frontend_port: int) -> None:
    """Start Vite SPA dev server + FastAPI WebSocket backend with instant HMR."""
    cwd = Path.cwd()
    click.echo("⚡ Initializing Xania 4.0 SPA Development Environment...")

    # 1. Compile initial pages
    web_dir = _compile_project(cwd)

    # 2. Check if npm install needed in .xania/web
    node_modules = web_dir / "node_modules"
    if not node_modules.exists():
        click.echo("📦 Installing frontend dependencies (Vite, React, Tailwind, Lucide)...")
        subprocess.run(["npm", "install", "--prefer-offline", "--no-audit", "--no-fund"], cwd=str(web_dir), check=False)

    # 3. Launch FastAPI backend
    if (cwd / "server.py").exists():
        app_path = "server:app"
    elif (cwd / "app.py").exists():
        app_path = "app:app"
    else:
        app_path = "xania.web.app:app"
    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = str(cwd) + os.pathsep + backend_env.get("PYTHONPATH", "")

    click.echo(f"🚀 Starting FastAPI backend on http://{host}:{port} ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", app_path, "--host", host, "--port", str(port), "--reload"],
        cwd=str(cwd),
        env=backend_env,
    )

    # 4. Launch Vite frontend
    click.echo(f"✨ Starting Vite SPA dev server on http://localhost:{frontend_port} ...")
    vite_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(frontend_port), "--host"],
        cwd=str(web_dir),
    )

    try:
        # File watcher for auto-recompiling Python pages to trigger Vite HMR
        last_mtime = 0.0
        app_dir = cwd / "app"
        while True:
            time.sleep(0.5)
            # Check backend & vite health
            if backend_proc.poll() is not None or vite_proc.poll() is not None:
                break

            if app_dir.exists():
                current_max = max((p.stat().st_mtime for p in app_dir.glob("**/*.py")), default=0.0)
                if current_max > last_mtime:
                    if last_mtime > 0:
                        click.echo("🔄 Python components modified, updating React SPA...")
                        _compile_project(cwd)
                    last_mtime = current_max

    except KeyboardInterrupt:
        click.echo("\nStopping Xania dev servers...")
    finally:
        backend_proc.terminate()
        vite_proc.terminate()


@cli.command("build")
def build() -> None:
    """Build production SPA static assets into .xania/web/dist."""
    cwd = Path.cwd()
    click.echo("🏗️ Compiling Xania SPA for production...")
    web_dir = _compile_project(cwd)

    node_modules = web_dir / "node_modules"
    if not node_modules.exists():
        click.echo("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install", "--prefer-offline", "--no-audit", "--no-fund"], cwd=str(web_dir), check=True)

    click.echo("⚡ Running Vite build...")
    res = subprocess.run(["npm", "run", "build"], cwd=str(web_dir))
    if res.returncode == 0:
        dist_dir = web_dir / "dist"
        click.echo(f"✅ Production build successful! Output: {dist_dir}")
    else:
        raise click.ClickException("Vite build failed.")


@cli.command("export")
def export_cmd() -> None:
    """Alias for build: export production SPA static assets into .xania/web/dist."""
    build()


def main(argv: list[str] | None = None) -> None:
    cli.main(args=argv, prog_name="xania")


__all__ = ["cli", "main"]
