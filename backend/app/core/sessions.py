"stateful siession id stored in redis"

from app.config import get_settings
from app.core.redis import get_client
from app.core.security import generate_session_token, hash_session_token

settings = get_settings()

SESSION_PREFIX = "session:"
USER_PREFIX = "user_sessions:"


def _session_key(token_hash: str) -> str:
    return f"{SESSION_PREFIX}{token_hash}"


def _user_key(user_id: int) -> str:
    return f"{USER_PREFIX}{user_id}"


def create_session(user_id: int) -> str:
    """Create a session and return the raw token to put in the cookie."""
    token = generate_session_token()
    token_hash = hash_session_token(token)
    ttl = settings.session_ttl_minutes * 60

    redis_client = get_client()
    pipe = redis_client.pipeline()  # batch into one network request

    pipe.set(_session_key(token_hash), user_id, ex=ttl)
    pipe.sadd(
        _user_key(user_id), token_hash
    )  # multiple sessions per user, a user with a set of tokens

    # Keep the index from outliving its sessions; refreshed on each new login.
    pipe.expire(
        _user_key(user_id), ttl
    )  # sadd doesnt clean itself so we must clear dead expired hashes in the set
    pipe.execute()
    return token


def resolve_session(token: str) -> int | None:
    """Return the user_id for a live token, or None if missing/expired."""
    value = get_client().get(_session_key(hash_session_token(token)))
    return int(value) if value is not None else None


def revoke(token: str) -> None:
    """Revoke a single session (logout)."""
    redis_client = get_client()
    token_hash = hash_session_token(token)
    user_id = redis_client.get(_session_key(token_hash))

    pipe = redis_client.pipeline()
    pipe.delete(_session_key(token_hash))
    if user_id is not None:
        pipe.srem(_user_key(int(user_id)), token_hash)
    pipe.execute()


def revoke_all_for_user(user_id: int) -> None:
    """Revoke every session for a user (e.g. after a password change)."""
    redis_client = get_client()
    token_hashes = redis_client.smembers(_user_key(user_id))  # all members of the set

    pipe = redis_client.pipeline()
    for token_hash in token_hashes:
        pipe.delete(_session_key(token_hash))
    pipe.delete(_user_key(user_id))
    pipe.execute()
