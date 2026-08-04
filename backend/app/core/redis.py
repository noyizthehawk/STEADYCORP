"""Redis client accessor.

A lazily-created singleton so importing this module never opens a connection
(redis-py connects on first command). Tests swap in a fakeredis instance via
``set_client`` — see the ``fake_redis`` fixture in tests/conftest.py.
"""

import redis

from app.config import get_settings

settings = get_settings()

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def set_client(client: redis.Redis | None) -> None:
    """Override the client (tests) or reset to None to rebuild from settings."""
    global _client
    _client = client
