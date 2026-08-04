"""Auth primitives: password hashing, email normalization, session tokens.

Pure, dependency-light helpers. No web framework, no Redis, no DB — the Redis
session store that consumes these lives in app/core/sessions.py.

- Passwords: argon2 (slow + salted, the right tool for low-entropy secrets).
- Session tokens: high-entropy random strings, hashed with SHA-256 before they
  touch storage (fast is fine — the token already carries full entropy). The
  raw token lives only in the httpOnly cookie; only its hash is a Redis key.
"""

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

COOKIE_NAME = "steadycorp_session"
password_hasher = PasswordHasher()

# A valid hash to verify against when a login email doesn't exist, so response
# time doesn't reveal whether an account is registered (constant-time login).
DUMMY_HASH = password_hasher.hash("steadycorp-timing-equalizer")


def hash_password(raw: str) -> str:
    return password_hasher.hash(raw)  # hash the password


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return password_hasher.verify(hashed, raw)  # compare raw password with the hash
    except VerificationError:
        return False


def normalize_email(raw: str) -> str:
    """Case-insensitive, whitespace-trimmed email key for storage/lookup."""
    return raw.strip().lower()


def generate_session_token() -> str:
    """Opaque token placed in the cookie; never persisted in the clear."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """SHA-256 of the session token — this is the Redis key, not the raw token."""
    return hashlib.sha256(token.encode()).hexdigest()
