from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from xania.example.counter import Counter
from xania.renderer.registry import ComponentRegistry
from xania.web.routes import router


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    # Static runtime (no inline JS).
    static_dir = Path(__file__).parent / "xania" / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Register example components.
    ComponentRegistry.register("Counter", Counter, id="counter")

    # File-system router (Next.js style App Router)
    from xania.routing import build_fastapi_router
    app_dir = Path(__file__).parent / "app"
    if app_dir.exists():
        build_fastapi_router(app, app_dir)

    # API routes.
    app.include_router(router)

    return app


app = create_app()

import shutil
import sys

import click
import uvicorn


def save_static(output_dir: Path = Path.cwd()) -> None:
    """Save minimal static website assets to `output_dir`.

    Copies `xania/renderer/index.html` (if present) to `output_dir/index.html`
    and copies the `xania/static/` folder to `output_dir/static/`.
    """
    project_root = Path(__file__).parent
    renderer_index = project_root / "xania" / "renderer" / "index.html"
    static_src = project_root / "xania" / "static"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if renderer_index.exists():
        shutil.copy(renderer_index, output_dir / "index.html")

    if static_src.exists():
        dest_static = output_dir / "static"
        if dest_static.exists():
            shutil.rmtree(dest_static)
        shutil.copytree(static_src, dest_static)

    click.echo(f"Saved static files to {output_dir}" )


@click.group(invoke_without_command=True, name="Xania")
@click.option("--host", "-H", default="127.0.0.1", show_default=True)
@click.option("--port", "-p", default=8000, show_default=True, type=int)
@click.option("--reload", is_flag=True, default=False)
@click.pass_context
def cli(ctx: click.Context, host: str, port: int, reload: bool) -> None:
    """Run the Xania server when invoked without a subcommand."""
    if ctx.invoked_subcommand is None:
        click.echo(f"Starting Xania server on {host}:{port} (reload={reload})")
        uvicorn.run("app:app", host=host, port=port, reload=reload)


@cli.command(name="build")
@click.option("--out", "-o", default=".", type=click.Path(), show_default=True)
def build(out: str) -> None:
    """Generate static files in the current working directory (or `--out`)."""
    save_static(Path(out))


@cli.command(name="help")
def xania_help() -> None:
    """Show a step-by-step tutorial on using this framework to create a website."""
    tutorial = (
        "Xania Framework — Quick Start:\n"
        "\n"
        "1) Create your components under `components/` or `xania/renderer/`.\n"
        "2) Add routes in `xania/web/routes.py` to serve APIs or data.\n"
        "3) Run the development server: `python app.py Xania`\n"
        "   - Options: `--host`, `--port`, `--reload`.\n"
        "4) When ready to produce a static site, run: `python app.py Xania build`\n"
        "   - This copies `xania/renderer/index.html` and `xania/static/` into the current directory.\n"
        "5) Serve the generated `index.html` from any static host or open locally.\n"
        "\n"
        "Examples:\n"
        "  python app.py Xania --port 9000\n"
        "  python app.py Xania build --out ./dist\n"
    )
    click.echo(tutorial)


if __name__ == "__main__":
    cli()
