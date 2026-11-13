from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    default_jurisdiction: str = Field(default="US-NY-NYC", max_length=64)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    default_jurisdiction: Optional[str] = Field(None, max_length=64)
    current_password: Optional[str] = Field(None, min_length=1, max_length=128)
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    default_jurisdiction: str
    is_admin: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Legal Source & Citation Schemas ---
class LegalChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    jurisdiction: str
    section_code: str
    heading: str
    content: str
    is_active: bool
    superseded_by: Optional[str] = None


class LegalSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    jurisdiction: str
    title: str
    citation_prefix: str
    source_url: Optional[str] = None
    effective_date: Optional[str] = None
    is_active: bool
    superseded_by: Optional[str] = None
    created_at: datetime
    chunks: List[LegalChunkResponse] = []


class LegalSourceIngestRequest(BaseModel):
    jurisdiction: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=4, max_length=512)
    citation_prefix: str = Field(..., min_length=2, max_length=128)
    source_url: Optional[str] = None
    effective_date: Optional[str] = None
    is_active: bool = True
    superseded_by: Optional[str] = None
    raw_text: str = Field(..., min_length=30)


class VerifiedCitationItem(BaseModel):
    chunk_id: int
    source_id: int
    jurisdiction: str
    source_title: str
    citation_label: str
    section_code: str
    heading: str
    excerpt: str
    similarity_score: float
    is_active: bool
    superseded_by: Optional[str] = None
    source_url: Optional[str] = None


# --- Analysis & Complaint Schemas ---
class AnalysisResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_id: int
    abstained: bool
    abstention_reason: Optional[str] = None
    confidence_score: float
    summary_explanation: str
    key_rights: List[str]
    missing_evidence: List[str]
    limitations_and_warnings: List[str]
    recommended_next_steps: List[str]
    verified_citations: List[VerifiedCitationItem]
    stripped_hallucinations_count: int
    created_at: datetime


class DemandLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_id: int
    user_id: int
    title: str
    recipient_name: str
    property_address: str
    requested_remedy: str
    response_deadline_days: int
    content: str
    citations_used: List[str]
    created_at: datetime
    updated_at: datetime


class ComplaintCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    jurisdiction: str = Field(..., min_length=2, max_length=64)
    category: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=20, max_length=8000)
    property_address: Optional[str] = Field(None, max_length=512)
    landlord_name: Optional[str] = Field(None, max_length=255)
    landlord_contact: Optional[str] = Field(None, max_length=255)
    issue_start_date: Optional[str] = Field(None, max_length=64)
    prior_notice_given: bool = False
    urgency_level: str = Field(default="medium", pattern="^(low|medium|high|emergency)$")


class ComplaintUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    jurisdiction: Optional[str] = Field(None, min_length=2, max_length=64)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, min_length=20, max_length=8000)
    property_address: Optional[str] = Field(None, max_length=512)
    landlord_name: Optional[str] = Field(None, max_length=255)
    landlord_contact: Optional[str] = Field(None, max_length=255)
    issue_start_date: Optional[str] = Field(None, max_length=64)
    prior_notice_given: Optional[bool] = None
    urgency_level: Optional[str] = Field(None, pattern="^(low|medium|high|emergency)$")
    status: Optional[str] = Field(None, pattern="^(draft|analyzed|letter_ready|resolved)$")


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    jurisdiction: str
    category: str
    description: str
    property_address: Optional[str] = None
    landlord_name: Optional[str] = None
    landlord_contact: Optional[str] = None
    issue_start_date: Optional[str] = None
    prior_notice_given: bool
    urgency_level: str
    status: str
    created_at: datetime
    updated_at: datetime
    analyses: List[AnalysisResultResponse] = []
    letters: List[DemandLetterResponse] = []


# --- Letter Generation & Editing Schemas ---
class LetterGenerateRequest(BaseModel):
    complaint_id: int
    recipient_name: Optional[str] = None
    property_address: Optional[str] = None
    requested_remedy: Optional[str] = None
    response_deadline_days: int = Field(default=14, ge=1, le=90)


class LetterUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    recipient_name: Optional[str] = Field(None, min_length=2, max_length=255)
    property_address: Optional[str] = Field(None, min_length=5, max_length=512)
    requested_remedy: Optional[str] = Field(None, min_length=5)
    response_deadline_days: Optional[int] = Field(None, ge=1, le=90)
    content: str = Field(..., min_length=20)


class LetterSendRequest(BaseModel):
    recipient_email: EmailStr
    recipient_phone: str = Field(..., pattern=r"^\+[1-9]\d{7,14}$")


class DeliveryChannelResult(BaseModel):
    sent: bool
    error: Optional[str] = None


class LetterSendResponse(BaseModel):
    email: DeliveryChannelResult
    sms: DeliveryChannelResult
