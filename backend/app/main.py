"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="STEADYCORP",
    description="Drop-site API for STEADY BRICKS.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,  # httpOnly cookie auth
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)

# Feature routers get wired here as they land:
#   app.include_router(auth.router)
#   app.include_router(drops.router)
#   app.include_router(game.router)
#   app.include_router(checkout.router)
#   app.include_router(webhooks.router)
