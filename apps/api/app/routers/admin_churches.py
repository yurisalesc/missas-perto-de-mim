"""Admin endpoints for church CRUD."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.schemas.church import ChurchCreate, ChurchDetailOut, ChurchOut, ChurchUpdate
from app.schemas.pagination import Page
from app.services.church_admin_service import ChurchAdminService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/igrejas", response_model=ChurchDetailOut, status_code=201)
def create_church(payload: ChurchCreate, db: Session = Depends(get_db)) -> ChurchDetailOut:
    return ChurchAdminService(db).create(payload)


@router.get("/igrejas", response_model=Page[ChurchOut] | list[ChurchOut])
def list_churches(
    nome: str | None = None,
    cidade: str | None = None,
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page[ChurchOut] | list[ChurchOut]:
    """List churches.

    - Without ``page``/``page_size``: legacy bare list (backward compatible).
    - With either pagination param: ``Page`` envelope (admin UI).
    """

    service = ChurchAdminService(db)
    if page is None and page_size is None:
        return service.list_all_filtered(nome=nome, cidade=cidade)

    return service.list_page(
        nome=nome,
        cidade=cidade,
        page=page or 1,
        page_size=page_size or 25,
    )


@router.get("/igrejas/{church_id}", response_model=ChurchDetailOut)
def get_church(church_id: int, db: Session = Depends(get_db)) -> ChurchDetailOut:
    return ChurchAdminService(db).get(church_id)


@router.patch("/igrejas/{church_id}", response_model=ChurchDetailOut)
def update_church(
    church_id: int, payload: ChurchUpdate, db: Session = Depends(get_db)
) -> ChurchDetailOut:
    return ChurchAdminService(db).update(church_id, payload)


@router.delete("/igrejas/{church_id}", status_code=204)
def delete_church(church_id: int, db: Session = Depends(get_db)) -> None:
    ChurchAdminService(db).delete(church_id)
