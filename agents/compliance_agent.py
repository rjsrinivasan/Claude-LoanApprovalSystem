"""Compliance & Action Orchestrator Agent - Handles decision persistence and notifications."""

import logging
import uuid
from typing import Any, Dict

from utils.logging_config import get_logger
from utils.audit_trail import log_audit_event, AuditEvent
from database.connection import DatabaseConnection
from database.models import LoanApplication, Notification

logger = get_logger(__name__)


class ComplianceAgent:
    """Agent for compliance, persistence, and notification operations."""

    def __init__(self):
        """Initialize the agent."""
        pass

    def persist_decision(
        self,
        application_id: str,
        applicant_id: str,
        classification: str,
        risk_score: float,
        confidence_level: float,
        decision_reasoning: Dict[str, Any],
        key_factors: list,
        applicant_profile: Dict[str, Any] = None,
        financial_risk_analysis: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Persist decision to database and generate case ID.

        Args:
            application_id: Application ID
            applicant_id: Applicant ID
            classification: Decision classification
            risk_score: Risk score (0-100)
            confidence_level: Confidence level (0-100)
            decision_reasoning: JSON reasoning
            key_factors: List of key factors
            applicant_profile: Applicant profile data
            financial_risk_analysis: Financial risk analysis data

        Returns:
            Dictionary with case ID and persistence status
        """
        try:
            case_id = f"CASE_{uuid.uuid4().hex[:12].upper()}"

            # Import here to avoid circular imports
            from database.models import LoanDecision

            session = DatabaseConnection.get_session()
            try:
                # Create decision record
                decision = LoanDecision(
                    case_id=case_id,
                    application_id=application_id,
                    applicant_id=applicant_id,
                    classification=classification,
                    risk_score=risk_score,
                    confidence_level=confidence_level,
                    decision_reasoning=decision_reasoning,
                    key_factors=key_factors,
                    applicant_profile=applicant_profile,
                    financial_risk_analysis=financial_risk_analysis,
                    decision_details={
                        "classification": classification,
                        "risk_score": risk_score,
                        "confidence_level": confidence_level,
                    },
                )

                session.add(decision)

                # Update application status
                app = session.query(LoanApplication).filter(
                    LoanApplication.application_id == application_id
                ).first()
                if app:
                    app.status = "completed"

                session.commit()

                logger.info(
                    f"Decision persisted successfully",
                    extra={
                        "case_id": case_id,
                        "classification": classification,
                    },
                )

                # Log audit event
                log_audit_event(
                    event_type=AuditEvent.DECISION_PERSISTED,
                    case_id=case_id,
                    resource_type="LoanDecision",
                    resource_id=case_id,
                    description=f"Decision {classification} persisted to database",
                    status="success",
                    metadata={
                        "classification": classification,
                        "risk_score": risk_score,
                        "confidence_level": confidence_level,
                    },
                )

                return {
                    "success": True,
                    "case_id": case_id,
                    "message": "Decision persisted successfully",
                }

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error persisting decision: {str(e)}")
            log_audit_event(
                event_type=AuditEvent.ERROR_OCCURRED,
                resource_type="LoanDecision",
                description=f"Failed to persist decision: {str(e)}",
                status="failure",
                error_message=str(e),
            )
            raise

    def create_notification(
        self,
        case_id: str,
        applicant_id: str,
        classification: str,
    ) -> Dict[str, Any]:
        """Create notification record.

        Args:
            case_id: Case ID
            applicant_id: Applicant ID
            classification: Decision classification

        Returns:
            Notification creation status
        """
        try:
            notification_id = f"NOTIF_{uuid.uuid4().hex[:12]}"

            # Determine notification message
            if classification == "approved":
                notification_type = "approval"
                message = f"Your loan application (Case ID: {case_id}) has been APPROVED. Congratulations!"
            elif classification == "rejected":
                notification_type = "rejection"
                message = f"Your loan application (Case ID: {case_id}) has been REJECTED. Please contact us for details."
            else:
                notification_type = "review"
                message = f"Your loan application (Case ID: {case_id}) requires manual review. We will contact you soon."

            session = DatabaseConnection.get_session()
            try:
                notification = Notification(
                    notification_id=notification_id,
                    case_id=case_id,
                    applicant_id=applicant_id,
                    notification_type=notification_type,
                    status="pending",
                    message=message,
                    recipient_details={},
                )

                session.add(notification)
                session.commit()

                logger.info(
                    f"Notification created",
                    extra={
                        "notification_id": notification_id,
                        "case_id": case_id,
                    },
                )

                # Log audit event
                log_audit_event(
                    event_type=AuditEvent.NOTIFICATION_SENT,
                    case_id=case_id,
                    resource_type="Notification",
                    resource_id=notification_id,
                    description=f"Notification created for {notification_type}",
                    status="success",
                )

                return {
                    "success": True,
                    "notification_id": notification_id,
                    "notification_type": notification_type,
                    "message": message,
                }

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }


def run_compliance_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the compliance agent as a workflow node.

    Args:
        state: Workflow state (dict or Pydantic WorkflowState)

    Returns:
        Updated state with compliance actions completed
    """
    # Handle Pydantic model
    if hasattr(state, "__dict__") and not isinstance(state, dict):
        state = state.dict() if hasattr(state, "dict") else state.__dict__

    agent = ComplianceAgent()

    app_data = state.get("application_data", {})
    decision = state.get("decision_output", {})

    # Persist decision
    persistence_result = agent.persist_decision(
        application_id=app_data.get("application_id"),
        applicant_id=app_data.get("applicant_id"),
        classification=decision.get("classification"),
        risk_score=decision.get("risk_score"),
        confidence_level=decision.get("confidence_level"),
        decision_reasoning=decision.get("reasoning", {}),
        key_factors=decision.get("key_factors", []),
        applicant_profile=state.get("applicant_profile_output"),
        financial_risk_analysis=state.get("financial_risk_output"),
    )

    if persistence_result.get("success"):
        case_id = persistence_result.get("case_id")

        # Create notification
        notification_result = agent.create_notification(
            case_id=case_id,
            applicant_id=app_data.get("applicant_id"),
            classification=decision.get("classification"),
        )

        state["compliance_output"] = {
            "case_id": case_id,
            "persistence_status": "success",
            "notification_status": "pending" if notification_result.get("success") else "failed",
            "notification_id": notification_result.get("notification_id"),
        }

        state["case_id"] = case_id

    else:
        state["compliance_output"] = {
            "case_id": None,
            "persistence_status": "failed",
            "notification_status": "skipped",
            "error": persistence_result.get("error"),
        }

    return state
