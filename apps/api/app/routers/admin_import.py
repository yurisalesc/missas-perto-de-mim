"""Admin endpoints for CSV import/export."""

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.services.admin_csv_service import AdminCsvService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/importacao/csv")
async def import_churches_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    content = await file.read()
    return AdminCsvService(db).import_compact_csv(content)


@router.post("/importacao/csv/popular")
async def populate_database_from_csv(
    file: UploadFile = File(...),
    replace_existing: bool = True,
    db: Session = Depends(get_db),
) -> dict:
    content = await file.read()
    return AdminCsvService(db).populate_database_from_wide_csv(content, replace_existing=replace_existing)


@router.get("/exportacao/csv")
def export_database_to_csv(db: Session = Depends(get_db)) -> StreamingResponse:
    return AdminCsvService(db).export_database_csv_response()

