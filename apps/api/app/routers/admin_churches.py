"""Admin endpoints for church CRUD."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.core.text_normalization import expand_nossa_senhora
from app.db.session import get_db
from app.models.church import Church
from app.repositories.church_repository import ChurchRepository
from app.schemas.church import ChurchCreate, ChurchOut, ChurchUpdate

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/igrejas", response_model=ChurchOut, status_code=201)
def create_church(payload: ChurchCreate, db: Session = Depends(get_db)) -> Church:
    data = payload.model_dump()
    data["nome"] = expand_nossa_senhora(data["nome"])
    return ChurchRepository(db).create(Church(**data))


@router.get("/igrejas", response_model=list[ChurchOut])
def list_churches(
    nome: str | None = None,
    cidade: str | None = None,
    db: Session = Depends(get_db),
) -> list[Church]:
    return ChurchRepository(db).list_filtered(nome=nome, cidade=cidade)


@router.patch("/igrejas/{church_id}", response_model=ChurchOut)
def update_church(church_id: int, payload: ChurchUpdate, db: Session = Depends(get_db)) -> Church:
    church = ChurchRepository(db).get(church_id)
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    data = payload.model_dump(exclude_none=True)
    if "nome" in data:
        data["nome"] = expand_nossa_senhora(data["nome"])
    for key, value in data.items():
        setattr(church, key, value)
    db.commit()
    db.refresh(church)
    return church


@router.delete("/igrejas/{church_id}", status_code=204)
def delete_church(church_id: int, db: Session = Depends(get_db)) -> None:
    church = ChurchRepository(db).get(church_id)
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    ChurchRepository(db).delete(church)

