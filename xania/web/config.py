from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str
    secret_key: str
    cookie_secure: bool
    session_ttl_seconds: int
    redis_url: str | None

    @property
    def is_dev(self) -> bool:
        return self.env.lower() in {"dev", "development", "local"}


def get_settings() -> Settings:
    env = os.getenv("XANIA_ENV", "dev")
    secret = os.getenv("XANIA_SECRET_KEY", "")
    ttl_s = int(os.getenv("XANIA_SESSION_TTL_SECONDS", str(60 * 60 * 8)))

    # Default: dev-friendly, prod-safe.
    is_dev = env.lower() in {"dev", "development", "local"}
    if not secret and not is_dev:
        raise RuntimeError("XANIA_SECRET_KEY must be set in non-dev environments")
    if not secret and is_dev:
        secret = "dev-insecure-secret-change-me"

    cookie_secure = os.getenv("XANIA_COOKIE_SECURE", "").strip().lower()
    if cookie_secure in {"1", "true", "yes"}:
        secure = True
    elif cookie_secure in {"0", "false", "no"}:
        secure = False
    else:
        secure = not is_dev
        
    redis_url = os.getenv("XANIA_REDIS_URL")

    settings = Settings(
        env=env, 
        secret_key=secret, 
        cookie_secure=secure, 
        session_ttl_seconds=ttl_s,
        redis_url=redis_url
    )
    
    # Auto-configure Redis Session Store if URL is provided
    if redis_url:
        from xania.renderer.registry import ComponentRegistry
        from xania.renderer.redis_session import RedisSessionStore
        store = RedisSessionStore(redis_url=redis_url, ttl_seconds=ttl_s)
        ComponentRegistry.configure_store(store)
        
    return settings


__all__ = ["Settings", "get_settings"]

