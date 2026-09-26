from __future__ import annotations

import asyncio
import inspect
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from xania.state.state import BaseState, default_registry

logger = logging.getLogger("xania.server")


class XaniaServer:
    """Production FastAPI WebSocket server powering Xania 4.0 SPA apps."""

    def __init__(self, state_cls: Optional[Type[BaseState]] = None, dist_dir: Optional[Path] = None):
        self.app = FastAPI(title="Xania Full-Stack SPA")
        self.state_cls = state_cls or BaseState
        self.dist_dir = dist_dir

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.middleware("http")
        async def allow_iframe_embedding(request, call_next):
            response = await call_next(request)
            if "x-frame-options" in response.headers:
                del response.headers["x-frame-options"]
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        self._setup_routes()

    def register_state(self, state_cls: Type[BaseState]) -> None:
        self.state_cls = state_cls

    def _setup_routes(self) -> None:
        @self.app.get("/api/health")
        async def health():
            return {"status": "ok", "framework": "Xania", "version": "4.0.2"}

        @self.app.websocket("/ws")
        async def websocket_endpoint(ws: WebSocket):
            await ws.accept()
            # Generate or retrieve session id
            session_id = ws.query_params.get("session_id", "default_session")
            state_instance = default_registry.get_state(session_id, self.state_cls)

            # Send initial state snapshot on connection
            initial_state = state_instance.get_full_state()
            await ws.send_text(json.dumps({
                "type": "init",
                "state": initial_state
            }))

            try:
                while True:
                    data_raw = await ws.receive_text()
                    try:
                        message = json.loads(data_raw)
                    except json.JSONDecodeError:
                        continue

                    # Handle event dispatch: { "name": "increment", "payload": {} }
                    event_name = message.get("name", "")
                    payload = message.get("payload", {})

                    # Strip class prefix if present (e.g. "CounterState.increment" -> "increment")
                    if "." in event_name:
                        _, method_name = event_name.split(".", 1)
                    else:
                        method_name = event_name

                    handler = getattr(state_instance, method_name, None)
                    if handler and callable(handler):
                        try:
                            sig = inspect.signature(handler)
                            params = list(sig.parameters.keys())
                            if len(params) == 0:
                                res = handler()
                            elif len(params) == 1:
                                if isinstance(payload, dict):
                                    if params[0] in payload:
                                        res = handler(payload[params[0]])
                                    elif "value" in payload:
                                        res = handler(payload["value"])
                                    else:
                                        res = handler(payload)
                                else:
                                    res = handler(payload)
                            else:
                                if isinstance(payload, dict):
                                    res = handler(**payload)
                                else:
                                    res = handler(payload)

                            if inspect.isawaitable(res):
                                await res
                        except Exception as e:
                            logger.exception("Error executing state handler %s: %s", method_name, e)

                    # Extract sparse delta & queued client events
                    delta = state_instance.get_delta()
                    events = state_instance.get_queued_events()

                    if delta or events:
                        await ws.send_text(json.dumps({
                            "type": "update",
                            "delta": delta,
                            "events": events
                        }))

            except WebSocketDisconnect:
                logger.info("Session %s disconnected", session_id)
            except Exception as e:
                logger.error("WebSocket exception: %s", e)

        # Mount compiled SPA dist in production if available
        if self.dist_dir and self.dist_dir.exists():
            index_path = self.dist_dir / "index.html"
            assets_dir = self.dist_dir / "assets"
            if assets_dir.exists():
                self.app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

            @self.app.get("/")
            async def spa_root():
                return FileResponse(index_path)

            @self.app.get("/{full_path:path}")
            async def spa_fallback(full_path: str):
                target = self.dist_dir / full_path
                if target.is_file():
                    return FileResponse(target)
                if index_path.exists():
                    return FileResponse(index_path)
                return HTMLResponse("<h1>SPA index.html not found</h1>", status_code=404)


def create_app(state_cls: Optional[Type[BaseState]] = None, dist_dir: Optional[Path] = None) -> FastAPI:
    server = XaniaServer(state_cls=state_cls, dist_dir=dist_dir)
    return server.app
