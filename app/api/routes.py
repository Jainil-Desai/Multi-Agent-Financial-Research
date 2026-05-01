from fastapi import APIRouter

from app.api.ingest import router as ingest_router
from app.api.research import router as research_router

router = APIRouter()
router.include_router(ingest_router)
router.include_router(research_router)
