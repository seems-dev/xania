from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from xania.renderer.registry import ComponentRegistry
from xania.web.auth import AuthManager, Session, get_auth_manager, require_csrf, require_role, require_session
from xania.web.ratelimit import limiter
from xania.web.schemas import EventRequest, EventResponse, Update
from fastapi import WebSocket, WebSocketDisconnect
import json
from xania.web.config import get_settings


router = APIRouter()

MOUNT_ACTION = "__mount__"


async def _call_lifecycle(method):
    """Call a lifecycle method, supporting both sync and async."""
    if asyncio.iscoroutinefunction(method):
        await method()
    else:
        # Run sync methods in a thread pool to avoid blocking the event loop
        await asyncio.get_event_loop().run_in_executor(None, method)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, response: Response) -> str:
    import uuid
    session_id = request.cookies.get("xania_session_id")
    if not session_id:
        session_id = uuid.uuid4().hex
        response.set_cookie(
            "xania_session_id",
            session_id,
            httponly=True,
            samesite="lax"
        )
    return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Welcome to Xania</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap');
      body { font-family: 'Inter', sans-serif; }
    </style>
  </head>
  <body class="bg-black text-white min-h-screen flex flex-col items-center justify-center selection:bg-purple-500/30 overflow-hidden relative">
    <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-black to-black -z-10"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none -z-10"></div>
    
    <main class="max-w-3xl w-full px-6 flex flex-col items-center text-center z-10">
      <div class="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-md mb-8 shadow-2xl">
        <span class="flex h-2 w-2 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
        </span>
        <span class="text-sm font-medium text-slate-300">Xania is running</span>
      </div>

      <h1 class="text-5xl md:text-7xl font-black tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-br from-white via-white to-white/40 drop-shadow-sm">
        Build at the speed of thought.
      </h1>
      
      <p class="text-lg md:text-xl text-slate-400 mb-12 max-w-2xl leading-relaxed">
        You are looking at the default Xania welcome page. Get started by creating your first component.
      </p>

      <div class="relative group cursor-text">
        <div class="absolute -inset-1 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
        <div class="relative bg-black/50 border border-white/10 backdrop-blur-xl rounded-xl p-6 shadow-2xl flex items-center gap-4">
          <span class="text-slate-500 font-mono text-sm uppercase tracking-widest font-bold select-none">File</span>
          <code class="font-mono text-purple-300 text-lg">app/page.py</code>
        </div>
      </div>
    </main>
  </body>
</html>"""


@router.get("/api/ping")
def ping() -> dict[str, str]:
    return {"ok": "true"}


@router.post("/api/auth/login")
def login(
    payload: dict[str, str],
    request: Request,
    response: Response,
    auth: AuthManager = Depends(get_auth_manager),
) -> JSONResponse:
    ip = (request.client.host if request.client else "unknown") or "unknown"
    if not limiter.allow(f"login:{ip}", capacity=10, refill_per_sec=10 / 60.0):
        raise HTTPException(status_code=429, detail="Too many login attempts, slow down")

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    user = auth.authenticate(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    sess = auth.new_session(username=username)
    auth.set_session_cookie(response, sess)
    return JSONResponse({"ok": True, "user": user, "csrf": sess.csrf})


@router.post("/api/auth/logout")
def logout(response: Response, auth: AuthManager = Depends(get_auth_manager)) -> JSONResponse:
    auth.clear_session_cookie(response)
    return JSONResponse({"ok": True})


@router.get("/api/auth/me")
def me(sess: Session = Depends(require_session), auth: AuthManager = Depends(get_auth_manager)) -> dict[str, object]:
    user = auth.current_user(sess)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"ok": True, "user": user, "csrf": sess.csrf}


def _process_image(src: str, w: int, fmt: str, cache_path: Path):
    try:
        from PIL import Image  # type: ignore[import-untyped, import-not-found]
    except ImportError:
        # Pillow not installed, just copy the file
        import shutil
        src_path = Path(src)
        if not src_path.exists() and (Path("static") / src).exists():
            src_path = Path("static") / src
        if src_path.exists():
            shutil.copy(src_path, cache_path)
        return

    src_path = Path(src)
    if not src_path.exists():
        if (Path("static") / src).exists():
            src_path = Path("static") / src
        else:
            return

    img = Image.open(src_path)
    if w:
        ratio = w / float(img.size[0])
        h = int((float(img.size[1]) * float(ratio)))
        img = img.resize((w, h), Image.Resampling.LANCZOS)
    img.save(cache_path, format=fmt.upper())

@router.get("/_xania/image")
async def serve_optimized_image(src: str, w: int = 1080, fmt: str = "webp"):
    from fastapi.responses import FileResponse
    from pathlib import Path
    import hashlib
    import asyncio
    
    # Simple security check to prevent directory traversal
    if ".." in src or src.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid image path")

    cache_dir = Path(".xania_cache/images")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{hashlib.md5(src.encode()).hexdigest()}_{w}w.{fmt}"
    
    if cache_path.exists():
        return FileResponse(cache_path)
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _process_image, src, w, fmt, cache_path)
    
    if cache_path.exists():
        return FileResponse(cache_path)
    
    # Fallback if processing failed
    src_path = Path(src)
    if not src_path.exists() and (Path("static") / src).exists():
        src_path = Path("static") / src
    
    if src_path.exists():
        return FileResponse(src_path)
        
    raise HTTPException(status_code=404, detail="Image not found")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    import uuid
    from xania.engine.differ import diff, serialize_patches
    
    session_id = websocket.cookies.get("xania_session_id")
    if not session_id:
        # Without a session from the initial page load, we can't reliably map state.
        await websocket.close(code=1008, reason="Missing session cookie")
        return

    try:
        while True:
            # Wait for any message from the client
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
                req = EventRequest(**data)
            except Exception:
                continue # Ignore malformed

            try:
                component = ComponentRegistry.get(req.component, session_id)
            except KeyError:
                # Component not yet registered (user might need to refresh the page)
                await websocket.send_json({"error": f"Component '{req.component}' not found. Please refresh the page."})
                continue

            # Wrap event processing so errors don't kill the WebSocket
            try:
                from xania.renderer.elements import Element

                old_vdom = None
                if req.action == MOUNT_ACTION:
                    if not getattr(component, "_mounted", False):
                        if hasattr(component, "mount"):
                            await _call_lifecycle(component.mount)
                        component._mounted = True
                else:
                    # Wrap in a container div matching <div id="app_root"> in the DOM
                    # so that patch paths align with the actual DOM tree
                    old_vdom = Element("div", component.render(component.state))
                    old_state = component.state.to_dict()
                    await component.handle(req.action, req.payload)  # type: ignore
                    if hasattr(component, "update"):
                        if asyncio.iscoroutinefunction(component.update):
                            await component.update(old_state)
                        else:
                            await asyncio.get_event_loop().run_in_executor(None, component.update, old_state)
                            
                    # Persist state back to store
                    ComponentRegistry._session_store.set(session_id, req.component, component)

                new_vdom = Element("div", component.render(component.state))

                if old_vdom is not None:
                    patches = diff(old_vdom, new_vdom)
                    response_data = {"updates": [{
                        "id": component.id,
                        "patches": serialize_patches(patches),
                    }]}
                else:
                    html = component.to_html()
                    response_data = {"updates": [{
                        "id": component.id,
                        "html": html,
                    }]}
                    
                await websocket.send_json(response_data)
                
            except Exception as exc:
                import traceback
                traceback.print_exc()
                await websocket.send_json({"error": f"Event processing failed: {exc}"})
            
    except WebSocketDisconnect:
        pass



@router.get("/{full_path:path}", response_class=HTMLResponse)
def spa_fallback(request: Request, response: Response, full_path: str) -> str:
    # History API fallback so refresh works on routes like `/about`.
    # Excludes API paths and static assets (served by app.mount()).
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    return index(request, response)


__all__ = ["router", "MOUNT_ACTION"]
