"""Pydantic models for request/response validation."""

from datetime import datetime
from typing import Any, List, Optional
from enum import Enum as PyEnum

from pydantic import BaseModel, Field, field_validator


class EmploymentType(str, PyEnum):
    """Employment type enumeration."""

    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"
    CONTRACT = "contract"
    RETIRED = "retired"


class Classification(str, PyEnum):
    """Loan classification types."""

    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


# ============================
# Request Models
# ============================


class LoanApplicationRequest(BaseModel):
    """Loan application request payload."""

    applicant_id: str = Field(..., description="Unique applicant identifier")
    age: int = Field(..., ge=18, le=100, description="Applicant age")
    income: float = Field(..., gt=0, description="Annual income in currency units")
    employment_type: EmploymentType = Field(..., description="Type of employment")
    employment_tenure_years: Optional[int] = Field(None, ge=0, description="Years in current employment")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score (FICO-like)")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    loan_tenure_months: int = Field(..., gt=0, description="Loan tenure in months")
    existing_liabilities: float = Field(..., ge=0, description="Total existing monthly liabilities")
    location: Optional[str] = Field(None, description="Applicant location")

    @field_validator("employment_tenure_years")
    @classmethod
    def validate_tenure(cls, v: Optional[int], info) -> Optional[int]:
        """Validate employment tenure."""
        if v is not None and v < 0:
            raise ValueError("Employment tenure must be non-negative")
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "applicant_id": "APP-001",
                "age": 35,
                "income": 75000.00,
                "employment_type": "salaried",
                "employment_tenure_years": 5,
                "credit_score": 720,
                "loan_amount": 300000.00,
                "loan_tenure_months": 360,
                "existing_liabilities": 2000.00,
                "location": "New York, NY",
            }
        }


# ============================
# Response Models
# ============================


class DecisionFactors(BaseModel):
    """Key factors influencing the decision."""

    factor: str = Field(..., description="Factor name")
    value: str = Field(..., description="Factor value/assessment")
    impact: str = Field(..., description="Impact level: positive, negative, or neutral")
    weight: float = Field(default=1.0, ge=0, le=1, description="Relative importance weight")


class DecisionReasoning(BaseModel):
    """Reasoning behind the decision."""

    summary: str = Field(..., description="High-level decision summary")
    applicant_profile_assessment: str = Field(..., description="Assessment of applicant profile")
    financial_risk_assessment: str = Field(..., description="Assessment of financial risk")
    decision_logic: str = Field(..., description="Logical path to decision")
    risk_mitigation_factors: Optional[List[str]] = Field(default=None, description="Risk mitigation considerations")


class LoanApplicationResponse(BaseModel):
    """Loan application response with decision."""

    case_id: str = Field(..., description="Unique case identifier for audit trail")
    classification: Classification = Field(..., description="Final classification")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    confidence_level: float = Field(..., ge=0, le=100, description="Decision confidence (0-100%)")
    key_decision_factors: List[DecisionFactors] = Field(..., description="Key factors in decision")
    explanation: DecisionReasoning = Field(..., description="Decision reasoning and explanation")
    applicant_profile: Optional[dict] = Field(None, description="Applicant profile analysis")
    financial_risk_analysis: Optional[dict] = Field(None, description="Financial risk analysis")
    next_steps: str = Field(..., description="Recommended next steps")
    created_at: datetime = Field(..., description="Decision timestamp")
    audit_trace_id: str = Field(..., description="Audit log reference ID")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for tracking")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================
# Internal Models (for agents)
# ============================


class ApplicantProfileOutput(BaseModel):
    """Output from Applicant Profile Agent."""

    income_stability_score: float = Field(..., ge=0, le=100)
    employment_risk_level: str = Field(...)  # low, medium, high
    credit_history_summary: str = Field(...)
    application_completeness_flags: List[str] = Field(default_factory=list)
    assessment_reasoning: str = Field(...)


class FinancialRiskOutput(BaseModel):
    """Output from Financial Risk Analysis Agent."""

    dti_ratio: float = Field(..., ge=0)
    credit_score_risk_level: str = Field(...)  # low, medium, high
    loan_amount_risk: str = Field(...)  # low, medium, high
    anomalies_detected: List[str] = Field(default_factory=list)
    risk_assessment_reasoning: str = Field(...)


class DecisionOutput(BaseModel):
    """Output from Loan Decision Agent."""

    classification: Classification = Field(...)
    risk_score: float = Field(..., ge=0, le=100)
    confidence_level: float = Field(..., ge=0, le=100)
    key_factors: List[DecisionFactors] = Field(...)
    reasoning: DecisionReasoning = Field(...)


class AuditTrailEntry(BaseModel):
    """Audit trail entry."""

    event_type: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: dict = Field(default_factory=dict)
    status: str = Field(default="success")
