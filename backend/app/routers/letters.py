from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import enforce_rate_limit, get_current_user
from app.models import AnalysisResult, Complaint, DemandLetter, User
from app.schemas import (
    DemandLetterResponse,
    LetterGenerateRequest,
    LetterSendRequest,
    LetterSendResponse,
    LetterUpdateRequest,
)
from app.services.delivery_service import DeliveryError, send_letter_email, send_letter_sms
from app.services.letter_service import generate_demand_letter_draft

router = APIRouter(
    prefix="/letters",
    tags=["Demand Letters"],
    dependencies=[Depends(enforce_rate_limit)],
)


def _get_owned_letter(
    letter_id: int, current_user: User, db: Session
) -> DemandLetter:
    letter = db.query(DemandLetter).filter(DemandLetter.id == letter_id).first()
    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demand letter not found.",
        )
    if letter.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this demand letter.",
        )
    return letter


@router.post(
    "/generate",
    response_model=DemandLetterResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_letter(
    payload: LetterGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DemandLetter:
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == payload.complaint_id)
        .first()
    )
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )
    if complaint.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to generate a letter for this complaint.",
        )

    latest_analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.complaint_id == complaint.id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )

    return generate_demand_letter_draft(
        db=db,
        complaint=complaint,
        user=current_user,
        latest_analysis=latest_analysis,
        recipient_name=payload.recipient_name,
        property_address=payload.property_address,
        requested_remedy=payload.requested_remedy,
        response_deadline_days=payload.response_deadline_days,
    )


@router.get("/{letter_id}", response_model=DemandLetterResponse)
def get_letter(
    letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DemandLetter:
    return _get_owned_letter(letter_id, current_user, db)


@router.patch("/{letter_id}", response_model=DemandLetterResponse)
def update_letter(
    letter_id: int,
    payload: LetterUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DemandLetter:
    letter = _get_owned_letter(letter_id, current_user, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(letter, field, value)
    db.commit()
    db.refresh(letter)
    return letter


@router.post("/{letter_id}/send", response_model=LetterSendResponse)
def send_letter(
    letter_id: int,
    payload: LetterSendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LetterSendResponse:
    letter = _get_owned_letter(letter_id, current_user, db)
    results = {}
    for channel, sender, recipient in (
        ("email", send_letter_email, str(payload.recipient_email)),
        ("sms", send_letter_sms, payload.recipient_phone),
    ):
        try:
            sender(recipient, letter)
            results[channel] = {"sent": True}
        except DeliveryError as exc:
            results[channel] = {"sent": False, "error": str(exc)}
    return LetterSendResponse(**results)


@router.delete("/{letter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_letter(
    letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    letter = _get_owned_letter(letter_id, current_user, db)
    db.delete(letter)
    db.commit()


@router.get("/{letter_id}/export")
def export_letter_txt(
    letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    letter = _get_owned_letter(letter_id, current_user, db)
    filename = f"tenantguard_letter_{letter.id}.txt"
    return Response(
        content=letter.content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
