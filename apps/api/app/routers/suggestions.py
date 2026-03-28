"""Suggestion endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.suggestion import UserSuggestion
from app.repositories.suggestion_repository import SuggestionRepository
from app.schemas.suggestion import SuggestionCreate, SuggestionOut

router = APIRouter(prefix="/sugestoes", tags=["sugestoes"])


@router.post("", response_model=SuggestionOut, status_code=201)
def create_suggestion(payload: SuggestionCreate, db: Session = Depends(get_db)) -> UserSuggestion:
    """Create a new user suggestion without account requirement."""

    suggestion = UserSuggestion(**payload.model_dump(), status="pending")
    return SuggestionRepository(db).create(suggestion)
