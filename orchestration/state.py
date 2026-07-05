"""Workflow state definition."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class WorkflowState(BaseModel):
    """Loan approval workflow state."""

    # Input
    application_data: Dict[str, Any]
    application_id: str = ""

    # Intermediate outputs
    applicant_profile_output: Optional[Dict[str, Any]] = None
    financial_risk_output: Optional[Dict[str, Any]] = None
    decision_output: Optional[Dict[str, Any]] = None
    compliance_output: Optional[Dict[str, Any]] = None

    # Final result
    case_id: Optional[str] = None
    classification: Optional[str] = None
    risk_score: Optional[float] = None
    confidence_level: Optional[float] = None

    # Error tracking
    errors: List[str] = []

    # Audit trail
    audit_events: List[Dict[str, Any]] = []

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True
