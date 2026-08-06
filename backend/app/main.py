"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import health
from app.auth.endpoint import router as auth_router
from app.bricks.endpoint import router as bricks_router
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
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(bricks_router, prefix="/api", tags=["bricks"])

# Feature routers get wired here as they land — prefix/tags applied at include:
#   from app.drops.endpoint import router as drops_router
#   app.include_router(drops_router, prefix="/api/drops", tags=["drops"])
