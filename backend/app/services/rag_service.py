from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AnalysisResult, Complaint, LegalChunk, LegalSource
from app.services.ai_provider import ai_provider, cosine_similarity


def run_rag_analysis_for_complaint(
    db: Session, complaint: Complaint
) -> AnalysisResult:
    # 1. Fetch all indexed chunks for the selected jurisdiction
    rows = (
        db.query(LegalChunk, LegalSource)
        .join(LegalSource, LegalChunk.source_id == LegalSource.id)
        .filter(LegalChunk.jurisdiction == complaint.jurisdiction)
        .all()
    )

    if not rows:
        analysis = AnalysisResult(
            complaint_id=complaint.id,
            abstained=True,
            abstention_reason=(
                f"No legal sources are currently indexed for jurisdiction '{complaint.jurisdiction}'. "
                "TenantGuard abstains from generating legal explanations when statutory sources are unavailable."
            ),
            confidence_score=0.0,
            summary_explanation=(
                f"Unable to analyze complaint because no housing statutes are indexed for {complaint.jurisdiction}. "
                "Please select a supported jurisdiction or ask an administrator to ingest statutory text."
            ),
            key_rights=[],
            missing_evidence=[
                f"Indexed statutory provisions for jurisdiction {complaint.jurisdiction}."
            ],
            limitations_and_warnings=[
                "TenantGuard abstains when a jurisdiction lacks indexed legal sources."
            ],
            recommended_next_steps=[
                "Consult a local tenant union or municipal housing agency for your jurisdiction."
            ],
            verified_citations=[],
            stripped_hallucinations_count=0,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    # 2. Compute query embedding and score candidate chunks
    query_text = f"{complaint.category} {complaint.title} {complaint.description}"
    query_vec = ai_provider.get_embedding(query_text)

    scored_candidates: List[Dict[str, Any]] = []
    for chunk, source in rows:
        score = cosine_similarity(query_vec, chunk.embedding or [])
        effective_score = score if (chunk.is_active and source.is_active) else score * 0.85
        scored_candidates.append(
            {
                "chunk_id": chunk.id,
                "source_id": source.id,
                "jurisdiction": chunk.jurisdiction,
                "source_title": source.title,
                "citation_label": f"{source.citation_prefix} {chunk.section_code}".strip(),
                "section_code": chunk.section_code,
                "heading": chunk.heading,
                "excerpt": chunk.content,
                "similarity_score": round(effective_score, 4),
                "is_active": bool(chunk.is_active and source.is_active),
                "superseded_by": chunk.superseded_by or source.superseded_by,
                "source_url": source.source_url,
            }
        )

    scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    top_chunks = [
        c
        for c in scored_candidates[: settings.TOP_K_CHUNKS]
        if c["similarity_score"] >= settings.MIN_SIMILARITY_THRESHOLD
    ]

    # 3. Safe abstention if no retrieved chunk meets minimum similarity confidence
    if not top_chunks:
        best_score = scored_candidates[0]["similarity_score"] if scored_candidates else 0.0
        analysis = AnalysisResult(
            complaint_id=complaint.id,
            abstained=True,
            abstention_reason=(
                f"Retrieved statutory provisions in '{complaint.jurisdiction}' had insufficient relevance "
                f"(highest similarity score {best_score:.2f} < threshold {settings.MIN_SIMILARITY_THRESHOLD:.2f})."
            ),
            confidence_score=best_score,
            summary_explanation=(
                "TenantGuard abstained from providing a statutory interpretation because none of the indexed laws "
                f"in {complaint.jurisdiction} closely matched the specific issue described."
            ),
            key_rights=[],
            missing_evidence=[
                "More specific details regarding physical housing conditions (e.g., heat, water leaks, plumbing, utility shutoff) or additional local statutes."
            ],
            limitations_and_warnings=[
                "Automated abstention triggered to prevent ungrounded legal extrapolation."
            ],
            recommended_next_steps=[
                "Refine your complaint description with specific housing defect facts."
            ],
            verified_citations=[],
            stripped_hallucinations_count=0,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    # 4. Generate grounded analysis via AI Provider
    raw_synthesis = ai_provider.generate_grounded_analysis(
        complaint_description=complaint.description,
        jurisdiction=complaint.jurisdiction,
        prior_notice_given=complaint.prior_notice_given,
        issue_start_date=complaint.issue_start_date or "",
        retrieved_chunks=top_chunks,
    )

    # 5. Strict Citation-ID Validation against retrieved chunk IDs (No blind fallback)
    allowed_by_id = {c["chunk_id"]: c for c in top_chunks}
    claimed_ids = raw_synthesis.get("cited_chunk_ids", [])
    verified_citations: List[Dict[str, Any]] = []
    stripped_count = 0
    seen_ids = set()

    if isinstance(claimed_ids, list):
        for cid in claimed_ids:
            if isinstance(cid, int) and cid in allowed_by_id:
                if cid not in seen_ids:
                    verified_citations.append(allowed_by_id[cid])
                    seen_ids.add(cid)
            else:
                stripped_count += 1

    # If the synthesizer failed to cite any valid retrieved chunk ID, abstain safely
    if not verified_citations:
        analysis = AnalysisResult(
            complaint_id=complaint.id,
            abstained=True,
            abstention_reason=(
                "Post-generation citation validation failed: the model did not cite any valid retrieved statutory chunk IDs."
            ),
            confidence_score=0.0,
            summary_explanation=(
                "TenantGuard abstained because the generated response could not be linked to any valid retrieved statutory section ID."
            ),
            key_rights=[],
            missing_evidence=[],
            limitations_and_warnings=[
                "Citation-ID validation checks referential integrity against retrieved chunks and abstains when zero valid citations remain."
            ],
            recommended_next_steps=[
                "Re-run the analysis or inspect the statutory library directly."
            ],
            verified_citations=[],
            stripped_hallucinations_count=stripped_count,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    # 6. Check for outdated/superseded statutes in verified citations and inject explicit warnings
    limitations = list(raw_synthesis.get("limitations_and_warnings", []))
    for vc in verified_citations:
        if not vc["is_active"]:
            superseded_note = (
                f"WARNING: Retrieved provision {vc['citation_label']} is marked as historical/superseded"
                + (f" by {vc['superseded_by']}." if vc["superseded_by"] else ".")
                + " Do not rely on superseded thresholds without verifying current amendments."
            )
            if superseded_note not in limitations:
                limitations.insert(0, superseded_note)

    avg_conf = round(
        sum(c["similarity_score"] for c in verified_citations) / len(verified_citations),
        4,
    )

    analysis = AnalysisResult(
        complaint_id=complaint.id,
        abstained=False,
        abstention_reason=None,
        confidence_score=avg_conf,
        summary_explanation=raw_synthesis.get("summary_explanation", ""),
        key_rights=raw_synthesis.get("key_rights", []),
        missing_evidence=raw_synthesis.get("missing_evidence", []),
        limitations_and_warnings=limitations,
        recommended_next_steps=raw_synthesis.get("recommended_next_steps", []),
        verified_citations=verified_citations,
        stripped_hallucinations_count=stripped_count,
    )
    complaint.status = "analyzed"
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis
