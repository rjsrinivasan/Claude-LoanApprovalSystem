"""FastAPI route handlers."""

import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from api.models import LoanApplicationRequest, LoanApplicationResponse, DecisionFactor, DecisionReasoning
from database.connection import DatabaseConnection
from database.models import LoanApplication, Applicant
from orchestration.workflow import run_workflow
from utils.audit_trail import log_audit_event, AuditEvent, get_audit_summary
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["loan-applications"])


@router.post(
    "/loan-applications",
    response_model=LoanApplicationResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": Dict}, 500: {"model": Dict}},
)
async def submit_loan_application(
    request: LoanApplicationRequest,
) -> LoanApplicationResponse:
    """Submit a loan application for processing.

    Args:
        request: Loan application request

    Returns:
        LoanApplicationResponse with decision

    Raises:
        HTTPException: On validation or processing errors
    """
    try:
        # Generate IDs
        application_id = f"APP_{uuid.uuid4().hex[:12]}"
        audit_id = log_audit_event(
            event_type=AuditEvent.APPLICATION_RECEIVED,
            resource_type="LoanApplication",
            resource_id=application_id,
            description=f"Application received for {request.applicant_id}",
            status="success",
            metadata={
                "applicant_id": request.applicant_id,
                "loan_amount": request.loan_amount,
            },
        )

        logger.info(
            f"Processing loan application",
            extra={
                "application_id": application_id,
                "applicant_id": request.applicant_id,
            },
        )

        # Save application to database
        session = DatabaseConnection.get_session()
        try:
            # Upsert applicant
            applicant = session.query(Applicant).filter(
                Applicant.applicant_id == request.applicant_id
            ).first()

            if not applicant:
                applicant = Applicant(
                    applicant_id=request.applicant_id,
                    age=request.age,
                    income=request.income,
                    employment_type=request.employment_type.value,
                    employment_tenure_years=request.employment_tenure_years,
                    location=request.location,
                )
                session.add(applicant)
            else:
                applicant.age = request.age
                applicant.income = request.income
                applicant.employment_type = request.employment_type.value
                applicant.employment_tenure_years = request.employment_tenure_years
                applicant.location = request.location

            # Create application record
            application = LoanApplication(
                application_id=application_id,
                applicant_id=request.applicant_id,
                credit_score=request.credit_score,
                loan_amount=request.loan_amount,
                loan_tenure_months=request.loan_tenure_months,
                existing_liabilities=request.existing_liabilities,
                status="processing",
            )
            session.add(application)
            session.commit()

        finally:
            session.close()

        # Run workflow
        workflow_input = {
            "application_id": application_id,
            "applicant_id": request.applicant_id,
            "age": request.age,
            "income": request.income,
            "employment_type": request.employment_type.value,
            "employment_tenure_years": request.employment_tenure_years or 0,
            "credit_score": request.credit_score,
            "loan_amount": request.loan_amount,
            "loan_tenure_months": request.loan_tenure_months,
            "existing_liabilities": request.existing_liabilities,
            "location": request.location,
        }

        workflow_result = run_workflow(workflow_input)

        # Handle workflow errors
        if workflow_result.get("errors"):
            logger.error(
                f"Workflow validation errors",
                extra={
                    "application_id": application_id,
                    "errors": workflow_result.get("errors"),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Application validation failed",
                    "details": workflow_result.get("errors"),
                },
            )

        # Extract decision
        decision_output = workflow_result.get("decision_output", {})
        compliance_output = workflow_result.get("compliance_output", {})

        if not decision_output:
            logger.error(
                "No decision output from workflow",
                extra={"application_id": application_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Decision processing failed",
            )

        # Build response
        case_id = compliance_output.get("case_id", f"CASE_{uuid.uuid4().hex[:8]}")

        # Convert key factors
        key_factors = []
        for kf in decision_output.get("key_factors", []):
            if isinstance(kf, dict):
                key_factors.append(
                    DecisionFactor(
                        factor=kf.get("factor", ""),
                        value=kf.get("value", ""),
                        impact=kf.get("impact", "neutral"),
                        weight=kf.get("weight", 1.0),
                    )
                )

        # Build reasoning
        reasoning_data = decision_output.get("reasoning", {})
        if isinstance(reasoning_data, dict):
            reasoning = DecisionReasoning(
                summary=reasoning_data.get("summary", "Decision made"),
                applicant_profile_assessment=reasoning_data.get(
                    "applicant_profile_assessment", ""
                ),
                financial_risk_assessment=reasoning_data.get(
                    "financial_risk_assessment", ""
                ),
                decision_logic=reasoning_data.get("decision_logic", ""),
                risk_mitigation_factors=reasoning_data.get(
                    "risk_mitigation_factors", []
                ),
            )
        else:
            reasoning = DecisionReasoning(
                summary="Decision made",
                applicant_profile_assessment="",
                financial_risk_assessment="",
                decision_logic="",
            )

        # Determine next steps
        classification = decision_output.get("classification", "manual_review")
        if classification == "approved":
            next_steps = "Application approved. Proceed with loan origination."
        elif classification == "rejected":
            next_steps = "Application rejected. Applicant will be notified."
        else:
            next_steps = "Application requires manual review by underwriting team."

        response = LoanApplicationResponse(
            case_id=case_id,
            classification=classification,
            risk_score=decision_output.get("risk_score", 50),
            confidence_level=decision_output.get("confidence_level", 50),
            key_decision_factors=key_factors,
            explanation=reasoning,
            next_steps=next_steps,
            created_at=datetime.utcnow(),
            audit_trace_id=audit_id,
        )

        logger.info(
            f"Application processed successfully",
            extra={
                "application_id": application_id,
                "case_id": case_id,
                "classification": classification,
            },
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error processing loan application: {str(e)}",
            extra={"error": str(e)},
        )
        log_audit_event(
            event_type=AuditEvent.ERROR_OCCURRED,
            resource_type="LoanApplication",
            description=f"Application processing failed: {str(e)}",
            status="failure",
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application processing failed",
        )


@router.get(
    "/loan-applications/{case_id}",
    status_code=status.HTTP_200_OK,
)
async def get_application_status(case_id: str) -> Dict[str, Any]:
    """Get loan application status by case ID.

    Args:
        case_id: Case ID

    Returns:
        Application status and decision

    Raises:
        HTTPException: If case not found
    """
    try:
        session = DatabaseConnection.get_session()
        try:
            from database.models import LoanDecision

            decision = session.query(LoanDecision).filter(
                LoanDecision.case_id == case_id
            ).first()

            if not decision:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Case {case_id} not found",
                )

            # Get audit summary
            audit_summary = get_audit_summary(case_id)

            return {
                "case_id": case_id,
                "classification": decision.classification,
                "risk_score": float(decision.risk_score),
                "confidence_level": float(decision.confidence_level),
                "created_at": decision.created_at.isoformat() if decision.created_at else None,
                "audit_summary": audit_summary,
            }

        finally:
            session.close()

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error retrieving case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve case",
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status
    """
    try:
        db_connected = DatabaseConnection.health_check()

        return {
            "status": "healthy" if db_connected else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database_connected": db_connected,
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database_connected": False,
            "error": str(e),
        }
