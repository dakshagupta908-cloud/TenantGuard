from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    default_jurisdiction = Column(String(64), default="US-NY-NYC", nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaints = relationship(
        "Complaint", back_populates="user", cascade="all, delete-orphan"
    )
    letters = relationship(
        "DemandLetter", back_populates="user", cascade="all, delete-orphan"
    )


class LegalSource(Base):
    __tablename__ = "legal_sources"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(64), index=True, nullable=False)
    title = Column(String(512), nullable=False)
    citation_prefix = Column(String(128), nullable=False)
    source_url = Column(String(1024), nullable=True)
    effective_date = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    superseded_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    chunks = relationship(
        "LegalChunk", back_populates="source", cascade="all, delete-orphan"
    )


class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(
        Integer, ForeignKey("legal_sources.id", ondelete="CASCADE"), nullable=False
    )
    jurisdiction = Column(String(64), index=True, nullable=False)
    section_code = Column(String(128), nullable=False)
    heading = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    superseded_by = Column(String(255), nullable=True)
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("LegalSource", back_populates="chunks")

    __table_args__ = (
        Index("ix_legal_chunks_jurisdiction_section", "jurisdiction", "section_code"),
    )


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title = Column(String(255), nullable=False)
    jurisdiction = Column(String(64), index=True, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    property_address = Column(String(512), nullable=True)
    landlord_name = Column(String(255), nullable=True)
    landlord_contact = Column(String(255), nullable=True)
    issue_start_date = Column(String(64), nullable=True)
    prior_notice_given = Column(Boolean, default=False, nullable=False)
    urgency_level = Column(String(32), default="medium", nullable=False)
    status = Column(String(32), default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user = relationship("User", back_populates="complaints")
    analyses = relationship(
        "AnalysisResult",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisResult.created_at)",
    )
    letters = relationship(
        "DemandLetter",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="desc(DemandLetter.updated_at)",
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(
        Integer,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    abstained = Column(Boolean, default=False, nullable=False)
    abstention_reason = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    summary_explanation = Column(Text, nullable=False)
    key_rights = Column(JSON, default=list, nullable=False)
    missing_evidence = Column(JSON, default=list, nullable=False)
    limitations_and_warnings = Column(JSON, default=list, nullable=False)
    recommended_next_steps = Column(JSON, default=list, nullable=False)
    verified_citations = Column(JSON, default=list, nullable=False)
    stripped_hallucinations_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", back_populates="analyses")


class DemandLetter(Base):
    __tablename__ = "demand_letters"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(
        Integer,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title = Column(String(255), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    property_address = Column(String(512), nullable=False)
    requested_remedy = Column(Text, nullable=False)
    response_deadline_days = Column(Integer, default=14, nullable=False)
    content = Column(Text, nullable=False)
    citations_used = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    complaint = relationship("Complaint", back_populates="letters")
    user = relationship("User", back_populates="letters")
