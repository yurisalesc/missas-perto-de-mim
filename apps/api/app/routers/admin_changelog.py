"""Admin endpoints for changelog CRUD."""

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.models.changelog import ChangelogEntry
from app.repositories.changelog_repository import ChangelogRepository
from app.schemas.changelog import ChangelogCreate, ChangelogOut, ChangelogUpdate

router = APIRouter(dependencies=[Depends(require_admin)])

_FORTALEZA_TZ = ZoneInfo("America/Fortaleza")


def _to_naive_local(dt: datetime) -> datetime:
    """Convert datetime to naive local (Fortaleza) datetime.

    If *dt* is timezone-aware it is converted to America/Fortaleza first.
    Naive datetimes are assumed to already represent Fortaleza local time
    and are returned unchanged.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(_FORTALEZA_TZ).replace(tzinfo=None)
    return dt


@router.get("/changelog", response_model=list[ChangelogOut])
def list_changelog_entries(db: Session = Depends(get_db)) -> list[ChangelogOut]:
    """List all changelog entries for admin."""

    return ChangelogRepository(db).list_all()


@router.post("/changelog", response_model=ChangelogOut, status_code=201)
def create_changelog_entry(payload: ChangelogCreate, db: Session = Depends(get_db)) -> ChangelogOut:
    """Create a new changelog entry."""

    data = payload.model_dump()
    if data["published_at"] is not None:
        data["published_at"] = _to_naive_local(data["published_at"])
    else:
        data["published_at"] = datetime.now(_FORTALEZA_TZ).replace(tzinfo=None)
    return ChangelogRepository(db).create(ChangelogEntry(**data))


@router.patch("/changelog/{entry_id}", response_model=ChangelogOut)
def update_changelog_entry(
    entry_id: int,
    payload: ChangelogUpdate,
    db: Session = Depends(get_db),
) -> ChangelogOut:
    """Update an existing changelog entry."""

    repository = ChangelogRepository(db)
    entry = repository.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Changelog entry not found")
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        if key == "published_at" and isinstance(value, datetime):
            value = _to_naive_local(value)
        setattr(entry, key, value)
    return repository.update(entry)


@router.delete("/changelog/{entry_id}", status_code=204)
def delete_changelog_entry(entry_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a changelog entry."""

    repository = ChangelogRepository(db)
    entry = repository.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Changelog entry not found")
    repository.delete(entry)
