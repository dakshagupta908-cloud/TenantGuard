from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import AnalysisResult, Complaint, DemandLetter, User


def generate_demand_letter_draft(
    db: Session,
    complaint: Complaint,
    user: User,
    latest_analysis: Optional[AnalysisResult],
    recipient_name: Optional[str] = None,
    property_address: Optional[str] = None,
    requested_remedy: Optional[str] = None,
    response_deadline_days: int = 14,
) -> DemandLetter:
    today_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    deadline_date = (
        datetime.now(timezone.utc) + timedelta(days=response_deadline_days)
    ).strftime("%B %d, %Y")

    final_recipient = (
        recipient_name
        or complaint.landlord_name
        or "Property Owner / Management Company"
    )
    final_address = (
        property_address
        or complaint.property_address
        or "[Insert Rental Property Address & Unit Number]"
    )
    final_remedy = (
        requested_remedy
        or f"Prompt inspection and complete repair of the {complaint.category.lower()} issues described below."
    )

    # Include only active verified citations from the analysis
    active_citations = []
    if latest_analysis and not latest_analysis.abstained:
        for c in latest_analysis.verified_citations:
            if c.get("is_active", True):
                active_citations.append(c)

    citation_labels = [c["citation_label"] for c in active_citations]

    if active_citations:
        legal_basis_lines = [
            f"Under applicable housing regulations in {complaint.jurisdiction}, including:"
        ]
        for c in active_citations:
            legal_basis_lines.append(
                f"  • {c['citation_label']} ({c['heading']}): \"{c['excerpt']}\""
            )
        legal_basis_block = "\n".join(legal_basis_lines)
    else:
        legal_basis_block = (
            f"Please be advised that under local residential tenancy regulations in {complaint.jurisdiction}, "
            "the landlord is responsible for maintaining habitable premises and addressing essential repair needs."
        )

    onset_line = (
        f"This condition has been ongoing since {complaint.issue_start_date}."
        if complaint.issue_start_date
        else "This condition currently affects the habitability of the premises."
    )
    prior_notice_line = (
        "As previously communicated, I have notified management regarding this issue."
        if complaint.prior_notice_given
        else "Please accept this letter as formal written notice of the condition."
    )

    letter_body = f"""Date: {today_str}

To: {final_recipient}
{complaint.landlord_contact or ''}

From: {user.full_name} ({user.email})
Premises: {final_address}

Subject: FORMAL NOTICE OF REQUIRED REPAIRS — {complaint.title.upper()}

Dear {final_recipient},

I am writing as the current tenant at {final_address} to provide formal written notice of conditions requiring prompt maintenance and repair.

1. DESCRIPTION OF CONDITION
{complaint.description}

{onset_line} {prior_notice_line}

2. POTENTIALLY APPLICABLE HOUSING REGULATIONS ({complaint.jurisdiction})
{legal_basis_block}

3. REQUESTED ACTION & TIMELINE
To resolve this matter cooperatively and ensure the premises remain safe and habitable, I respectfully request the following action:
{final_remedy}

Please complete the requested repairs no later than {deadline_date} (within {response_deadline_days} calendar days from the date of this notice) and confirm in writing when the work is complete. If the repairs cannot be completed by then, please contact me promptly with a firm completion schedule.

I value a constructive tenancy and appreciate your prompt attention to this maintenance request. I am retaining a copy of this notice and supporting documentation for my records.

Sincerely,

_____________________________
{user.full_name}
Tenant at {final_address}

---
INFORMATIONAL NOTICE: This draft was prepared with the assistance of TenantGuard using tenant-supplied facts and retrieved statutory excerpts. It is for informational communication purposes and does not constitute formal legal representation.
"""

    letter = DemandLetter(
        complaint_id=complaint.id,
        user_id=user.id,
        title=f"Formal Repair Notice: {complaint.title}",
        recipient_name=final_recipient,
        property_address=final_address,
        requested_remedy=final_remedy,
        response_deadline_days=response_deadline_days,
        content=letter_body.strip(),
        citations_used=citation_labels,
    )
    complaint.status = "letter_ready"
    db.add(letter)
    db.commit()
    db.refresh(letter)
    return letter
