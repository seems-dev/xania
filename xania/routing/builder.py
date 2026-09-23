from __future__ import annotations

import inspect
import uuid
from typing import Any, Callable, List, get_type_hints
from pathlib import Path
from fastapi import FastAPI, Request, Response, HTTPException
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

    def _coerce_params(self, func: Callable, raw_params: dict[str, str]) -> dict[str, Any]:
        if type(func) is type:
            # If it's a class, inspect its __init__
            hints = get_type_hints(func.__init__)
        else:
            hints = get_type_hints(func)
            
        coerced = {}
        for name, value in raw_params.items():
            target_type = hints.get(name, str)
            try:
                coerced[name] = target_type(value)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value for '{name}': expected {target_type.__name__}, got '{value}'"
                )
        return coerced

    async def handle(self, action: str, payload: dict[str, Any]) -> None:
        if self._page_instance:
            await self._page_instance.handle(action, payload)  # type: ignore
        else:
            await super().handle(action, payload)  # type: ignore

    def render(self, state, start_layout_index: int = 0):
        # 1. Render the Page
        page_fn = getattr(self.page_module, "Page", None)
        if not page_fn:
            raise ValueError("page.py must export a 'Page' function or component")
        
        # Coerce path parameters based on type hints
        coerced_params = self._coerce_params(page_fn, self.path_params)
        
        if type(page_fn) is type and issubclass(page_fn, Component):
            if not self._page_instance:
                # Merge coerced params into initial state
                self._page_instance = page_fn(id=self.id + "_page")
                self._page_instance.state.update(coerced_params)
            content = self._page_instance.render(self._page_instance.state)
        else:
            content = page_fn(**coerced_params) if callable(page_fn) else page_fn

        # 2. Wrap inside Layouts (from innermost to outermost)
        for layout_mod in reversed(self.layout_modules[start_layout_index:]):
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
        # 3. Create or reuse state / instance for this request
        session_id = request.cookies.get("xania_session_id")

        # Check for ISR Cache
        page_fn = getattr(page_module, "Page", None)
        is_isr = getattr(page_fn, "_isr_revalidate", None)
        isr_key = f"isr:{route_path}"
        
        if is_isr is not None:
            from xania.runtime.isr import ISRCache
            cached_html = ISRCache.get(isr_key, is_isr)
            if cached_html:
                html_content = cached_html
                page_title = "Cached Page" # For ISR, we might need to cache metadata too, but simplified for now
                if request.headers.get("x-xania-spa") == "true":
                    return JSONResponse({
                        "html": html_content,
                        "title": page_title,
                        "component": "ISR",
                        "slot": "children",
                        "unmount_components": []
                    })
                
                # Full page cache hit
                final_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{page_title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>window.XaniaConfig = {{ serverEvents: false }};</script>
  </head>
  <body class="bg-gray-950 text-white min-h-screen font-sans">
    <div id="app_root" data-component="ISR">
        {html_content}
    </div>
    <script src="/static/runtime.js?v=6"></script>
  </body>
</html>"""
                return HTMLResponse(final_html)

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
            current_comp_name = request.headers.get("x-xania-current-component")
            start_layout_index = 0
            
            if current_comp_name:
                old_wrapper = ComponentRegistry.all_templates().get(current_comp_name)
                if old_wrapper:
                    _, old_kwargs = old_wrapper
                    old_layouts = old_kwargs.get("layout_modules", [])
                    # Find common prefix
                    for i in range(min(len(layout_modules), len(old_layouts))):
                        if layout_modules[i] == old_layouts[i]:
                            start_layout_index += 1
                        else:
                            break
                            
            # Find components to unmount
            unmount_components = []
            if session_id in ComponentRegistry._active_components:
                active_comps = ComponentRegistry._active_components[session_id]
                # If they are navigating away, we unmount the old component.
                if current_comp_name and current_comp_name in active_comps and current_comp_name != component_name:
                    unmount_components.append(current_comp_name)
                    # Trigger unmount immediately (lifecycle hooks will be properly wired in Phase 2)
                    old_comp_instance = ComponentRegistry.get(current_comp_name, session_id)
                    if hasattr(old_comp_instance, "unmount"):
                        old_comp_instance.unmount()
                    ComponentRegistry.remove(current_comp_name, session_id)

            # Render only the changed segment
            partial_html = wrapper.render(wrapper.state, start_layout_index=start_layout_index)  # type: ignore[call-arg]
            if isinstance(partial_html, Component) or hasattr(partial_html, "to_html"):
                # Wait, render returns Element. We need html.
                # Actually wrapper.render() returns Element, but we need HTML string
                # Let's use the `render` function from xania.renderer.render
                pass
            
            from xania.renderer.render import render as render_vdom
            html_content = render_vdom(partial_html)
            
            # Save to ISR Cache if applicable
            if is_isr is not None:
                ISRCache.set(isr_key, html_content)

            resp = JSONResponse({
                "html": html_content,
                "title": page_title,
                "component": component_name,
                "slot": "children",
                "unmount_components": unmount_components
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
        if is_isr is not None:
            # We want to disable serverEvents for ISR and save the shell
            # But html_shell hardcodes serverEvents: true
            shell = shell.replace("serverEvents: true", "serverEvents: false")
            html_content_for_cache = wrapper.to_html()
            ISRCache.set(isr_key, html_content_for_cache)
            
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
