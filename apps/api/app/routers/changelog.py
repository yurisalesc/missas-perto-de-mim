"""Public changelog endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.changelog_repository import ChangelogRepository
from app.schemas.changelog import ChangelogOut

router = APIRouter(prefix="/changelog", tags=["changelog"])


@router.get("/latest", response_model=list[ChangelogOut])
def list_latest_changelog(db: Session = Depends(get_db)) -> list[ChangelogOut]:
    """Return changelog entries from the last 15 days."""

    return ChangelogRepository(db).list_last_days(days=15)
