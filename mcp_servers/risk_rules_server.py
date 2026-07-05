"""MCP Server for Risk Rules and Financial Risk Analysis."""

import json
import logging
from typing import Any, Dict, List

from fastmcp import FastMCP

from database.connection import DatabaseConnection
from database.models import RiskRule
from utils.validators import (
    calculate_dti_ratio,
    assess_credit_risk,
    detect_anomalies,
)

# Initialize MCP server
mcp = FastMCP("risk_rules_server", "1.0.0")
logger = logging.getLogger(__name__)


@mcp.tool()
def fetch_risk_rules() -> Dict[str, Any]:
    """Fetch active risk rules from database.

    Returns:
        Dictionary of active risk rules
    """
    try:
        session = DatabaseConnection.get_session()
        try:
            rules = (
                session.query(RiskRule)
                .filter(RiskRule.active == True)
                .all()
            )

            rules_dict = {}
            for rule in rules:
                rules_dict[rule.rule_type] = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "threshold_approve": float(rule.threshold_approve) if rule.threshold_approve else None,
                    "threshold_review": float(rule.threshold_review) if rule.threshold_review else None,
                    "description": rule.description,
                }

            return {
                "success": True,
                "rules": rules_dict,
            }

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching risk rules: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def calculate_dti_ratio_tool(
    monthly_income: float,
    total_liabilities: float,
    loan_amount: float,
    loan_tenure_months: int,
) -> Dict[str, Any]:
    """Calculate Debt-to-Income ratio.

    Args:
        monthly_income: Monthly income
        total_liabilities: Total monthly liabilities
        loan_amount: New loan amount
        loan_tenure_months: New loan tenure in months

    Returns:
        DTI ratio calculation result
    """
    try:
        dti = calculate_dti_ratio(
            monthly_income=monthly_income,
            total_liabilities=total_liabilities,
            loan_amount=loan_amount,
            loan_tenure_months=loan_tenure_months,
        )

        # Get thresholds
        session = DatabaseConnection.get_session()
        try:
            rule = (
                session.query(RiskRule)
                .filter(RiskRule.rule_type == "dti_ratio")
                .first()
            )
        finally:
            session.close()

        threshold_approve = float(rule.threshold_approve) if rule else 0.40
        threshold_review = float(rule.threshold_review) if rule else 0.50

        # Assess risk level
        if dti <= threshold_approve:
            risk_level = "low"
        elif dti <= threshold_review:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "success": True,
            "dti_ratio": round(dti, 4),
            "dti_percentage": round(dti * 100, 2),
            "dti_risk_level": risk_level,
            "threshold_approve": threshold_approve,
            "threshold_review": threshold_review,
            "monthly_income": monthly_income,
            "total_liabilities": total_liabilities,
            "new_loan_payment": (loan_amount / loan_tenure_months),
        }

    except Exception as e:
        logger.error(f"Error calculating DTI ratio: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def evaluate_credit_risk(credit_score: int) -> Dict[str, Any]:
    """Evaluate credit score risk.

    Args:
        credit_score: Credit score (300-850)

    Returns:
        Credit risk assessment
    """
    try:
        risk_level, risk_score = assess_credit_risk(credit_score)

        return {
            "success": True,
            "credit_score": credit_score,
            "credit_risk_level": risk_level,
            "credit_risk_score": risk_score,
            "assessment": f"Credit score of {credit_score} indicates {risk_level} credit risk",
        }

    except Exception as e:
        logger.error(f"Error evaluating credit risk: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def evaluate_loan_amount_risk(
    loan_amount: float,
    monthly_income: float,
) -> Dict[str, Any]:
    """Evaluate loan amount risk based on income ratio.

    Args:
        loan_amount: Loan amount
        monthly_income: Monthly income

    Returns:
        Loan amount risk assessment
    """
    try:
        annual_income = monthly_income * 12
        if annual_income <= 0:
            loan_to_income_ratio = 999.0
            risk_level = "very_high"
        else:
            loan_to_income_ratio = loan_amount / annual_income

            if loan_to_income_ratio <= 3.0:
                risk_level = "low"
            elif loan_to_income_ratio <= 4.0:
                risk_level = "medium"
            elif loan_to_income_ratio <= 5.0:
                risk_level = "high"
            else:
                risk_level = "very_high"

        return {
            "success": True,
            "loan_amount": loan_amount,
            "annual_income": annual_income,
            "loan_to_income_ratio": round(loan_to_income_ratio, 2),
            "loan_amount_risk_level": risk_level,
            "assessment": f"Loan-to-income ratio of {loan_to_income_ratio:.2f}x indicates {risk_level} risk",
        }

    except Exception as e:
        logger.error(f"Error evaluating loan amount risk: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def detect_anomalies_tool(
    loan_amount: float,
    monthly_income: float,
    dti_ratio: float,
    credit_score: int,
    employment_tenure_years: int = 0,
) -> Dict[str, Any]:
    """Detect anomalies in loan application.

    Args:
        loan_amount: Loan amount
        monthly_income: Monthly income
        dti_ratio: DTI ratio
        credit_score: Credit score
        employment_tenure_years: Years in employment

    Returns:
        List of detected anomalies
    """
    try:
        anomalies = detect_anomalies(
            loan_amount=loan_amount,
            monthly_income=monthly_income,
            dti_ratio=dti_ratio,
        )

        # Additional anomaly checks
        if credit_score < 550:
            anomalies.append(f"Very low credit score ({credit_score})")

        if employment_tenure_years == 0:
            anomalies.append("No employment tenure information provided")

        if monthly_income <= 0:
            anomalies.append("Invalid or missing income information")

        risk_level = "low"
        if len(anomalies) >= 3:
            risk_level = "high"
        elif len(anomalies) >= 1:
            risk_level = "medium"

        return {
            "success": True,
            "anomalies_detected": anomalies,
            "anomaly_count": len(anomalies),
            "anomaly_risk_level": risk_level,
            "requires_review": len(anomalies) >= 2,
        }

    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


async def start_server(port: int = 3002):
    """Start the MCP server."""
    logger.info(f"Starting RiskRulesDB MCP Server on port {port}")
    await mcp.run(port)


if __name__ == "__main__":
    import asyncio

    asyncio.run(start_server())
