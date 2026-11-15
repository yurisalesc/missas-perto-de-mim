"""Admin endpoints for suggestion moderation."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.repositories.suggestion_repository import SuggestionRepository
from app.schemas.pagination import Page
from app.schemas.suggestion import SuggestionModeration, SuggestionOut

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/sugestoes", response_model=Page[SuggestionOut] | list[SuggestionOut])
def list_suggestions(
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page[SuggestionOut] | list[SuggestionOut]:
    """List suggestions.

    - Without pagination params: legacy bare list.
    - With either param: ``Page`` envelope.
    """

    repo = SuggestionRepository(db)
    if page is None and page_size is None:
        return repo.list_all()

    items, total = repo.list_page(page=page or 1, page_size=page_size or 25)
    return Page(items=items, total=total, page=page or 1, page_size=page_size or 25)


@router.patch("/sugestoes/{suggestion_id}", response_model=SuggestionOut)
def moderate_suggestion(
    suggestion_id: int, payload: SuggestionModeration, db: Session = Depends(get_db)
) -> SuggestionOut:
    repo = SuggestionRepository(db)
    suggestion = repo.get(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    try:
        suggestion.status = payload.status
        repo.save(suggestion)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return suggestion
