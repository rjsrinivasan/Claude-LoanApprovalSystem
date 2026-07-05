"""Applicant Profile Agent - Analyzes applicant information."""

import json
import logging
from typing import Any, Dict

from anthropic import Anthropic

from agents.prompts import (
    APPLICANT_PROFILE_SYSTEM_PROMPT,
    APPLICANT_PROFILE_USER_PROMPT_TEMPLATE,
)
from config.settings import get_settings
from database.schemas import ApplicantProfileOutput
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ApplicantProfileAgent:
    """Agent for analyzing applicant profiles."""

    def __init__(self):
        """Initialize the agent."""
        self.settings = get_settings()
        self.client = Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = self.settings.claude_model

    def analyze_applicant(
        self,
        applicant_id: str,
        age: int,
        income: float,
        employment_type: str,
        employment_tenure_years: int,
        location: str,
        credit_history_summary: str = "Not available",
    ) -> ApplicantProfileOutput:
        """Analyze applicant profile.

        Args:
            applicant_id: Applicant ID
            age: Applicant age
            income: Annual income
            employment_type: Type of employment
            employment_tenure_years: Years in current employment
            location: Applicant location
            credit_history_summary: Summary of credit history

        Returns:
            ApplicantProfileOutput with analysis results
        """
        try:
            # Prepare the prompt
            user_prompt = APPLICANT_PROFILE_USER_PROMPT_TEMPLATE.format(
                applicant_id=applicant_id,
                age=age,
                income=income,
                employment_type=employment_type,
                employment_tenure_years=employment_tenure_years,
                location=location or "Not provided",
                credit_history_summary=credit_history_summary,
            )

            logger.info(
                f"Analyzing applicant profile for {applicant_id}",
                extra={"applicant_id": applicant_id},
            )

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=APPLICANT_PROFILE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract response
            response_text = message.content[0].text

            # Parse JSON response
            # Find JSON in response (may be wrapped in markdown code blocks)
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text

            analysis = json.loads(json_str)

            logger.info(
                f"Applicant profile analysis completed",
                extra={
                    "applicant_id": applicant_id,
                    "income_stability_score": analysis.get("income_stability_score"),
                },
            )

            # Ensure assessment_reasoning is a string
            assessment_reasoning = analysis.get("assessment_reasoning", "Analysis complete")
            if isinstance(assessment_reasoning, dict):
                assessment_reasoning = json.dumps(assessment_reasoning)

            # Create output object
            return ApplicantProfileOutput(
                income_stability_score=analysis.get("income_stability_score", 50),
                employment_risk_level=analysis.get(
                    "employment_risk_level", "medium"
                ),
                credit_history_summary=analysis.get(
                    "credit_history_summary", credit_history_summary
                ),
                application_completeness_flags=analysis.get(
                    "application_completeness_flags", []
                ),
                assessment_reasoning=assessment_reasoning,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response as JSON: {str(e)}")
            # Return default output on parsing error
            return ApplicantProfileOutput(
                income_stability_score=50,
                employment_risk_level="medium",
                credit_history_summary="Analysis error",
                application_completeness_flags=["json_parsing_error"],
                assessment_reasoning="Failed to parse agent response",
            )

        except Exception as e:
            logger.error(
                f"Error analyzing applicant profile: {str(e)}",
                extra={"applicant_id": applicant_id},
            )
            raise


def run_applicant_profile_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the applicant profile agent as a workflow node.

    Args:
        state: Workflow state (dict or Pydantic WorkflowState)

    Returns:
        Updated state with applicant profile analysis
    """
    # Handle Pydantic model
    if hasattr(state, "__dict__") and not isinstance(state, dict):
        state = state.dict() if hasattr(state, "dict") else state.__dict__

    agent = ApplicantProfileAgent()

    app_data = state.get("application_data", {})

    output = agent.analyze_applicant(
        applicant_id=app_data.get("applicant_id", "UNKNOWN"),
        age=app_data.get("age", 0),
        income=app_data.get("income", 0),
        employment_type=app_data.get("employment_type", "unknown"),
        employment_tenure_years=app_data.get("employment_tenure_years", 0),
        location=app_data.get("location", ""),
    )

    state["applicant_profile_output"] = output.dict()
    return state
