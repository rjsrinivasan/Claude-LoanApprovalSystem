"""Audit trail logging utilities."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from database.connection import DatabaseConnection
from database.models import AuditLog
from utils.logging_config import get_logger

logger = get_logger(__name__)


class AuditEvent:
    """Audit event types."""

    APPLICATION_RECEIVED = "APPLICATION_RECEIVED"
    APPLICANT_PROFILE_RETRIEVED = "APPLICANT_PROFILE_RETRIEVED"
    FINANCIAL_RISK_ANALYZED = "FINANCIAL_RISK_ANALYZED"
    DECISION_SYNTHESIZED = "DECISION_SYNTHESIZED"
    DECISION_MADE = "DECISION_MADE"
    DECISION_PERSISTED = "DECISION_PERSISTED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"


def log_audit_event(
    event_type: str,
    case_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    status: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    actor: str = "system",
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
) -> str:
    """Log an audit event to the database.

    Args:
        event_type: Type of event
        case_id: Case ID for traceability
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        description: Event description
        status: Event status (success, failure, pending)
        metadata: Additional metadata
        error_message: Error message if applicable
        actor: Who/what triggered the event
        old_value: Previous value (for updates)
        new_value: New value (for updates)

    Returns:
        audit_id: ID of the audit log entry
    """
    try:
        audit_id = f"audit_{uuid.uuid4().hex[:12]}"

        audit_entry = AuditLog(
            audit_id=audit_id,
            case_id=case_id,
            event_type=event_type,
            event_description=description,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            status=status,
            error_message=error_message,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        session = DatabaseConnection.get_session()
        try:
            session.add(audit_entry)
            session.commit()
            logger.info(
                f"Audit event logged",
                extra={
                    "audit_id": audit_id,
                    "event_type": event_type,
                    "case_id": case_id,
                    "status": status,
                },
            )
            return audit_id
        finally:
            session.close()

    except Exception as e:
        logger.error(
            f"Failed to log audit event: {str(e)}",
            extra={
                "event_type": event_type,
                "case_id": case_id,
            },
        )
        raise


def get_audit_trail(case_id: str) -> list:
    """Retrieve audit trail for a case.

    Args:
        case_id: Case ID to retrieve audit trail for

    Returns:
        List of audit events
    """
    try:
        session = DatabaseConnection.get_session()
        try:
            events = (
                session.query(AuditLog)
                .filter(AuditLog.case_id == case_id)
                .order_by(AuditLog.timestamp.asc())
                .all()
            )

            return [
                {
                    "audit_id": e.audit_id,
                    "event_type": e.event_type,
                    "description": e.event_description,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "status": e.status,
                    "actor": e.actor,
                }
                for e in events
            ]
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to retrieve audit trail: {str(e)}")
        return []


def get_audit_summary(case_id: str) -> Dict[str, Any]:
    """Get a summary of the audit trail for a case.

    Args:
        case_id: Case ID

    Returns:
        Audit summary
    """
    try:
        audit_events = get_audit_trail(case_id)

        if not audit_events:
            return {
                "case_id": case_id,
                "total_events": 0,
                "timeline": [],
                "summary": "No audit events found",
            }

        return {
            "case_id": case_id,
            "total_events": len(audit_events),
            "first_event": audit_events[0]["timestamp"],
            "last_event": audit_events[-1]["timestamp"],
            "event_types": list(set(e["event_type"] for e in audit_events)),
            "status_distribution": {
                status: len([e for e in audit_events if e["status"] == status])
                for status in set(e["status"] for e in audit_events)
            },
            "timeline": audit_events,
        }
    except Exception as e:
        logger.error(f"Failed to generate audit summary: {str(e)}")
        return {"case_id": case_id, "error": str(e)}
