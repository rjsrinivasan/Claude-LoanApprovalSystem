"""Streamlit UI for Loan Approval System."""

import requests
import streamlit as st
from datetime import datetime
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="Intelligent Loan Approval System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("🏦 Intelligent Loan Approval System")
st.markdown("AI-Powered Loan Application Analysis")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    api_url = st.text_input(
        "API URL",
        value="http://localhost:8000",
        help="Base URL of the Loan Approval API",
    )
    st.divider()
    st.markdown("### About")
    st.markdown("""
    This system uses Multi-Agent AI to analyze loan applications and provide:
    - Fast and consistent decisions
    - Explainable reasoning
    - Audit trails for compliance
    - Fair and unbiased assessments
    """)

# Initialize session state
if "submitted_applications" not in st.session_state:
    st.session_state.submitted_applications = []

# Tabs
tab1, tab2 = st.tabs(["Submit Application", "View Results"])

# =====================================================
# TAB 1: Submit Application
# =====================================================
with tab1:
    st.header("Loan Application Form")

    with st.form("loan_application_form"):
        # Applicant Information
        st.subheader("👤 Applicant Information")

        col1, col2 = st.columns(2)
        with col1:
            applicant_id = st.text_input(
                "Applicant ID",
                placeholder="e.g., APP-001",
                help="Unique identifier for the applicant",
            )
            age = st.number_input(
                "Age",
                min_value=18,
                max_value=100,
                value=35,
                step=1,
                help="Applicant's age",
            )

        with col2:
            location = st.text_input(
                "Location",
                placeholder="e.g., New York, NY",
                help="Applicant's location",
            )
            employment_type = st.selectbox(
                "Employment Type",
                options=["salaried", "self_employed", "contract", "retired"],
                help="Type of employment",
            )

        # Employment and Income
        st.subheader("💼 Employment & Income")

        col1, col2 = st.columns(2)
        with col1:
            income = st.number_input(
                "Annual Income ($)",
                min_value=0.0,
                value=75000.0,
                step=1000.0,
                help="Annual income in USD",
            )
            employment_tenure = st.number_input(
                "Employment Tenure (years)",
                min_value=0,
                max_value=60,
                value=5,
                step=1,
                help="Years in current employment",
            )

        with col2:
            credit_score = st.number_input(
                "Credit Score",
                min_value=300,
                max_value=850,
                value=720,
                step=1,
                help="Credit score (FICO range)",
            )
            existing_liabilities = st.number_input(
                "Existing Monthly Liabilities ($)",
                min_value=0.0,
                value=2000.0,
                step=100.0,
                help="Total monthly debt obligations",
            )

        # Loan Information
        st.subheader("💰 Loan Information")

        col1, col2 = st.columns(2)
        with col1:
            loan_amount = st.number_input(
                "Loan Amount ($)",
                min_value=0.0,
                value=300000.0,
                step=10000.0,
                help="Requested loan amount",
            )

        with col2:
            loan_tenure = st.number_input(
                "Loan Tenure (months)",
                min_value=1,
                max_value=600,
                value=360,
                step=1,
                help="Loan repayment period in months",
            )

        # Submit button
        submitted = st.form_submit_button(
            "🚀 Submit Application",
            use_container_width=True,
        )

        if submitted:
            # Validation
            errors = []
            if not applicant_id:
                errors.append("Applicant ID is required")
            if income <= 0:
                errors.append("Income must be positive")
            if loan_amount <= 0:
                errors.append("Loan amount must be positive")

            if errors:
                st.error("⚠️ Validation errors:")
                for error in errors:
                    st.write(f"  • {error}")
            else:
                # Call API
                st.info("Processing application...")

                payload = {
                    "applicant_id": applicant_id,
                    "age": age,
                    "income": income,
                    "employment_type": employment_type,
                    "employment_tenure_years": employment_tenure,
                    "credit_score": credit_score,
                    "loan_amount": loan_amount,
                    "loan_tenure_months": loan_tenure,
                    "existing_liabilities": existing_liabilities,
                    "location": location,
                }

                try:
                    response = requests.post(
                        f"{api_url}/api/v1/loan-applications",
                        json=payload,
                        timeout=120,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.submitted_applications.append(result)
                        st.success("✅ Application processed successfully!")

                        # Display decision
                        st.divider()
                        st.subheader("Decision")

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            classification = result.get("classification", "unknown").upper()
                            if classification == "APPROVED":
                                st.metric("Status", "✅ APPROVED")
                            elif classification == "REJECTED":
                                st.metric("Status", "❌ REJECTED")
                            else:
                                st.metric("Status", "⏳ UNDER REVIEW")

                        with col2:
                            risk_score = result.get("risk_score", 0)
                            st.metric("Risk Score", f"{risk_score:.1f}%")

                        with col3:
                            confidence = result.get("confidence_level", 0)
                            st.metric("Confidence", f"{confidence:.1f}%")

                        with col4:
                            case_id = result.get("case_id", "N/A")
                            st.metric("Case ID", case_id)

                        # Display reasoning
                        st.divider()
                        st.subheader("Decision Reasoning")

                        explanation = result.get("explanation", {})
                        st.write("**Summary:**", explanation.get("summary", ""))
                        st.write(
                            "**Applicant Assessment:**",
                            explanation.get("applicant_profile_assessment", ""),
                        )
                        st.write(
                            "**Financial Risk:**",
                            explanation.get("financial_risk_assessment", ""),
                        )

                        # Key factors
                        st.divider()
                        st.subheader("Key Decision Factors")

                        factors = result.get("key_decision_factors", [])
                        for factor in factors:
                            with st.container():
                                col1, col2, col3 = st.columns([2, 2, 1])
                                with col1:
                                    st.write(f"**{factor.get('factor')}**")
                                with col2:
                                    st.write(factor.get("value", ""))
                                with col3:
                                    impact = factor.get("impact", "neutral")
                                    if impact == "positive":
                                        st.write("✅")
                                    elif impact == "negative":
                                        st.write("❌")
                                    else:
                                        st.write("⚪")

                        # Next steps
                        st.divider()
                        st.info(f"**Next Steps:** {result.get('next_steps', '')}")

                    else:
                        error_data = response.json()
                        st.error(
                            f"Application processing failed: {error_data.get('detail', 'Unknown error')}"
                        )

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Make sure the server is running.")
                except requests.exceptions.Timeout:
                    st.error("❌ Request timeout. The server took too long to respond.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# =====================================================
# TAB 2: View Results
# =====================================================
with tab2:
    st.header("Application Results")

    if not st.session_state.submitted_applications:
        st.info("No applications submitted yet. Submit one in the 'Submit Application' tab.")
    else:
        st.subheader(f"Submitted Applications ({len(st.session_state.submitted_applications)})")

        for idx, app in enumerate(st.session_state.submitted_applications):
            with st.expander(
                f"Case {app.get('case_id', 'Unknown')} - "
                f"{app.get('classification', 'unknown').upper()} - "
                f"{app.get('created_at', 'N/A')}"
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Classification", app.get("classification", "N/A").upper())

                with col2:
                    st.metric("Risk Score", f"{app.get('risk_score', 0):.1f}%")

                with col3:
                    st.metric("Confidence", f"{app.get('confidence_level', 0):.1f}%")

                st.divider()

                # Explanation
                explanation = app.get("explanation", {})
                st.write("**Summary:**", explanation.get("summary", ""))

                # Key factors
                st.write("**Key Factors:**")
                factors = app.get("key_decision_factors", [])
                for factor in factors:
                    st.write(
                        f"  • {factor.get('factor')}: {factor.get('value')} "
                        f"({factor.get('impact')})"
                    )

                # Next steps
                st.write("**Next Steps:**", app.get("next_steps", ""))

                # Audit trace
                st.write(f"**Audit Trace ID:** `{app.get('audit_trace_id', 'N/A')}`")

# Footer
st.divider()
st.markdown("""
---
### ⚠️ Disclaimer

This is a **case study and reference implementation** of an AI-powered loan approval system.
It is **NOT suitable for production banking use** without:

- Regulatory and legal review
- Compliance assessment (fair lending, bias audits)
- Model risk management approval
- Fairness and ethics review
- Integration with production banking systems
- Comprehensive testing and validation

For real-world deployment, consult with compliance, legal, risk management, and fairness experts.
""")
