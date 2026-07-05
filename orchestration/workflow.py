"""LangGraph workflow orchestration for loan approval."""

import logging
from typing import Any, Dict

from langgraph.graph import StateGraph
from pydantic import ValidationError

from agents.applicant_profile_agent import run_applicant_profile_agent
from agents.financial_risk_agent import run_financial_risk_agent
from agents.loan_decision_agent import run_loan_decision_agent
from agents.compliance_agent import run_compliance_agent
from utils.logging_config import get_logger
from utils.audit_trail import log_audit_event, AuditEvent
from orchestration.state import WorkflowState

logger = get_logger(__name__)


def validate_application(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate loan application data.

    Args:
        state: Workflow state (dict or Pydantic WorkflowState)

    Returns:
        Updated state
    """
    logger.info("Validating application data")

    # Convert Pydantic model to dict if needed
    if hasattr(state, "__dict__") and not isinstance(state, dict):
        state_dict = state.dict() if hasattr(state, "dict") else state.__dict__
    else:
        state_dict = state

    app_data = state_dict.get("application_data", {})

    # Check required fields
    required_fields = [
        "applicant_id",
        "age",
        "income",
        "employment_type",
        "credit_score",
        "loan_amount",
        "loan_tenure_months",
        "existing_liabilities",
    ]

    missing_fields = [f for f in required_fields if f not in app_data]

    if "errors" not in state_dict:
        state_dict["errors"] = []

    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        state_dict["errors"].append(error_msg)
        return state_dict

    # Validate value ranges
    if not (18 <= app_data.get("age", 0) <= 100):
        error_msg = "Age must be between 18 and 100"
        state_dict["errors"].append(error_msg)

    if app_data.get("income", 0) <= 0:
        error_msg = "Income must be positive"
        state_dict["errors"].append(error_msg)

    if app_data.get("credit_score", 0) < 300 or app_data.get("credit_score", 0) > 850:
        error_msg = "Credit score must be between 300 and 850"
        state_dict["errors"].append(error_msg)

    if app_data.get("loan_amount", 0) <= 0:
        error_msg = "Loan amount must be positive"
        state_dict["errors"].append(error_msg)

    if not state_dict["errors"]:
        log_audit_event(
            event_type=AuditEvent.APPLICATION_RECEIVED,
            resource_type="LoanApplication",
            resource_id=app_data.get("applicant_id"),
            description="Application validation successful",
            status="success",
        )
        logger.info("Application validation passed")
    else:
        log_audit_event(
            event_type=AuditEvent.ERROR_OCCURRED,
            resource_type="LoanApplication",
            resource_id=app_data.get("applicant_id"),
            description="Application validation failed",
            status="failure",
            error_message="; ".join(state_dict["errors"]),
        )

    return state_dict


def should_continue(state: Dict[str, Any]) -> str:
    """Determine if workflow should continue based on validation errors.

    Args:
        state: Workflow state (dict or Pydantic WorkflowState)

    Returns:
        "continue" or "end"
    """
    # Handle Pydantic model
    if hasattr(state, "__dict__") and not isinstance(state, dict):
        state_dict = state.dict() if hasattr(state, "dict") else state.__dict__
    else:
        state_dict = state

    if state_dict.get("errors"):
        return "end"
    return "continue"


def create_workflow():
    """Create the loan approval workflow.

    Returns:
        Compiled workflow graph
    """
    # Create state graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("validate", validate_application)
    workflow.add_node("applicant_profile", run_applicant_profile_agent)
    workflow.add_node("financial_risk", run_financial_risk_agent)
    workflow.add_node("loan_decision", run_loan_decision_agent)
    workflow.add_node("compliance", run_compliance_agent)

    # Add edges
    workflow.set_entry_point("validate")

    # Conditional routing after validation
    workflow.add_conditional_edges(
        "validate",
        should_continue,
        {
            "continue": "applicant_profile",
            "end": "compliance",
        },
    )

    # Linear flow for successful validation
    workflow.add_edge("applicant_profile", "financial_risk")
    workflow.add_edge("financial_risk", "loan_decision")
    workflow.add_edge("loan_decision", "compliance")

    # End point
    workflow.add_edge("compliance", "__end__")

    return workflow.compile()


# Global workflow instance
_workflow_instance = None


def get_workflow():
    """Get or create the compiled workflow.

    Returns:
        Compiled workflow graph
    """
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = create_workflow()
    return _workflow_instance


def run_workflow(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run the loan approval workflow.

    Args:
        application_data: Loan application data

    Returns:
        Workflow result
    """
    try:
        logger.info(
            f"Starting workflow for applicant {application_data.get('applicant_id')}"
        )

        # Initialize state
        state = WorkflowState(application_data=application_data)

        # Get workflow
        workflow = get_workflow()

        # Run workflow
        result = workflow.invoke(state.dict())

        logger.info(
            f"Workflow completed",
            extra={
                "applicant_id": application_data.get("applicant_id"),
                "case_id": result.get("case_id"),
                "classification": result.get("classification"),
            },
        )

        return result

    except ValidationError as e:
        logger.error(f"State validation error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "application_data": application_data,
        }

    except Exception as e:
        logger.error(f"Workflow error: {str(e)}")
        log_audit_event(
            event_type=AuditEvent.ERROR_OCCURRED,
            resource_type="Workflow",
            description=f"Workflow execution failed: {str(e)}",
            status="failure",
            error_message=str(e),
        )
        return {
            "success": False,
            "error": str(e),
            "application_data": application_data,
        }
