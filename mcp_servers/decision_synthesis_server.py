"""MCP Server for Decision Synthesis."""

import json
import logging
from typing import Any, Dict, List

from fastmcp import FastMCP

from database.connection import DatabaseConnection
from database.models import RiskRule

# Initialize MCP server
mcp = FastMCP("decision_synthesis_server", "1.0.0")
logger = logging.getLogger(__name__)


@mcp.tool()
def synthesize_decision_inputs(
    applicant_profile: Dict[str, Any],
    financial_risk: Dict[str, Any],
) -> Dict[str, Any]:
    """Synthesize applicant profile and financial risk analysis.

    Args:
        applicant_profile: Output from applicant profile agent
        financial_risk: Output from financial risk agent

    Returns:
        Consolidated decision inputs
    """
    try:
        return {
            "success": True,
            "consolidated_data": {
                "applicant_profile": applicant_profile,
                "financial_risk": financial_risk,
                "synthesis_timestamp": str(__import__("datetime").datetime.utcnow()),
            },
        }
    except Exception as e:
        logger.error(f"Error synthesizing decision inputs: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def apply_decision_thresholds(
    income_stability_score: float,
    employment_risk_level: str,
    credit_score: int,
    dti_ratio: float,
    anomalies: List[str],
) -> Dict[str, Any]:
    """Apply business rule thresholds to determine classification.

    Args:
        income_stability_score: Income stability (0-1)
        employment_risk_level: Employment risk level
        credit_score: Credit score
        dti_ratio: DTI ratio
        anomalies: List of detected anomalies

    Returns:
        Preliminary classification based on thresholds
    """
    try:
        # Get decision thresholds from database
        session = DatabaseConnection.get_session()
        try:
            credit_rule = (
                session.query(RiskRule)
                .filter(RiskRule.rule_type == "credit_score")
                .first()
            )
            dti_rule = (
                session.query(RiskRule)
                .filter(RiskRule.rule_type == "dti_ratio")
                .first()
            )
        finally:
            session.close()

        min_credit_approve = int(credit_rule.threshold_approve) if credit_rule else 650
        min_credit_review = int(credit_rule.threshold_review) if credit_rule else 550
        max_dti_approve = float(dti_rule.threshold_approve) if dti_rule else 0.40
        max_dti_review = float(dti_rule.threshold_review) if dti_rule else 0.50

        # Assess signals
        approval_signals = 0
        concern_signals = 0

        # Credit score signal
        if credit_score >= min_credit_approve:
            approval_signals += 1
        elif credit_score < min_credit_review:
            concern_signals += 2

        # DTI ratio signal
        if dti_ratio <= max_dti_approve:
            approval_signals += 1
        elif dti_ratio > max_dti_review:
            concern_signals += 2

        # Income stability signal
        if income_stability_score >= 0.75:
            approval_signals += 1
        elif income_stability_score < 0.60:
            concern_signals += 1

        # Employment risk signal
        if employment_risk_level == "low":
            approval_signals += 1
        elif employment_risk_level == "high":
            concern_signals += 1

        # Anomaly signal
        if len(anomalies) > 0:
            concern_signals += len(anomalies)

        # Determine preliminary classification
        if concern_signals >= 3:
            preliminary_classification = "rejected"
            preliminary_risk_score = 75.0
        elif concern_signals >= 1:
            preliminary_classification = "manual_review"
            preliminary_risk_score = 55.0
        elif approval_signals >= 3:
            preliminary_classification = "approved"
            preliminary_risk_score = 25.0
        else:
            preliminary_classification = "manual_review"
            preliminary_risk_score = 50.0

        return {
            "success": True,
            "preliminary_classification": preliminary_classification,
            "preliminary_risk_score": preliminary_risk_score,
            "approval_signals": approval_signals,
            "concern_signals": concern_signals,
            "thresholds_applied": {
                "min_credit_approve": min_credit_approve,
                "min_credit_review": min_credit_review,
                "max_dti_approve": max_dti_approve,
                "max_dti_review": max_dti_review,
            },
        }

    except Exception as e:
        logger.error(f"Error applying decision thresholds: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def get_decision_templates() -> Dict[str, Any]:
    """Get JSON templates for decision outputs.

    Returns:
        Decision output templates
    """
    try:
        templates = {
            "decision_factors": [
                {
                    "factor": "Credit Score",
                    "value": "700+",
                    "impact": "positive",
                    "weight": 0.25,
                },
                {
                    "factor": "DTI Ratio",
                    "value": "< 0.40",
                    "impact": "positive",
                    "weight": 0.25,
                },
                {
                    "factor": "Income Stability",
                    "value": "High",
                    "impact": "positive",
                    "weight": 0.25,
                },
                {
                    "factor": "Employment Risk",
                    "value": "Low",
                    "impact": "positive",
                    "weight": 0.15,
                },
            ],
            "decision_reasoning": {
                "summary": "Application approved",
                "applicant_profile_assessment": "Strong employment history",
                "financial_risk_assessment": "Acceptable financial profile",
                "decision_logic": "All major criteria met",
                "risk_mitigation_factors": ["Strong credit score", "Stable employment"],
            },
            "classifications": ["approved", "rejected", "manual_review"],
        }

        return {
            "success": True,
            "templates": templates,
        }

    except Exception as e:
        logger.error(f"Error getting decision templates: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


async def start_server(port: int = 3003):
    """Start the MCP server."""
    logger.info(f"Starting DecisionSynthesis MCP Server on port {port}")
    await mcp.run(port)


if __name__ == "__main__":
    import asyncio

    asyncio.run(start_server())
