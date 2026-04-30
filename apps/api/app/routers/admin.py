"""Admin router aggregator."""

from fastapi import APIRouter

from app.routers import admin_changelog, admin_churches, admin_import, admin_schedules, admin_suggestions

router = APIRouter(tags=["administracao"])
router.include_router(admin_changelog.router)
router.include_router(admin_churches.router)
router.include_router(admin_schedules.router)
router.include_router(admin_suggestions.router)
router.include_router(admin_import.router)
