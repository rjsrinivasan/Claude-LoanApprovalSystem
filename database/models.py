"""SQLAlchemy ORM models for the database."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Enum, Boolean,
    JSON, ForeignKey, Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Applicant(Base):
    """Applicant profile information."""

    __tablename__ = "applicants"

    applicant_id = Column(String(36), primary_key=True)
    age = Column(Integer, nullable=False)
    income = Column(Numeric(12, 2), nullable=False)  # Annual income
    employment_type = Column(
        Enum("salaried", "self_employed", "contract", "retired"),
        nullable=False,
    )
    employment_tenure_years = Column(Integer)
    location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applications = relationship("LoanApplication", back_populates="applicant")
    decisions = relationship("LoanDecision", back_populates="applicant")

    __table_args__ = (
        Index("idx_applicant_id", "applicant_id"),
        Index("idx_created_at", "created_at"),
    )


class LoanApplication(Base):
    """Loan application records."""

    __tablename__ = "loan_applications"

    application_id = Column(String(36), primary_key=True)
    applicant_id = Column(String(36), ForeignKey("applicants.applicant_id"), nullable=False)
    credit_score = Column(Integer, nullable=False)
    loan_amount = Column(Numeric(12, 2), nullable=False)
    loan_tenure_months = Column(Integer, nullable=False)
    existing_liabilities = Column(Numeric(12, 2), nullable=False)
    application_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(
        Enum("submitted", "processing", "completed"),
        default="submitted",
    )

    # Relationships
    applicant = relationship("Applicant", back_populates="applications")
    decision = relationship("LoanDecision", back_populates="application", uselist=False)

    __table_args__ = (
        Index("idx_applicant_id", "applicant_id"),
        Index("idx_created_at", "created_at"),
        Index("idx_status", "status"),
    )


class RiskRule(Base):
    """Risk assessment rules stored in database."""

    __tablename__ = "risk_rules"

    rule_id = Column(String(36), primary_key=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(
        Enum("credit_score", "dti_ratio", "loan_amount", "income_stability"),
        nullable=False,
    )
    min_value = Column(Numeric(10, 3))
    max_value = Column(Numeric(10, 3))
    threshold_approve = Column(Numeric(10, 3))
    threshold_review = Column(Numeric(10, 3))
    description = Column(String(500))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_rule_type", "rule_type"),
        Index("idx_active", "active"),
    )


class LoanDecision(Base):
    """Final loan decisions with reasoning."""

    __tablename__ = "loan_decisions"

    case_id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("loan_applications.application_id"), nullable=False)
    applicant_id = Column(String(36), ForeignKey("applicants.applicant_id"), nullable=False)
    classification = Column(
        Enum("approved", "rejected", "manual_review"),
        nullable=False,
    )
    risk_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    confidence_level = Column(Numeric(5, 2), nullable=False)  # 0-100
    decision_reasoning = Column(JSON, nullable=False)
    key_factors = Column(JSON, nullable=False)
    applicant_profile = Column(JSON)
    financial_risk_analysis = Column(JSON)
    decision_details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application = relationship("LoanApplication", back_populates="decision")
    applicant = relationship("Applicant", back_populates="decisions")

    __table_args__ = (
        Index("idx_case_id", "case_id"),
        Index("idx_application_id", "application_id"),
        Index("idx_applicant_id", "applicant_id"),
        Index("idx_classification", "classification"),
        Index("idx_created_at", "created_at"),
    )


class AuditLog(Base):
    """Comprehensive audit trail."""

    __tablename__ = "audit_logs"

    audit_id = Column(String(36), primary_key=True)
    case_id = Column(String(36))
    event_type = Column(String(50), nullable=False)
    event_description = Column(String(500))
    actor = Column(String(100))
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    old_value = Column(JSON)
    new_value = Column(JSON)
    status = Column(String(20))
    error_message = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)
    audit_metadata = Column(JSON)

    __table_args__ = (
        Index("idx_case_id", "case_id"),
        Index("idx_event_type", "event_type"),
        Index("idx_timestamp", "timestamp"),
        Index("idx_resource_id", "resource_id"),
    )


class Notification(Base):
    """Notification records."""

    __tablename__ = "notifications"

    notification_id = Column(String(36), primary_key=True)
    case_id = Column(String(36), nullable=False)
    applicant_id = Column(String(36), ForeignKey("applicants.applicant_id"), nullable=False)
    notification_type = Column(String(50), nullable=False)
    status = Column(
        Enum("pending", "sent", "failed"),
        default="pending",
    )
    message = Column(String(1000))
    recipient_details = Column(JSON)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applicant = relationship("Applicant")

    __table_args__ = (
        Index("idx_case_id", "case_id"),
        Index("idx_applicant_id", "applicant_id"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
    )
