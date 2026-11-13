from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import enforce_rate_limit, get_current_admin_user
from app.models import LegalChunk, LegalSource, User
from app.schemas import LegalSourceIngestRequest, LegalSourceResponse
from app.services.ai_provider import ai_provider
from app.services.chunker import chunk_statutory_text, extract_text_from_pdf_bytes

router = APIRouter(
    prefix="/sources",
    tags=["Legal Sources & Ingestion"],
    dependencies=[Depends(enforce_rate_limit)],
)

MAX_PDF_BYTES = 5 * 1024 * 1024  # 5 MB
READ_CHUNK_SIZE = 64 * 1024  # 64 KB


@router.get("/jurisdictions", response_model=List[str])
def list_jurisdictions(db: Session = Depends(get_db)) -> List[str]:
    rows = db.query(LegalSource.jurisdiction).distinct().all()
    jurisdictions = sorted({r[0] for r in rows if r[0]})
    return jurisdictions


@router.get("", response_model=List[LegalSourceResponse])
def list_legal_sources(
    jurisdiction: Optional[str] = None, db: Session = Depends(get_db)
) -> List[LegalSource]:
    query = db.query(LegalSource)
    if jurisdiction:
        query = query.filter(LegalSource.jurisdiction == jurisdiction)
    return query.order_by(LegalSource.jurisdiction, LegalSource.id).all()


@router.post(
    "/ingest",
    response_model=LegalSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_legal_source_text(
    payload: LegalSourceIngestRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> LegalSource:
    parsed_chunks = chunk_statutory_text(payload.raw_text)
    if not parsed_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract valid statutory chunks from the provided text.",
        )

    source = LegalSource(
        jurisdiction=payload.jurisdiction.strip(),
        title=payload.title.strip(),
        citation_prefix=payload.citation_prefix.strip(),
        source_url=payload.source_url,
        effective_date=payload.effective_date,
        is_active=payload.is_active,
        superseded_by=payload.superseded_by,
    )
    db.add(source)
    db.flush()

    for c in parsed_chunks:
        emb = ai_provider.get_embedding(
            f"{c['section_code']} {c['heading']} {c['content']}"
        )
        chunk = LegalChunk(
            source_id=source.id,
            jurisdiction=source.jurisdiction,
            section_code=c["section_code"],
            heading=c["heading"],
            content=c["content"],
            is_active=source.is_active,
            superseded_by=source.superseded_by,
            embedding=emb,
        )
        db.add(chunk)

    db.commit()
    db.refresh(source)
    return source


@router.post(
    "/ingest-pdf",
    response_model=LegalSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_legal_source_pdf(
    jurisdiction: str = Form(...),
    title: str = Form(...),
    citation_prefix: str = Form(...),
    source_url: Optional[str] = Form(None),
    effective_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> LegalSource:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files (.pdf) are allowed.",
        )

    if file.size is not None and file.size > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded PDF exceeds 5MB limit.",
        )

    buffer = bytearray()
    while True:
        chunk = await file.read(READ_CHUNK_SIZE)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > MAX_PDF_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Uploaded PDF exceeds 5MB limit.",
            )

    extracted_text = extract_text_from_pdf_bytes(bytes(buffer))
    if len(extracted_text.strip()) < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF did not contain sufficient extractable text.",
        )

    ingest_req = LegalSourceIngestRequest(
        jurisdiction=jurisdiction,
        title=title,
        citation_prefix=citation_prefix,
        source_url=source_url,
        effective_date=effective_date,
        is_active=True,
        raw_text=extracted_text,
    )
    return ingest_legal_source_text(
        payload=ingest_req, current_admin=current_admin, db=db
    )
