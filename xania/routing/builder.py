from __future__ import annotations

import uuid
from typing import Any, Callable, List
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from xania.routing.app_router import RouteNode, scan_directory
from xania.renderer.component import Component
from xania.renderer.registry import ComponentRegistry
from xania.engine.runtime import html_shell
from xania.renderer.render import render


class LayoutWrapper(Component):
    """A virtual component that wraps a page inside multiple layouts."""
    def __init__(self, id: str, page_module: Any, layout_modules: List[Any], path_params: dict):
        super().__init__(id=id)
        self.page_module = page_module
        self.layout_modules = layout_modules
        self.path_params = path_params
        self._page_instance = None

    def handle(self, action: str, payload: dict[str, Any]) -> None:
        if self._page_instance:
            self._page_instance.handle(action, payload)
        else:
            super().handle(action, payload)

    def render(self, state):
        # 1. Render the Page
        page_fn = getattr(self.page_module, "Page", None)
        if not page_fn:
            raise ValueError("page.py must export a 'Page' function or component")
        
        # Pass path parameters as context or props to Page if it accepts them
        # (For now, we just pass them if it's a Component, or pass as kwargs if function)
        if type(page_fn) is type and issubclass(page_fn, Component):
            if not self._page_instance:
                self._page_instance = page_fn(id=self.id + "_page")
            # State merging logic if path_params exist
            # But currently we just render
            content = self._page_instance.render(self._page_instance.state)
        else:
            content = page_fn(**self.path_params) if callable(page_fn) else page_fn

        # 2. Wrap inside Layouts (from innermost to outermost)
        for layout_mod in reversed(self.layout_modules):
            layout_fn = getattr(layout_mod, "Layout", None)
            if layout_fn:
                # layout_fn must accept *children or children list
                content = layout_fn(content)

        return content


def build_fastapi_router(app: FastAPI, app_dir: Path):
    root_node = scan_directory(app_dir)
    
    def _mount_nodes(node: RouteNode, current_path: str, layout_stack: List[Any]):
        # Push this node's layout to the stack if it exists
        current_layouts = list(layout_stack)
        if node.layout_module:
            current_layouts.append(node.layout_module)
            
        # If there is a page, build the route endpoint
        if node.page_module:
            route_path = current_path if current_path else "/"
            
            # We need to capture the current state of layout_stack and page_module
            _register_endpoint(app, route_path, node.page_module, current_layouts)
            
        # Recurse for children
        for child_name, child_node in node.children.items():
            child_path = f"{current_path}/{child_node.fastapi_path}"
            _mount_nodes(child_node, child_path, current_layouts)

    _mount_nodes(root_node, "", [])


def _register_endpoint(app: FastAPI, route_path: str, page_module: Any, layout_modules: List[Any]):
    
    @app.get(route_path, response_class=HTMLResponse)
    def _route_handler(request: Request, response: Response):
        path_params = request.path_params
        # 1. Get or create session ID
        session_id = request.cookies.get("xania_session_id")
        if not session_id:
            session_id = uuid.uuid4().hex
            response.set_cookie(
                "xania_session_id",
                session_id,
                httponly=True,
                samesite="lax"
            )
            
        # 2. Generate a unique component ID for this specific route instance
        # So that the client can dispatch events to it
        component_name = f"Route_{route_path.replace('/', '_').replace('{', '').replace('}', '')}"
        
        # Ensure the wrapper class is registered as a template
        # So that /event can reconstruct it
        ComponentRegistry.register(
            component_name, 
            LayoutWrapper, 
            id=component_name,
            page_module=page_module, 
            layout_modules=layout_modules,
            path_params=path_params
        )
        
        # 3. Instantiate the component for this session
        wrapper = ComponentRegistry.get(component_name, session_id)
        wrapper.id = "app_root" # Mount it at the root ID
        
        # 4. Extract metadata
        merged_metadata = {}
        for layout_mod in layout_modules:
            meta_fn = getattr(layout_mod, "metadata", None)
            if callable(meta_fn):
                merged_metadata.update(meta_fn(**path_params))
        
        meta_fn = getattr(page_module, "metadata", None)
        if callable(meta_fn):
            merged_metadata.update(meta_fn(**path_params))

        # 5. Generate the HTML response
        html_content = wrapper.to_html()
        page_title = merged_metadata.get("title", "Xania App")
        
        session_cookie = request.cookies.get("xania_session_id")
        
        # If this is an SPA navigation request, return just the HTML and metadata
        if request.headers.get("x-xania-spa") == "true":
            resp = JSONResponse({
                "html": html_content,
                "title": page_title,
                "component": component_name
            })
            if not session_cookie:
                resp.set_cookie(
                    "xania_session_id",
                    session_id,
                    httponly=True,
                    samesite="lax"
                )
            return resp

        # Otherwise, generate the full HTML shell for a hard page load
        shell = html_shell([(component_name, wrapper)], metadata=merged_metadata)
        html_resp = HTMLResponse(shell)
        
        # We must set the cookie on the explicit HTMLResponse we are returning
        if not session_cookie:
            html_resp.set_cookie(
                "xania_session_id",
                session_id,
                httponly=True,
                samesite="lax"
            )
        return html_resp

__all__ = ["build_fastapi_router"]
