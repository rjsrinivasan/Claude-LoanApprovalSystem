"""Input validation utilities."""

from typing import Dict, Any, Tuple


def validate_loan_application(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate loan application data.

    Args:
        data: Application data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
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

    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Validate age
    if not isinstance(data["age"], int) or data["age"] < 18 or data["age"] > 100:
        return False, "Age must be between 18 and 100"

    # Validate income
    if not isinstance(data["income"], (int, float)) or data["income"] <= 0:
        return False, "Income must be a positive number"

    # Validate credit score
    if not isinstance(data["credit_score"], int) or data["credit_score"] < 300 or data["credit_score"] > 850:
        return False, "Credit score must be between 300 and 850"

    # Validate loan amount
    if not isinstance(data["loan_amount"], (int, float)) or data["loan_amount"] <= 0:
        return False, "Loan amount must be a positive number"

    # Validate loan tenure
    if not isinstance(data["loan_tenure_months"], int) or data["loan_tenure_months"] <= 0:
        return False, "Loan tenure must be a positive integer"

    # Validate existing liabilities
    if not isinstance(data["existing_liabilities"], (int, float)) or data["existing_liabilities"] < 0:
        return False, "Existing liabilities must be non-negative"

    # Validate employment type
    valid_employment_types = ["salaried", "self_employed", "contract", "retired"]
    if data["employment_type"] not in valid_employment_types:
        return False, f"Employment type must be one of: {', '.join(valid_employment_types)}"

    return True, ""


def calculate_monthly_payment(
    loan_amount: float,
    annual_rate: float = 0.06,  # Default 6% annual
    tenure_months: int = 360,
) -> float:
    """Calculate monthly loan payment using amortization formula.

    Args:
        loan_amount: Total loan amount
        annual_rate: Annual interest rate (default 6%)
        tenure_months: Loan tenure in months

    Returns:
        Monthly payment amount
    """
    if tenure_months == 0:
        return 0
    if annual_rate == 0:
        return loan_amount / tenure_months

    monthly_rate = annual_rate / 12
    payment = loan_amount * (
        (monthly_rate * (1 + monthly_rate) ** tenure_months) /
        ((1 + monthly_rate) ** tenure_months - 1)
    )
    return payment


def calculate_dti_ratio(
    monthly_income: float,
    total_liabilities: float,
    loan_amount: float,
    loan_tenure_months: int,
) -> float:
    """Calculate Debt-to-Income ratio.

    Args:
        monthly_income: Monthly income (annual / 12)
        total_liabilities: Total monthly liabilities
        loan_amount: New loan amount
        loan_tenure_months: New loan tenure in months

    Returns:
        DTI ratio (0-1)
    """
    if monthly_income <= 0:
        return 1.0  # Maximum risk if no income

    monthly_payment = calculate_monthly_payment(loan_amount, tenure_months=loan_tenure_months)
    total_monthly_debt = total_liabilities + monthly_payment

    dti = total_monthly_debt / monthly_income
    return min(dti, 2.0)  # Cap at 2.0 (200%)


def assess_income_stability(
    employment_type: str,
    employment_tenure_years: int = 0,
) -> Tuple[str, float]:
    """Assess income stability based on employment characteristics.

    Args:
        employment_type: Type of employment
        employment_tenure_years: Years in current employment

    Returns:
        Tuple of (stability_level, stability_score)
    """
    # Base scores by employment type
    base_scores = {
        "salaried": 0.85,
        "contract": 0.70,
        "self_employed": 0.60,
        "retired": 0.80,  # Assumed stable pension/retirement income
    }

    base_score = base_scores.get(employment_type, 0.50)

    # Adjust based on tenure
    if employment_type == "salaried":
        if employment_tenure_years >= 5:
            score = 0.90
        elif employment_tenure_years >= 2:
            score = 0.80
        else:
            score = 0.70
    elif employment_type == "contract":
        if employment_tenure_years >= 3:
            score = 0.75
        else:
            score = 0.65
    elif employment_type == "self_employed":
        if employment_tenure_years >= 5:
            score = 0.75
        else:
            score = 0.60
    else:
        score = base_score

    # Map to stability level
    if score >= 0.80:
        level = "high"
    elif score >= 0.65:
        level = "medium"
    else:
        level = "low"

    return level, score


def assess_credit_risk(credit_score: int) -> Tuple[str, float]:
    """Assess credit risk based on credit score.

    Args:
        credit_score: Credit score (300-850)

    Returns:
        Tuple of (risk_level, risk_score)
    """
    if credit_score >= 750:
        return "low", 0.20  # 20% risk score
    elif credit_score >= 700:
        return "low_medium", 0.35
    elif credit_score >= 650:
        return "medium", 0.50
    elif credit_score >= 600:
        return "medium_high", 0.65
    elif credit_score >= 550:
        return "high", 0.80
    else:
        return "very_high", 0.95  # 95% risk score


def detect_anomalies(
    loan_amount: float,
    monthly_income: float,
    dti_ratio: float,
) -> list:
    """Detect financial anomalies.

    Args:
        loan_amount: Loan amount
        monthly_income: Monthly income
        dti_ratio: DTI ratio

    Returns:
        List of detected anomalies
    """
    anomalies = []

    # Check loan-to-income ratio
    annual_income = monthly_income * 12
    if annual_income > 0:
        loan_to_income = loan_amount / annual_income
        if loan_to_income > 5.0:
            anomalies.append(
                f"High loan-to-income ratio ({loan_to_income:.2f}x annual income)"
            )

    # Check DTI ratio
    if dti_ratio > 0.50:
        anomalies.append(f"DTI ratio exceeds 50% ({dti_ratio*100:.1f}%)")

    # Check for unusually large loans
    if loan_amount > 1_000_000:
        anomalies.append(f"Very large loan amount (${loan_amount:,.0f})")

    return anomalies
