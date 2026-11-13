from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import enforce_rate_limit, get_current_user
from app.models import AnalysisResult, Complaint, User
from app.schemas import (
    AnalysisResultResponse,
    ComplaintCreateRequest,
    ComplaintResponse,
    ComplaintUpdateRequest,
)
from app.services.rag_service import run_rag_analysis_for_complaint

router = APIRouter(
    prefix="/complaints",
    tags=["Complaints & Legal Analysis"],
    dependencies=[Depends(enforce_rate_limit)],
)


def _get_owned_complaint(
    complaint_id: int, current_user: User, db: Session
) -> Complaint:
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint record not found.",
        )
    if complaint.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this complaint record.",
        )
    return complaint


@router.get("", response_model=List[ComplaintResponse])
def list_my_complaints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Complaint]:
    return (
        db.query(Complaint)
        .filter(Complaint.user_id == current_user.id)
        .order_by(Complaint.updated_at.desc())
        .all()
    )


@router.post(
    "", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED
)
def create_complaint(
    payload: ComplaintCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Complaint:
    complaint = Complaint(
        user_id=current_user.id,
        title=payload.title.strip(),
        jurisdiction=payload.jurisdiction.strip(),
        category=payload.category.strip(),
        description=payload.description.strip(),
        property_address=payload.property_address,
        landlord_name=payload.landlord_name,
        landlord_contact=payload.landlord_contact,
        issue_start_date=payload.issue_start_date,
        prior_notice_given=payload.prior_notice_given,
        urgency_level=payload.urgency_level,
        status="draft",
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint_detail(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Complaint:
    return _get_owned_complaint(complaint_id, current_user, db)


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: int,
    payload: ComplaintUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Complaint:
    complaint = _get_owned_complaint(complaint_id, current_user, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(complaint, field, value)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    complaint = _get_owned_complaint(complaint_id, current_user, db)
    db.delete(complaint)
    db.commit()


@router.post(
    "/{complaint_id}/analyze",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    complaint = _get_owned_complaint(complaint_id, current_user, db)
    return run_rag_analysis_for_complaint(db=db, complaint=complaint)
