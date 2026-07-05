"""MCP Server for Notification System and Decision Persistence."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from fastmcp import FastMCP

from database.connection import DatabaseConnection
from database.models import LoanDecision, AuditLog, Notification
from utils.audit_trail import log_audit_event, AuditEvent

# Initialize MCP server
mcp = FastMCP("notification_system_server", "1.0.0")
logger = logging.getLogger(__name__)


@mcp.tool()
def persist_decision(
    application_id: str,
    applicant_id: str,
    classification: str,
    risk_score: float,
    confidence_level: float,
    decision_reasoning: Dict[str, Any],
    key_factors: list,
    applicant_profile: Dict[str, Any] = None,
    financial_risk_analysis: Dict[str, Any] = None,
    decision_details: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Persist loan decision to database.

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
        decision_details: Additional decision details

    Returns:
        Persisted decision with case ID
    """
    try:
        case_id = f"CASE_{uuid.uuid4().hex[:12].upper()}"

        session = DatabaseConnection.get_session()
        try:
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
                decision_details=decision_details,
            )

            session.add(decision)
            session.commit()

            logger.info(
                f"Decision persisted",
                extra={
                    "case_id": case_id,
                    "application_id": application_id,
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
                "message": f"Decision persisted successfully",
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
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def generate_case_id() -> Dict[str, Any]:
    """Generate a unique case ID.

    Returns:
        Generated case ID
    """
    try:
        case_id = f"CASE_{uuid.uuid4().hex[:12].upper()}"
        return {
            "success": True,
            "case_id": case_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error generating case ID: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def log_audit_trail(
    case_id: str,
    event_type: str,
    resource_type: str = "LoanDecision",
    description: str = "",
    metadata: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Log an audit trail event.

    Args:
        case_id: Case ID for traceability
        event_type: Type of event
        resource_type: Type of resource affected
        description: Event description
        metadata: Additional metadata

    Returns:
        Audit log entry
    """
    try:
        audit_id = log_audit_event(
            event_type=event_type,
            case_id=case_id,
            resource_type=resource_type,
            description=description,
            status="success",
            metadata=metadata or {},
        )

        return {
            "success": True,
            "audit_id": audit_id,
            "case_id": case_id,
            "event_type": event_type,
        }

    except Exception as e:
        logger.error(f"Error logging audit trail: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def trigger_notification(
    case_id: str,
    applicant_id: str,
    classification: str,
    recipient_details: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Trigger notification for decision.

    Args:
        case_id: Case ID
        applicant_id: Applicant ID
        classification: Decision classification
        recipient_details: Recipient contact information

    Returns:
        Notification record
    """
    try:
        notification_id = f"NOTIF_{uuid.uuid4().hex[:12]}"

        # Determine notification type and message
        if classification == "approved":
            notification_type = "approval"
            message = f"Your loan application (Case ID: {case_id}) has been APPROVED. Congratulations!"
        elif classification == "rejected":
            notification_type = "rejection"
            message = f"Your loan application (Case ID: {case_id}) has been REJECTED."
        else:
            notification_type = "review"
            message = f"Your loan application (Case ID: {case_id}) requires manual review."

        session = DatabaseConnection.get_session()
        try:
            notification = Notification(
                notification_id=notification_id,
                case_id=case_id,
                applicant_id=applicant_id,
                notification_type=notification_type,
                status="pending",
                message=message,
                recipient_details=recipient_details or {},
            )

            session.add(notification)
            session.commit()

            logger.info(
                f"Notification created",
                extra={
                    "notification_id": notification_id,
                    "case_id": case_id,
                    "type": notification_type,
                },
            )

            return {
                "success": True,
                "notification_id": notification_id,
                "case_id": case_id,
                "notification_type": notification_type,
                "status": "pending",
                "message": message,
            }

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error triggering notification: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def get_decision_summary(case_id: str) -> Dict[str, Any]:
    """Get a summary of the decision for a case.

    Args:
        case_id: Case ID

    Returns:
        Decision summary
    """
    try:
        session = DatabaseConnection.get_session()
        try:
            decision = (
                session.query(LoanDecision)
                .filter(LoanDecision.case_id == case_id)
                .first()
            )

            if not decision:
                return {
                    "success": False,
                    "error": f"Decision not found for case {case_id}",
                }

            return {
                "success": True,
                "case_id": case_id,
                "classification": decision.classification,
                "risk_score": float(decision.risk_score),
                "confidence_level": float(decision.confidence_level),
                "created_at": decision.created_at.isoformat() if decision.created_at else None,
            }

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error getting decision summary: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


async def start_server(port: int = 3004):
    """Start the MCP server."""
    logger.info(f"Starting NotificationSystem MCP Server on port {port}")
    await mcp.run(port)


if __name__ == "__main__":
    import asyncio

    asyncio.run(start_server())
