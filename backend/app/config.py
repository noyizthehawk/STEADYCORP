"""Application settings, loaded from environment variables (and .env as fallback).

Organized by concern: top-level app settings, plus nested groups for the
external services. Each group reads its own env-prefixed variables — e.g.
``StripeSettings`` reads ``STRIPE_SECRET_KEY`` / ``STRIPE_WEBHOOK_SECRET`` — so
the .env keys stay flat and readable while the Python stays grouped
(``settings.stripe.secret_key``). Real secrets are wrapped in ``SecretStr`` so
they don't leak into logs or reprs.

Precedence (pydantic-settings): real process env vars > .env file > defaults.
"""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = ".env"


class StripeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_prefix="STRIPE_", extra="ignore")

    secret_key: SecretStr = SecretStr("")  # STRIPE_SECRET_KEY
    webhook_secret: SecretStr = SecretStr("")  # STRIPE_WEBHOOK_SECRET


class R2Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_prefix="R2_", extra="ignore")

    account_id: str = ""  # R2_ACCOUNT_ID
    access_key_id: str = ""  # R2_ACCESS_KEY_ID
    secret_access_key: SecretStr = SecretStr("")  # R2_SECRET_ACCESS_KEY
    bucket: str = ""  # R2_BUCKET
    public_base_url: str = ""  # R2_PUBLIC_BASE_URL


class ResendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_prefix="RESEND_", extra="ignore")

    api_key: SecretStr = SecretStr("")  # RESEND_API_KEY


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    #core
    environment: str = "dev"  # ENVIRONMENT
    database_url: str = "sqlite:///./steadycorp.db"  # DATABASE_URL
    frontend_origin: str = "http://localhost:5173"  # FRONTEND_ORIGIN

    # Auth (stateful session-id, stored in Redis)
    session_ttl_minutes: int = 60 * 24 * 7  # SESSION_TTL_MINUTES (default 7 days)
    redis_url: str = "redis://localhost:6379/0"  # REDIS_URL

    # Drop / claim tuning
    brick_hold_minutes: int = 10  # BRICK_HOLD_MINUTES
    bricks_per_drop: int = 20  # BRICKS_PER_DROP

    #shipping
    shipping_allowed_countries: str = "US,CA"  # SHIPPING_ALLOWED_COUNTRIES

    @property
    def shipping_allowed_countries_list(self) -> list[str]:
        return [c.strip().upper() for c in self.shipping_allowed_countries.split(",") if c.strip()]

    #  Quiz gate (K-of-N threshold) 
    quiz_questions_per_run: int = 6  # QUIZ_QUESTIONS_PER_RUN (N)
    quiz_required_correct: int = 3  # QUIZ_REQUIRED_CORRECT (K)
    quiz_seconds_per_question: int = 10  # QUIZ_SECONDS_PER_QUESTION

    # email
    email_from: str = "drops@steadycorp.example"  # EMAIL_FROM

    # --- Grouped service configs (each reads its own PREFIX_* env vars) ---
    stripe: StripeSettings = Field(default_factory=StripeSettings)
    r2: R2Settings = Field(default_factory=R2Settings)
    resend: ResendSettings = Field(default_factory=ResendSettings)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_prod(self) -> bool:
        return self.environment.lower() in {"prod", "production"}

    @property
    def cookie_secure(self) -> bool:
        """Send the session cookie only over HTTPS outside local dev."""
        return self.environment.lower() != "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
