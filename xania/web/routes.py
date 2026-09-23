from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone

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
    <title>Xania Stress Demo</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body>
    <div id="app"></div>
    <script src="/static/spa_runtime.js"></script>
    <script src="/static/app.js"></script>
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


def _seeded_users(count: int = 5000) -> list[dict[str, object]]:
    rng = random.Random(1337)
    first = [
        "Aarav",
        "Aditi",
        "Alex",
        "Amir",
        "Ananya",
        "Chen",
        "Diego",
        "Elena",
        "Fatima",
        "Hana",
        "Isha",
        "Jamal",
        "Kaito",
        "Liam",
        "Mina",
        "Noah",
        "Omar",
        "Priya",
        "Sara",
        "Wei",
        "Yara",
        "Zoe",
    ]
    last = [
        "Singh",
        "Patel",
        "Sharma",
        "Khan",
        "Garcia",
        "Smith",
        "Kim",
        "Chen",
        "Brown",
        "Johnson",
        "Nakamura",
        "Hassan",
        "Ibrahim",
        "Lopez",
        "Martinez",
    ]
    roles = ["Admin", "Editor", "Analyst", "Support", "Member"]
    statuses = ["active", "invited", "disabled"]

    now = datetime.now(timezone.utc)
    users: list[dict[str, object]] = []
    for i in range(1, count + 1):
        fn = rng.choice(first)
        ln = rng.choice(last)
        name = f"{fn} {ln}"
        created = now - timedelta(days=rng.randint(0, 365 * 3), hours=rng.randint(0, 23))
        users.append(
            {
                "id": i,
                "name": name,
                "email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
                "role": rng.choice(roles),
                "status": rng.choices(statuses, weights=[80, 10, 10], k=1)[0],
                "score": rng.randint(0, 1000),
                "created_at": created.isoformat().replace("+00:00", "Z"),
            }
        )
    return users


_USERS = _seeded_users()


def _clamp_int(value: int, *, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


@router.get("/api/metrics")
def metrics() -> dict[str, object]:
    active = sum(1 for u in _USERS if u["status"] == "active")
    disabled = sum(1 for u in _USERS if u["status"] == "disabled")
    invited = len(_USERS) - active - disabled
    return {
        "users_total": len(_USERS),
        "users_active": active,
        "users_invited": invited,
        "users_disabled": disabled,
        "requests_per_min_estimate": 1200,
        "db_latency_ms_p50": 12,
        "db_latency_ms_p95": 48,
        "render_budget_ms": 16,
    }


@router.get("/api/users")
def list_users(q: str | None = None, page: int = 1, page_size: int = 50) -> dict[str, object]:
    page = _clamp_int(page, lo=1, hi=10_000_000)
    page_size = _clamp_int(page_size, lo=10, hi=1000)

    items = _USERS
    if q:
        qn = q.strip().lower()
        if qn:
            items = [u for u in _USERS if qn in str(u["name"]).lower() or qn in str(u["email"]).lower()]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    return {"items": page_items, "total": total, "page": page, "page_size": page_size}


@router.get("/api/users/{user_id}")
def get_user(user_id: int) -> dict[str, object]:
    if user_id < 1 or user_id > len(_USERS):
        raise HTTPException(status_code=404, detail="User not found")
    return _USERS[user_id - 1]


@router.get("/api/private/big-json")
def private_big_json(sess: Session = Depends(require_role("admin"))) -> dict[str, object]:
    # Protected read endpoint. Returns a large-ish payload to stress the client.
    items = [{"i": i, "n": f"item-{i}", "u": (i * 2654435761) % 2**32} for i in range(50_000)]
    return {"ok": True, "count": len(items), "items": items}


@router.post("/api/private/write-echo")
async def private_write_echo(payload: dict[str, object], sess: Session = Depends(require_csrf)) -> dict[str, object]:
    # Protected write endpoint with CSRF requirement.
    await asyncio.sleep(0)
    return {"ok": True, "received": payload}


@router.post("/api/echo")
async def echo(payload: dict[str, object]) -> dict[str, object]:
    # Tiny async boundary to mimic realistic request handling.
    await asyncio.sleep(0)
    return {"ok": True, "received": payload}


@router.get("/api/delay")
async def delay(ms: int = 250) -> dict[str, object]:
    ms = _clamp_int(ms, lo=0, hi=5000)
    await asyncio.sleep(ms / 1000)
    return {"ok": True, "slept_ms": ms}


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

            from xania.renderer.elements import Element

            old_vdom = None
            if req.action != MOUNT_ACTION:
                # Wrap in a container div matching <div id="app_root"> in the DOM
                # so that patch paths align with the actual DOM tree
                old_vdom = Element("div", component.render(component.state))
                component.handle(req.action, req.payload)

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
