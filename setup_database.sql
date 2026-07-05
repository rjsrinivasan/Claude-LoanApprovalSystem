-- =====================================================
-- Loan Approval System - MySQL Database Schema
-- =====================================================

-- Create applicants table
CREATE TABLE IF NOT EXISTS applicants (
    applicant_id VARCHAR(36) PRIMARY KEY,
    age INT NOT NULL,
    income DECIMAL(12, 2) NOT NULL,
    employment_type ENUM('salaried', 'self_employed', 'contract', 'retired') NOT NULL,
    employment_tenure_years INT,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_applicant_id (applicant_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create loan_applications table
CREATE TABLE IF NOT EXISTS loan_applications (
    application_id VARCHAR(36) PRIMARY KEY,
    applicant_id VARCHAR(36) NOT NULL,
    credit_score INT NOT NULL,
    loan_amount DECIMAL(12, 2) NOT NULL,
    loan_tenure_months INT NOT NULL,
    existing_liabilities DECIMAL(12, 2) NOT NULL,
    application_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('submitted', 'processing', 'completed') DEFAULT 'submitted',
    INDEX idx_applicant_id (applicant_id),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status),
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create risk_rules table
CREATE TABLE IF NOT EXISTS risk_rules (
    rule_id VARCHAR(36) PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type ENUM('credit_score', 'dti_ratio', 'loan_amount', 'income_stability') NOT NULL,
    min_value DECIMAL(10, 3),
    max_value DECIMAL(10, 3),
    threshold_approve DECIMAL(10, 3),
    threshold_review DECIMAL(10, 3),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rule_type (rule_type),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create loan_decisions table (stores final decisions with reasoning)
CREATE TABLE IF NOT EXISTS loan_decisions (
    case_id VARCHAR(36) PRIMARY KEY,
    application_id VARCHAR(36) NOT NULL,
    applicant_id VARCHAR(36) NOT NULL,
    classification ENUM('approved', 'rejected', 'manual_review') NOT NULL,
    risk_score DECIMAL(5, 2) NOT NULL,
    confidence_level DECIMAL(5, 2) NOT NULL,
    decision_reasoning JSON NOT NULL,
    key_factors JSON NOT NULL,
    applicant_profile JSON,
    financial_risk_analysis JSON,
    decision_details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_case_id (case_id),
    INDEX idx_application_id (application_id),
    INDEX idx_applicant_id (applicant_id),
    INDEX idx_classification (classification),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create audit_logs table (comprehensive audit trail)
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id VARCHAR(36) PRIMARY KEY,
    case_id VARCHAR(36),
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT,
    actor VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    old_value JSON,
    new_value JSON,
    status VARCHAR(20),
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    INDEX idx_case_id (case_id),
    INDEX idx_event_type (event_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_resource_id (resource_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    notification_id VARCHAR(36) PRIMARY KEY,
    case_id VARCHAR(36) NOT NULL,
    applicant_id VARCHAR(36) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    status ENUM('pending', 'sent', 'failed') DEFAULT 'pending',
    message TEXT,
    recipient_details JSON,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_case_id (case_id),
    INDEX idx_applicant_id (applicant_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Insert Default Risk Rules
-- =====================================================

INSERT INTO risk_rules (rule_id, rule_name, rule_type, threshold_approve, threshold_review, description, active) VALUES
('rule_001', 'Credit Score Approval Threshold', 'credit_score', 650, 550, 'Credit score >= 650 for approval, >= 550 for review', TRUE),
('rule_002', 'DTI Ratio Approval Threshold', 'dti_ratio', 0.40, 0.50, 'DTI ratio <= 0.40 for approval, <= 0.50 for review', TRUE),
('rule_003', 'Loan Amount Risk', 'loan_amount', 500000, 1000000, 'Loan amount threshold for risk assessment', TRUE),
('rule_004', 'Income Stability', 'income_stability', 0.75, 0.60, 'Income stability confidence threshold', TRUE);

-- =====================================================
-- Create Views for Reporting
-- =====================================================

CREATE OR REPLACE VIEW v_decision_summary AS
SELECT
    ld.case_id,
    ld.applicant_id,
    ld.classification,
    ld.risk_score,
    ld.confidence_level,
    la.credit_score,
    la.loan_amount,
    a.income,
    ld.created_at
FROM loan_decisions ld
JOIN loan_applications la ON ld.application_id = la.application_id
JOIN applicants a ON ld.applicant_id = a.applicant_id
ORDER BY ld.created_at DESC;

-- =====================================================
-- Grants (adjust username/password as needed)
-- =====================================================
-- GRANT ALL PRIVILEGES ON loanapproval_db.* TO 'loanapp_user'@'localhost';
-- FLUSH PRIVILEGES;
