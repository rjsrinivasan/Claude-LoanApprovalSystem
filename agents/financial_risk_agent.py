"""Financial Risk Agent - Analyzes financial metrics and risk."""

import json
import logging
from typing import Any, Dict, List

from anthropic import Anthropic

from agents.prompts import (
    FINANCIAL_RISK_SYSTEM_PROMPT,
    FINANCIAL_RISK_USER_PROMPT_TEMPLATE,
)
from config.settings import get_settings
from database.schemas import FinancialRiskOutput
from utils.logging_config import get_logger
from utils.validators import (
    calculate_dti_ratio,
    assess_credit_risk,
    detect_anomalies,
)

logger = get_logger(__name__)


class FinancialRiskAgent:
    """Agent for analyzing financial risk."""

    def __init__(self):
        """Initialize the agent."""
        self.settings = get_settings()
        self.client = Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = self.settings.claude_model

    def analyze_financial_risk(
        self,
        applicant_id: str,
        monthly_income: float,
        credit_score: int,
        loan_amount: float,
        loan_tenure_months: int,
        existing_liabilities: float,
    ) -> FinancialRiskOutput:
        """Analyze financial risk.

        Args:
            applicant_id: Applicant ID
            monthly_income: Monthly income
            credit_score: Credit score
            loan_amount: Loan amount requested
            loan_tenure_months: Loan tenure in months
            existing_liabilities: Total existing monthly liabilities

        Returns:
            FinancialRiskOutput with analysis results
        """
        try:
            # Calculate metrics
            dti_ratio = calculate_dti_ratio(
                monthly_income=monthly_income,
                total_liabilities=existing_liabilities,
                loan_amount=loan_amount,
                loan_tenure_months=loan_tenure_months,
            )

            credit_risk_level, _ = assess_credit_risk(credit_score)

            loan_to_income_ratio = (loan_amount / (monthly_income * 12)) if monthly_income > 0 else 999

            # Assess loan amount risk
            if loan_to_income_ratio <= 3.0:
                loan_amount_risk = "low"
            elif loan_to_income_ratio <= 4.0:
                loan_amount_risk = "medium"
            elif loan_to_income_ratio <= 5.0:
                loan_amount_risk = "high"
            else:
                loan_amount_risk = "very_high"

            # Detect anomalies
            anomalies = detect_anomalies(
                loan_amount=loan_amount,
                monthly_income=monthly_income,
                dti_ratio=dti_ratio,
            )

            # Prepare prompt for Claude
            anomalies_str = "\n".join(anomalies) if anomalies else "No anomalies detected"

            user_prompt = FINANCIAL_RISK_USER_PROMPT_TEMPLATE.format(
                applicant_id=applicant_id,
                monthly_income=monthly_income,
                credit_score=credit_score,
                loan_amount=loan_amount,
                loan_tenure_months=loan_tenure_months,
                existing_liabilities=existing_liabilities,
                dti_ratio=dti_ratio,
                credit_risk_level=credit_risk_level,
                loan_to_income_ratio=loan_to_income_ratio,
                anomalies=anomalies_str,
            )

            logger.info(
                f"Analyzing financial risk for {applicant_id}",
                extra={
                    "applicant_id": applicant_id,
                    "dti_ratio": dti_ratio,
                    "credit_score": credit_score,
                },
            )

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=FINANCIAL_RISK_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract response
            response_text = message.content[0].text

            # Parse JSON response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text

            analysis = json.loads(json_str)

            logger.info(
                f"Financial risk analysis completed",
                extra={
                    "applicant_id": applicant_id,
                    "dti_ratio": dti_ratio,
                },
            )

            # Ensure risk_assessment_reasoning is a string
            risk_reasoning = analysis.get("risk_assessment_reasoning", "Analysis complete")
            if isinstance(risk_reasoning, dict):
                risk_reasoning = json.dumps(risk_reasoning)

            return FinancialRiskOutput(
                dti_ratio=dti_ratio,
                credit_score_risk_level=analysis.get(
                    "credit_score_risk_level", credit_risk_level
                ),
                loan_amount_risk=analysis.get("loan_amount_risk", loan_amount_risk),
                anomalies_detected=analysis.get(
                    "anomalies_detected", anomalies
                ),
                risk_assessment_reasoning=risk_reasoning,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response as JSON: {str(e)}")
            return FinancialRiskOutput(
                dti_ratio=dti_ratio,
                credit_score_risk_level="medium",
                loan_amount_risk="medium",
                anomalies_detected=anomalies,
                risk_assessment_reasoning="Failed to parse agent response",
            )

        except Exception as e:
            logger.error(
                f"Error analyzing financial risk: {str(e)}",
                extra={"applicant_id": applicant_id},
            )
            raise


def run_financial_risk_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the financial risk agent as a workflow node.

    Args:
        state: Workflow state (dict or Pydantic WorkflowState)

    Returns:
        Updated state with financial risk analysis
    """
    # Handle Pydantic model
    if hasattr(state, "__dict__") and not isinstance(state, dict):
        state = state.dict() if hasattr(state, "dict") else state.__dict__

    agent = FinancialRiskAgent()

    app_data = state.get("application_data", {})

    monthly_income = app_data.get("income", 0) / 12

    output = agent.analyze_financial_risk(
        applicant_id=app_data.get("applicant_id", "UNKNOWN"),
        monthly_income=monthly_income,
        credit_score=app_data.get("credit_score", 0),
        loan_amount=app_data.get("loan_amount", 0),
        loan_tenure_months=app_data.get("loan_tenure_months", 360),
        existing_liabilities=app_data.get("existing_liabilities", 0),
    )

    state["financial_risk_output"] = output.dict()
    return state
