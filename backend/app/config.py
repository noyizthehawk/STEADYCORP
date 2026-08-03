"""Application settings, loaded from environment / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "dev"
    database_url: str = "sqlite:///./steadycorp.db"

    # Auth
    jwt_secret: str = "change-me-dev-only"
    access_token_ttl: int = 60 * 24 * 7  # minutes

    # Drop / claim tuning
    brick_hold_minutes: int = 10
    bricks_per_drop: int = 20

    # CORS
    frontend_origin: str = "http://localhost:5173"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    r2_public_base_url: str = ""

    # Resend
    resend_api_key: str = ""
    email_from: str = "drops@steadycorp.example"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
