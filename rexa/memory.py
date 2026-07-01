from __future__ import annotations

import json
import os

import redis

_MAX_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "5"))
_TTL = int(os.getenv("MEMORY_TTL_SECONDS", str(60 * 60 * 24)))  # 24h default
_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "1.5"))
_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "1.5"))

_redis: redis.Redis | None = None


def _client() -> redis.Redis:
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=_SOCKET_TIMEOUT,
            health_check_interval=30,
        )
    return _redis


def _key(user_id: str) -> str:
    return f"rexa:chat:{user_id}"


def get_history(user_id: str) -> list[dict]:
    """Return [{role, content}, ...] for the last N turns."""
    try:
        raw = _client().get(_key(user_id))
        return json.loads(raw) if raw else []
    except Exception:
        return []


def save_turn(user_id: str, user_msg: str, assistant_msg: str) -> None:
    """Append a turn and trim to MEMORY_MAX_TURNS * 2 messages."""
    try:
        r = _client()
        key = _key(user_id)
        raw = r.get(key)
        history: list[dict] = json.loads(raw) if raw else []
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})
        history = history[-(_MAX_TURNS * 2):]
        r.set(key, json.dumps(history, ensure_ascii=False), ex=_TTL)
    except Exception:
        pass
