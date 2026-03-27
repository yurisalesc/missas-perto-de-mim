"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.routers import admin, masses, search, suggestions

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables."""

    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck endpoint."""

    return {"status": "ok"}


app.include_router(search.router)
app.include_router(masses.router)
app.include_router(suggestions.router)
app.include_router(admin.router, prefix="/administracao")
app.include_router(admin.router, prefix="/admin")
