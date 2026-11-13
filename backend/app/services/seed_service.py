import json
from pathlib import Path
from sqlalchemy.orm import Session

from app.models import LegalChunk, LegalSource
from app.services.ai_provider import ai_provider


def seed_initial_legal_sources(db: Session) -> int:
    existing_count = db.query(LegalSource).count()
    if existing_count > 0:
        return 0

    seed_path = (
        Path(__file__).resolve().parent.parent.parent
        / "seed_data"
        / "sample_housing_codes.json"
    )
    if not seed_path.exists():
        return 0

    raw_sources = json.loads(seed_path.read_text(encoding="utf-8"))
    created_chunks = 0

    for item in raw_sources:
        source = LegalSource(
            jurisdiction=item["jurisdiction"],
            title=item["title"],
            citation_prefix=item["citation_prefix"],
            source_url=item.get("source_url"),
            effective_date=item.get("effective_date"),
            is_active=item.get("is_active", True),
            superseded_by=item.get("superseded_by"),
        )
        db.add(source)
        db.flush()

        for sec in item.get("sections", []):
            text_for_embedding = f"{sec['section_code']} {sec['heading']} {sec['text']}"
            emb = ai_provider.get_embedding(text_for_embedding)
            chunk = LegalChunk(
                source_id=source.id,
                jurisdiction=source.jurisdiction,
                section_code=sec["section_code"],
                heading=sec["heading"],
                content=sec["text"],
                is_active=sec.get("is_active", source.is_active),
                superseded_by=sec.get("superseded_by", source.superseded_by),
                embedding=emb,
            )
            db.add(chunk)
            created_chunks += 1

    db.commit()
    return created_chunks
