"""Tests for validators module."""

import pytest
from utils.validators import (
    calculate_dti_ratio,
    assess_income_stability,
    assess_credit_risk,
    detect_anomalies,
)


class TestDTICalculation:
    """Test DTI ratio calculations."""

    def test_dti_calculation_normal(self):
        """Test normal DTI calculation."""
        dti = calculate_dti_ratio(
            monthly_income=5000,
            total_liabilities=1000,
            loan_amount=300000,
            loan_tenure_months=360,
        )
        assert 0 < dti < 1

    def test_dti_high_liabilities(self):
        """Test DTI with high liabilities."""
        dti = calculate_dti_ratio(
            monthly_income=3000,
            total_liabilities=2000,
            loan_amount=200000,
            loan_tenure_months=360,
        )
        assert dti > 0.5


class TestIncomeStability:
    """Test income stability assessment."""

    def test_salaried_long_tenure(self):
        """Test salaried employee with long tenure."""
        level, score = assess_income_stability(
            employment_type="salaried",
            employment_tenure_years=10,
        )
        assert level == "high"
        assert score >= 0.8

    def test_self_employed_short_tenure(self):
        """Test self-employed with short tenure."""
        level, score = assess_income_stability(
            employment_type="self_employed",
            employment_tenure_years=1,
        )
        assert level == "low"
        assert score < 0.7


class TestCreditRisk:
    """Test credit risk assessment."""

    def test_excellent_credit(self):
        """Test excellent credit score."""
        level, score = assess_credit_risk(800)
        assert level == "low"
        assert score < 0.3

    def test_poor_credit(self):
        """Test poor credit score."""
        level, score = assess_credit_risk(500)
        assert level == "high"
        assert score > 0.7


class TestAnomalyDetection:
    """Test anomaly detection."""

    def test_high_loan_to_income(self):
        """Test detection of high loan-to-income ratio."""
        anomalies = detect_anomalies(
            loan_amount=1000000,
            monthly_income=2000,
            dti_ratio=0.3,
        )
        assert len(anomalies) > 0
        assert any("income" in a.lower() for a in anomalies)

    def test_no_anomalies(self):
        """Test with normal parameters."""
        anomalies = detect_anomalies(
            loan_amount=300000,
            monthly_income=5000,
            dti_ratio=0.35,
        )
        assert len(anomalies) == 0
