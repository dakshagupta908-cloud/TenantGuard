from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import LegalChunk, LegalSource

router = APIRouter(tags=["Health & Status"])


@router.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "ai_provider": settings.AI_PROVIDER,
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict:
    sources_count = db.query(LegalSource).count()
    chunks_count = db.query(LegalChunk).count()
    return {
        "status": "ready",
        "database_connected": True,
        "ai_provider": settings.AI_PROVIDER,
        "indexed_sources": sources_count,
        "indexed_chunks": chunks_count,
    }
