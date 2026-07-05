"""Configuration management for the Loan Approval System."""

from functools import lru_cache
from typing import Optional
from urllib.parse import quote

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "loanapp_user"
    mysql_password: str = ""
    mysql_database: str = "loanapproval_db"

    # Anthropic API Configuration
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Service Configuration
    api_base_url: str = "http://localhost:8000"
    api_port: int = 8000
    streamlit_port: int = 8501

    # Logging Configuration
    log_level: str = "INFO"

    # MCP Server Configuration
    mcp_applicant_db_port: int = 3001
    mcp_risk_rules_port: int = 3002
    mcp_decision_synthesis_port: int = 3003
    mcp_notification_system_port: int = 3004

    # Decision Thresholds
    min_credit_score_approve: int = 650
    min_credit_score_review: int = 550
    max_dti_approve: float = 0.40
    max_dti_review: float = 0.50
    min_confidence_approve: float = 0.75

    # Risk Parameters
    min_monthly_income_multiplier: float = 1.25
    max_loan_to_income_ratio: float = 5.0

    # Feature Flags
    enable_audit_logging: bool = True
    enable_notifications: bool = True

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """Get database URL for SQLAlchemy."""
        encoded_password = quote(self.mysql_password, safe='')
        return (
            f"mysql+pymysql://{self.mysql_user}:{encoded_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    def validate_required_settings(self) -> None:
        """Validate that all required settings are configured."""
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set in .env")
        if not self.mysql_password:
            raise ValueError("MYSQL_PASSWORD must be set in .env")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.validate_required_settings()
    return settings
