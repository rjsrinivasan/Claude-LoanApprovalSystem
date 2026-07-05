"""FastAPI request and response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class EmploymentType(str, Enum):
    """Employment type enumeration."""

    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"
    CONTRACT = "contract"
    RETIRED = "retired"


class Classification(str, Enum):
    """Loan classification."""

    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class LoanApplicationRequest(BaseModel):
    """Loan application request."""

    applicant_id: str = Field(..., description="Unique applicant identifier")
    age: int = Field(..., ge=18, le=100, description="Applicant age")
    income: float = Field(..., gt=0, description="Annual income")
    employment_type: EmploymentType = Field(..., description="Type of employment")
    employment_tenure_years: Optional[int] = Field(None, ge=0, description="Years in employment")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")
    loan_amount: float = Field(..., gt=0, description="Loan amount requested")
    loan_tenure_months: int = Field(..., gt=0, description="Loan tenure in months")
    existing_liabilities: float = Field(..., ge=0, description="Monthly liabilities")
    location: Optional[str] = Field(None, description="Applicant location")

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


class DecisionFactor(BaseModel):
    """Decision factor."""

    factor: str = Field(..., description="Factor name")
    value: str = Field(..., description="Factor value")
    impact: str = Field(..., description="Impact level")
    weight: float = Field(default=1.0, description="Factor weight")


class DecisionReasoning(BaseModel):
    """Decision reasoning."""

    summary: str = Field(..., description="Decision summary")
    applicant_profile_assessment: str = Field(..., description="Applicant assessment")
    financial_risk_assessment: str = Field(..., description="Financial risk assessment")
    decision_logic: str = Field(..., description="Decision logic")
    risk_mitigation_factors: Optional[List[str]] = Field(None, description="Risk mitigation")


class LoanApplicationResponse(BaseModel):
    """Loan application response."""

    case_id: str = Field(..., description="Unique case identifier")
    classification: Classification = Field(..., description="Decision classification")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score")
    confidence_level: float = Field(..., ge=0, le=100, description="Confidence level")
    key_decision_factors: List[DecisionFactor] = Field(..., description="Key factors")
    explanation: DecisionReasoning = Field(..., description="Decision explanation")
    next_steps: str = Field(..., description="Recommended next steps")
    created_at: datetime = Field(..., description="Decision timestamp")
    audit_trace_id: str = Field(..., description="Audit log reference")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database_connected: bool = Field(..., description="Database connection status")
