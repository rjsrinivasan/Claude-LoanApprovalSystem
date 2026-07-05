"""MCP Server for Applicant Database operations."""

import json
import logging
from typing import Any, Dict

from fastmcp import FastMCP
from sqlalchemy import or_

from database.connection import DatabaseConnection
from database.models import Applicant, LoanApplication
from utils.audit_trail import log_audit_event, AuditEvent
from utils.validators import assess_income_stability

# Initialize MCP server
mcp = FastMCP("applicant_db_server", "1.0.0")
logger = logging.getLogger(__name__)


@mcp.tool()
def get_applicant_info(applicant_id: str) -> Dict[str, Any]:
    """Fetch applicant profile information from database.

    Args:
        applicant_id: Unique applicant identifier

    Returns:
        Applicant profile information or error
    """
    try:
        session = DatabaseConnection.get_session()
        try:
            applicant = session.query(Applicant).filter(
                Applicant.applicant_id == applicant_id
            ).first()

            if not applicant:
                return {
                    "success": False,
                    "error": f"Applicant {applicant_id} not found",
                }

            return {
                "success": True,
                "data": {
                    "applicant_id": applicant.applicant_id,
                    "age": applicant.age,
                    "income": float(applicant.income),
                    "employment_type": applicant.employment_type,
                    "employment_tenure_years": applicant.employment_tenure_years,
                    "location": applicant.location,
                },
            }
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching applicant info: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def analyze_employment_risk(
    employment_type: str,
    employment_tenure_years: int = 0,
) -> Dict[str, Any]:
    """Analyze employment risk based on job characteristics.

    Args:
        employment_type: Type of employment
        employment_tenure_years: Years in current employment

    Returns:
        Employment risk assessment
    """
    try:
        # Employment type risk mapping
        risk_levels = {
            "salaried": "low",
            "contract": "medium",
            "self_employed": "high",
            "retired": "low",
        }

        base_risk = risk_levels.get(employment_type, "medium")

        # Adjust risk based on tenure
        if employment_type == "salaried":
            if employment_tenure_years >= 5:
                final_risk = "low"
            elif employment_tenure_years >= 2:
                final_risk = "low_medium"
            else:
                final_risk = "medium"
        elif employment_type == "contract":
            if employment_tenure_years >= 3:
                final_risk = "low_medium"
            else:
                final_risk = "medium"
        elif employment_type == "self_employed":
            if employment_tenure_years >= 5:
                final_risk = "medium"
            else:
                final_risk = "high"
        else:
            final_risk = base_risk

        return {
            "success": True,
            "employment_type": employment_type,
            "tenure_years": employment_tenure_years,
            "employment_risk_level": final_risk,
            "reasoning": f"Employment type: {employment_type}, Tenure: {employment_tenure_years} years",
        }

    except Exception as e:
        logger.error(f"Error analyzing employment risk: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def check_application_completeness(applicant_id: str) -> Dict[str, Any]:
    """Check if application has all required information.

    Args:
        applicant_id: Applicant ID

    Returns:
        Completeness assessment
    """
    try:
        session = DatabaseConnection.get_session()
        try:
            applicant = session.query(Applicant).filter(
                Applicant.applicant_id == applicant_id
            ).first()

            if not applicant:
                return {
                    "success": True,
                    "is_complete": False,
                    "missing_fields": ["applicant_not_found"],
                }

            missing_fields = []

            if not applicant.age:
                missing_fields.append("age")
            if not applicant.income:
                missing_fields.append("income")
            if not applicant.employment_type:
                missing_fields.append("employment_type")
            if not applicant.location:
                missing_fields.append("location")

            return {
                "success": True,
                "is_complete": len(missing_fields) == 0,
                "missing_fields": missing_fields,
                "completeness_percentage": ((5 - len(missing_fields)) / 5) * 100,
            }

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error checking application completeness: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def analyze_income_stability(
    applicant_id: str,
    employment_type: str,
    employment_tenure_years: int = 0,
) -> Dict[str, Any]:
    """Analyze income stability for the applicant.

    Args:
        applicant_id: Applicant ID
        employment_type: Type of employment
        employment_tenure_years: Years in current employment

    Returns:
        Income stability assessment
    """
    try:
        stability_level, stability_score = assess_income_stability(
            employment_type=employment_type,
            employment_tenure_years=employment_tenure_years,
        )

        return {
            "success": True,
            "applicant_id": applicant_id,
            "income_stability_level": stability_level,
            "income_stability_score": stability_score,
            "assessment": f"Income stability is {stability_level} based on {employment_type} employment with {employment_tenure_years} years tenure",
        }

    except Exception as e:
        logger.error(f"Error analyzing income stability: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def get_credit_history(applicant_id: str) -> Dict[str, Any]:
    """Get credit history summary for applicant.

    Args:
        applicant_id: Applicant ID

    Returns:
        Credit history summary (if available)
    """
    try:
        session = DatabaseConnection.get_session()
        try:
            # Find all applications for this applicant
            applications = (
                session.query(LoanApplication)
                .filter(LoanApplication.applicant_id == applicant_id)
                .order_by(LoanApplication.created_at.desc())
                .all()
            )

            if not applications:
                return {
                    "success": True,
                    "applicant_id": applicant_id,
                    "application_count": 0,
                    "summary": "No previous applications found",
                }

            avg_credit_score = sum(a.credit_score for a in applications) / len(applications)

            return {
                "success": True,
                "applicant_id": applicant_id,
                "application_count": len(applications),
                "average_credit_score": avg_credit_score,
                "most_recent_credit_score": applications[0].credit_score,
                "summary": f"{len(applications)} previous application(s) on record",
            }

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error getting credit history: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


async def start_server(port: int = 3001):
    """Start the MCP server."""
    logger.info(f"Starting ApplicantDB MCP Server on port {port}")
    await mcp.run(port)


if __name__ == "__main__":
    import asyncio

    asyncio.run(start_server())
