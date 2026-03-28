"""Admin endpoints for suggestion moderation."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.repositories.suggestion_repository import SuggestionRepository
from app.schemas.suggestion import SuggestionModeration, SuggestionOut

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/sugestoes", response_model=list[SuggestionOut])
def list_suggestions(db: Session = Depends(get_db)):
    return SuggestionRepository(db).list_all()


@router.patch("/sugestoes/{suggestion_id}", response_model=SuggestionOut)
def moderate_suggestion(
    suggestion_id: int, payload: SuggestionModeration, db: Session = Depends(get_db)
):
    suggestion = SuggestionRepository(db).get(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    suggestion.status = payload.status
    db.commit()
    db.refresh(suggestion)
    return suggestion

