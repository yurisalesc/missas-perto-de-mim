"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.core.config import settings
from app.db.base import Base
from app.db.migrations import ensure_church_optional_columns
from app.db.session import engine
from app.routers import admin, changelog, masses, search, suggestions

is_production = settings.app_env == "production"
app = FastAPI(
    title=settings.app_name,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables."""

    Base.metadata.create_all(bind=engine)
    ensure_church_optional_columns(engine)


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck endpoint."""

    return {"status": "ok"}


app.include_router(search.router)
app.include_router(masses.router)
app.include_router(suggestions.router)
app.include_router(changelog.router)
app.include_router(admin.router, prefix="/admin")
