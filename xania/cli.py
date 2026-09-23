from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
import shutil
import sys
from typing import Optional

import click


@dataclass(frozen=True)
class CliConfig:
    default_app: str = "xania.web.app:app"


def _run_uvicorn(app: str, host: str, port: int, reload: bool) -> None:
    try:
        import uvicorn

        uvicorn.run(app, host=host, port=int(port), reload=reload)
    except Exception as e:  # pragma: no cover
        raise click.ClickException(f"Failed to start server: {e}") from e





@click.group(invoke_without_command=True)
@click.option("--app", "app_path", default=None, help="ASGI app path, e.g. module:app")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.pass_context
def cli(ctx: click.Context, app_path: Optional[str], host: str, port: int) -> None:
    """Xania CLI — Python UI framework for building SPAs."""
    if ctx.invoked_subcommand is not None:
        return
    cfg = CliConfig()
    _run_uvicorn(app_path or cfg.default_app, host=host, port=port, reload=False)


@cli.command("init")
@click.argument("project_name", default="my_spa")
def init(project_name: str) -> None:
    """Create a new Xania SPA project.
    
    Example:
        xania init my_website
    """
    if project_name == ".":
        project_path = Path.cwd()
    else:
        project_path = Path.cwd() / project_name
        if project_path.exists():
            raise click.ClickException(f"Directory {project_name} already exists")
        project_path.mkdir(parents=True, exist_ok=True)
    
    # Create main app file
    app_py = project_path / "app.py"
    app_py.write_text('''"""
My Xania Website

Development server with hot reload:
    xania dev
"""

from pathlib import Path
from importlib.resources import as_file, files
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from xania.routing.builder import build_fastapi_router
from xania.web.routes import router as xania_router

# 1. Create FastAPI application
app = FastAPI(title="My Xania App")

# 2. Mount Xania's static runtime assets dynamically
xania_static = files("xania").joinpath("static")
with as_file(xania_static) as static_path:
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 3. Mount the App Router from the `app` directory
app_dir = Path(__file__).parent / "app"
if app_dir.exists():
    build_fastapi_router(app, app_dir)

# 4. Include Xania's internal routes
app.include_router(xania_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
''', encoding="utf-8")
    
    # Create the app directory and components
    app_dir = project_path / "app"
    app_dir.mkdir(exist_ok=True)
    
    layout_py = app_dir / "layout.py"
    layout_py.write_text('''
from xania.renderer.elements import Div, Nav, A, component

@component
def Layout(children):
    return Div(
        Nav(
            A("Home", href="/", class_name="font-bold text-xl mr-4"),
            A("About", href="/about", class_name="text-gray-400 hover:text-white"),
            class_name="p-4 bg-gray-900 text-white flex items-center"
        ),
        Div(
            children,
            class_name="p-8 max-w-4xl mx-auto"
        ),
        class_name="min-h-screen bg-gray-50 font-sans"
    )
''', encoding="utf-8")

    page_py = app_dir / "page.py"
    page_py.write_text('''
from typing import Any
from xania.renderer.component import Component
from xania.renderer.state import State
from xania.renderer.elements import Div, H1, P, Button

def metadata(**kwargs):
    return {
        "title": "Welcome to Xania",
        "description": "A minimal Python SPA framework"
    }

class Page(Component):
    def initial_state(self) -> dict[str, Any]:
        return {"clicks": 0}

    def on_click(self, state: State, payload: dict[str, Any]) -> None:
        state.clicks += 1

    def render(self, state: State):
        return Div(
            H1("Welcome to Xania App Router", class_name="text-4xl font-black mb-4 text-blue-600"),
            P("Edit this page in app/page.py", class_name="text-gray-600 mb-8"),
            
            Div(
                Button(
                    f"Clicked {state.clicks} times", 
                    class_name="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold shadow hover:bg-blue-700 transition-colors cursor-pointer",
                    onclick="App.dispatch(this, 'click')"
                ),
                class_name="p-6 bg-white rounded-xl shadow-sm border"
            )
        )
''', encoding="utf-8")
    
    # Create README
    readme = project_path / "README.md"
    readme.write_text(f"""# {project_name.title()}

A modern Xania website powered by the App Router.

## Quick Start

**Start the development server with hot reload:**
```bash
xania dev
```
*(Or use `uv run xania dev` if running inside a uv project)*

Then open: `http://127.0.0.1:8000`

Edit `app.py` or the files in the `app/` folder and save - the server will hot-reload automatically!

## Routing
Xania uses file-system based routing.
- `app/layout.py` is the main wrapper for your site (navbar, sidebar).
- `app/page.py` is the index page (`/`).
- Create `app/dashboard/page.py` to add a `/dashboard` route.

## Deploying
Xania applications are standard FastAPI Python servers.
Deploy them to any platform that runs Python (Render, Railway, Heroku, Docker) using standard uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

## Learn More
Visit: https://github.com/xania/framework
""", encoding="utf-8")
    
    click.echo(f"✅ Created project: {project_name}/")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"  cd {project_name}")
    click.echo("  xania dev              # Start with hot reload")


@cli.command("dev")
@click.option("--app", "app_path", default=None, help="ASGI app path, e.g. module:app")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload/--no-reload", default=True, show_default=True)
def dev(app_path: Optional[str], host: str, port: int, reload: bool) -> None:
    """Run a development server (uvicorn --reload by default)."""
    cfg = CliConfig()
    
    # If no app specified, try to use local app.py in current directory
    if app_path is None:
        cwd = Path.cwd()
        local_app = cwd / "app.py"
        if local_app.exists():
            app_path = "app:app"
            # Set PYTHONPATH for the subprocess
            env = os.environ.copy()
            env["PYTHONPATH"] = str(cwd) + os.pathsep + env.get("PYTHONPATH", "")
            
            # Run uvicorn as a subprocess with the updated environment
            cmd = [
                sys.executable, "-m", "uvicorn",
                app_path,
                "--host", host,
                "--port", str(port),
            ]
            if reload:
                cmd.append("--reload")
            
            subprocess.run(cmd, env=env)
            return
        else:
            app_path = cfg.default_app
    
    _run_uvicorn(app_path, host=host, port=port, reload=reload)





@cli.command("help")
def help_cmd() -> None:
    """Print a quick-start guide."""
    click.echo(
        "\n".join(
            [
                "╔════════════════════════════════════════╗",
                "║  Xania — Python UI Framework           ║",
                "╚════════════════════════════════════════╝",
                "",
                "📦 Creating a new website:",
                "  xania init my_website",
                "  cd my_website",
                "  xania dev                  # Start local server",
                "",
                "🛠️  Development Server:",
                "  xania dev                           # Hot-reload enabled",
                "  xania dev --app yourproj.web:app    # Custom app",
                "",
                "💡 Workflow:",
                "  1. Initialize: xania init my_site",
                "  2. Start server: xania dev",
                "  3. Edit app/page.py",
                "  4. Watch it instantly hot-reload in the browser",
                "",
                "🚀 Deployment:",
                "  Deploy as a standard Python server via uvicorn:",
                "  uvicorn app:app --host 0.0.0.0 --port $PORT",
                "",
                "📚 Documentation:",
                "  Visit: https://github.com/xania/framework",
            ]
        )
    )


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    cli.main(args=argv, prog_name="xania")


__all__ = ["cli", "main"]

