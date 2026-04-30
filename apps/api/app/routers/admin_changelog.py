"""Admin endpoints for changelog CRUD."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.models.changelog import ChangelogEntry
from app.repositories.changelog_repository import ChangelogRepository
from app.schemas.changelog import ChangelogCreate, ChangelogOut, ChangelogUpdate

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/changelog", response_model=list[ChangelogOut])
def list_changelog_entries(db: Session = Depends(get_db)) -> list[ChangelogOut]:
    """List all changelog entries for admin."""

    return ChangelogRepository(db).list_all()


@router.post("/changelog", response_model=ChangelogOut, status_code=201)
def create_changelog_entry(payload: ChangelogCreate, db: Session = Depends(get_db)) -> ChangelogOut:
    """Create a new changelog entry."""

    data = payload.model_dump()
    data["published_at"] = data["published_at"] or datetime.now(UTC).replace(tzinfo=None)
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
