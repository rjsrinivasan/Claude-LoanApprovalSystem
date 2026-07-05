"""Loan Decision Agent - Synthesizes analysis into final decision."""

import json
import logging
from typing import Any, Dict, List

from anthropic import Anthropic

from agents.prompts import (
    LOAN_DECISION_SYSTEM_PROMPT,
    LOAN_DECISION_USER_PROMPT_TEMPLATE,
)
from config.settings import get_settings
from database.schemas import DecisionOutput, DecisionFactors, DecisionReasoning
from utils.logging_config import get_logger

logger = get_logger(__name__)


class LoanDecisionAgent:
    """Agent for making final loan decisions."""

    def __init__(self):
        """Initialize the agent."""
        self.settings = get_settings()
        self.client = Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = self.settings.claude_model

    def make_decision(
        self,
        applicant_id: str,
        income_stability_score: float,
        income_stability_level: str,
        employment_risk_level: str,
        credit_history_summary: str,
        completeness_flags: List[str],
        dti_ratio: float,
        dti_risk_level: str,
        credit_score: int,
        credit_risk_level: str,
        loan_to_income_ratio: float,
        loan_amount_risk: str,
        anomalies: List[str],
        loan_amount: float,
        loan_tenure_months: int,
        existing_liabilities: float,
    ) -> DecisionOutput:
        """Make a loan decision.

        Args:
            applicant_id: Applicant ID
            income_stability_score: Income stability score (0-100)
            income_stability_level: Income stability level
            employment_risk_level: Employment risk level
            credit_history_summary: Credit history summary
            completeness_flags: Completeness flags
            dti_ratio: DTI ratio
            dti_risk_level: DTI risk level
            credit_score: Credit score
            credit_risk_level: Credit risk level
            loan_to_income_ratio: Loan-to-income ratio
            loan_amount_risk: Loan amount risk level
            anomalies: List of detected anomalies
            loan_amount: Loan amount
            loan_tenure_months: Loan tenure
            existing_liabilities: Existing liabilities

        Returns:
            DecisionOutput with final decision
        """
        try:
            # Prepare prompt
            completeness_flags_str = ", ".join(completeness_flags) if completeness_flags else "None"
            anomalies_str = "\n".join(anomalies) if anomalies else "None"

            user_prompt = LOAN_DECISION_USER_PROMPT_TEMPLATE.format(
                income_stability_score=income_stability_score,
                income_stability_level=income_stability_level,
                employment_risk_level=employment_risk_level,
                credit_history_summary=credit_history_summary,
                completeness_flags=completeness_flags_str,
                dti_ratio=dti_ratio,
                dti_risk_level=dti_risk_level,
                credit_score=credit_score,
                credit_risk_level=credit_risk_level,
                loan_to_income_ratio=loan_to_income_ratio,
                loan_amount_risk=loan_amount_risk,
                anomalies=anomalies_str,
                loan_amount=loan_amount,
                loan_tenure_months=loan_tenure_months,
                existing_liabilities=existing_liabilities,
            )

            logger.info(
                f"Making loan decision for {applicant_id}",
                extra={"applicant_id": applicant_id},
            )

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=LOAN_DECISION_SYSTEM_PROMPT,
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

            # Extract classification
            classification = analysis.get("classification", "manual_review").lower()
            if classification not in ["approved", "rejected", "manual_review"]:
                classification = "manual_review"

            # Extract risk score and confidence
            risk_score = float(analysis.get("risk_score", 50))
            risk_score = max(0, min(100, risk_score))  # Clamp to 0-100

            confidence_level = float(analysis.get("confidence_level", 50))
            confidence_level = max(0, min(100, confidence_level))  # Clamp to 0-100

            # Extract key factors
            key_factors_raw = analysis.get("key_factors", [])
            key_factors = []

            if isinstance(key_factors_raw, list):
                for factor in key_factors_raw:
                    if isinstance(factor, dict):
                        key_factors.append(
                            DecisionFactors(
                                factor=factor.get("factor", "Unknown"),
                                value=factor.get("value", ""),
                                impact=factor.get("impact", "neutral"),
                                weight=float(factor.get("weight", 1.0)),
                            )
                        )

            # Extract reasoning
            reasoning = DecisionReasoning(
                summary=analysis.get("summary", "Decision made"),
                applicant_profile_assessment=analysis.get(
                    "applicant_profile_assessment", ""
                ),
                financial_risk_assessment=analysis.get(
                    "financial_risk_assessment", ""
                ),
                decision_logic=analysis.get("decision_logic", ""),
                risk_mitigation_factors=analysis.get(
                    "risk_mitigation_factors", []
                ),
            )

            logger.info(
                f"Loan decision completed",
                extra={
                    "applicant_id": applicant_id,
                    "classification": classification,
                    "risk_score": risk_score,
                    "confidence_level": confidence_level,
                },
            )

            return DecisionOutput(
                classification=classification,
                risk_score=risk_score,
                confidence_level=confidence_level,
                key_factors=key_factors,
                reasoning=reasoning,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response as JSON: {str(e)}")
            # Return safe default decision
            return DecisionOutput(
                classification="manual_review",
                risk_score=75.0,
                confidence_level=30.0,
                key_factors=[],
                reasoning=DecisionReasoning(
                    summary="Unable to parse decision agent response",
                    applicant_profile_assessment="",
                    financial_risk_assessment="",
                    decision_logic="Defaulted to manual review due to parsing error",
                ),
            )

        except Exception as e:
            logger.error(
                f"Error making loan decision: {str(e)}",
                extra={"applicant_id": applicant_id},
            )
            raise


def run_loan_decision_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the loan decision agent as a workflow node.

    Args:
        state: Workflow state (dict or Pydantic WorkflowState)

    Returns:
        Updated state with final decision
    """
    # Handle Pydantic model
    if hasattr(state, "__dict__") and not isinstance(state, dict):
        state = state.dict() if hasattr(state, "dict") else state.__dict__

    agent = LoanDecisionAgent()

    app_profile = state.get("applicant_profile_output", {})
    app_risk = state.get("financial_risk_output", {})
    app_data = state.get("application_data", {})

    monthly_income = app_data.get("income", 0) / 12
    loan_to_income = (app_data.get("loan_amount", 0) / (monthly_income * 12)) if monthly_income > 0 else 999

    output = agent.make_decision(
        applicant_id=app_data.get("applicant_id", "UNKNOWN"),
        income_stability_score=app_profile.get("income_stability_score", 50),
        income_stability_level=app_profile.get("income_stability_level", "medium"),
        employment_risk_level=app_profile.get("employment_risk_level", "medium"),
        credit_history_summary=app_profile.get("credit_history_summary", ""),
        completeness_flags=app_profile.get("application_completeness_flags", []),
        dti_ratio=app_risk.get("dti_ratio", 0.5),
        dti_risk_level=app_risk.get("dti_risk_level", "medium"),
        credit_score=app_data.get("credit_score", 600),
        credit_risk_level=app_risk.get("credit_score_risk_level", "medium"),
        loan_to_income_ratio=loan_to_income,
        loan_amount_risk=app_risk.get("loan_amount_risk", "medium"),
        anomalies=app_risk.get("anomalies_detected", []),
        loan_amount=app_data.get("loan_amount", 0),
        loan_tenure_months=app_data.get("loan_tenure_months", 360),
        existing_liabilities=app_data.get("existing_liabilities", 0),
    )

    state["decision_output"] = output.dict()
    return state
