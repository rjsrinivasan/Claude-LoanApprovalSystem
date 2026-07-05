# 🏦 Intelligent Loan Approval System

A production-grade **Multi-Agent Agentic AI system** for automated loan application analysis and decision-making using Claude Sonnet 4.6, LangGraph, FastAPI, and MySQL.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Running the System](#running-the-system)
- [API Usage](#api-usage)
- [Testing](#testing)
- [Compliance & Safety](#compliance--safety)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This system demonstrates how to build a scalable, explainable AI system for financial decision-making. It analyzes loan applications using a network of specialized agents that:

1. **Assess Applicant Profiles** - Income stability, employment risk, credit history
2. **Analyze Financial Risk** - DTI ratios, credit scores, anomaly detection
3. **Synthesize Decisions** - LLM-powered reasoning with clear explanations
4. **Ensure Compliance** - Audit trails, regulatory logging, notification management

### Key Capabilities

✅ **Fast Decision Making** - Analyze applications in seconds
✅ **Explainable Reasoning** - Clear justification for every decision
✅ **Audit-Friendly** - Complete decision history and reasoning trail
✅ **Fair & Unbiased** - Decisions exclude protected attributes from scoring
✅ **Scalable Architecture** - Modular agents, real database backend
✅ **Production-Ready** - Error handling, logging, validation throughout

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────┐
│          Streamlit UI (Port 8501)               │
│         Chatbot-Style Application               │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────┐
│    FastAPI Microservice (Port 8000)            │
│   Validation, Request Routing, Response        │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────┐
│        LangGraph Orchestration Engine           │
│     Multi-Stage Workflow Coordination           │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        │            │            │            │
   ┌────▼──┐   ┌────▼──┐   ┌────▼──┐   ┌────▼──┐
   │ Agent │   │ Agent │   │ Agent │   │ Agent │
   │   1   │   │   2   │   │   3   │   │   4   │
   └────┬──┘   └────┬──┘   └────┬──┘   └────┬──┘
        │            │            │            │
   ┌────▼──────┐ ┌──▼──────┐ ┌──▼──────┐ ┌──▼──────┐
   │ MCP Server│ │ MCP Srv │ │ MCP Srv │ │ MCP Srv │
   │  (Appli)  │ │ (Risks) │ │ (Synth) │ │(Notif)  │
   └────┬──────┘ └──┬──────┘ └──┬──────┘ └──┬──────┘
        │            │            │            │
        └────────────┼────────────┼────────────┘
                     │
              ┌──────▼──────┐
              │  MySQL DB   │
              │ (Applicants,│
              │ Decisions,  │
              │ Audit Logs) │
              └─────────────┘
```

### Data Flow

1. **User Input** → Streamlit submits application
2. **API Validation** → FastAPI validates with Pydantic
3. **Workflow Orchestration** → LangGraph coordinates agents
4. **Parallel Analysis** → Agents run concurrently:
   - Applicant Profile Agent → ApplicantDB MCP
   - Financial Risk Agent → RiskRulesDB MCP
5. **Decision Synthesis** → Decision Agent uses Claude for reasoning
6. **Compliance** → Compliance Agent persists decision + creates audit trail
7. **Response** → FastAPI returns structured decision
8. **UI Display** → Streamlit shows decision + explanation

### Workflow Diagram

```
START
  ↓
[Validate Application]
  ↓
  ├─ Has errors? → [End with error]
  │
  └─ Valid? ↓
  ┌─────────────────┐
  │ Run in Parallel │
  ├─────────────────┤
  │ Applicant       │ → [Applicant Profile Agent]
  │ Profile Agent   │   → ApplicantDB MCP
  │                 │
  │ Financial Risk  │ → [Financial Risk Agent]
  │ Agent           │   → RiskRulesDB MCP
  └─────────────────┘
        ↓
[Loan Decision Agent]
    → Synthesize outputs
    → Apply decision thresholds
    → Claude reasoning
    → Generate explanation
        ↓
[Compliance Agent]
    → Persist decision
    → Generate case ID
    → Create audit trail
    → Trigger notification
        ↓
[Return Response with Decision]
        ↓
      END
```

## ✨ Features

### Decision Classification

- **APPROVED** - All criteria met, low risk
- **REJECTED** - High risk signals, likely denial
- **MANUAL_REVIEW** - Mixed signals, requires underwriting

### Decision Factors

- Credit Score
- Debt-to-Income Ratio
- Income Stability
- Employment Risk
- Financial Anomalies

### Output Includes

- **Classification** - Final decision
- **Risk Score** (0-100) - Overall risk level
- **Confidence Level** (0-100) - Decision certainty
- **Key Factors** - Top drivers of decision
- **Explanation** - Reasoning in natural language
- **Case ID** - Unique reference for audit
- **Audit Trace** - Complete decision history

## 🔧 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Orchestration** | LangGraph | 0.0.76+ |
| **Agents** | Anthropic SDK | 0.25.1+ |
| **LLM** | Claude Sonnet 4.6 | Latest |
| **API** | FastAPI | 0.104.1+ |
| **UI** | Streamlit | 1.28.1+ |
| **MCP Servers** | FastMCP | 0.1.6+ |
| **Database** | MySQL | 8.0+ |
| **ORM** | SQLAlchemy | 2.0.23+ |
| **Validation** | Pydantic | 2.5.0+ |
| **Language** | Python | 3.8+ |

## 📦 Prerequisites

### Required

- Python 3.8+
- MySQL 8.0+ (or compatible)
- Anthropic API Key (Claude Sonnet 4.6 access)
- Git

### Optional

- Docker & Docker Compose (for containerization)
- Postman or curl (for API testing)
- MySQL Workbench (for database inspection)

## 🚀 Setup Instructions

### 1. Clone or Create Project

```bash
cd /home/ubuntu/Desktop/LoanApprovalSystem
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup MySQL Database

```bash
# Create database and user
mysql -u root -p < setup_database.sql
```

Or manually:

```sql
-- Login to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE loanapproval_db;
USE loanapproval_db;

-- Import schema
SOURCE setup_database.sql;

-- Create user (if not exists)
CREATE USER 'loanapp_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON loanapproval_db.* TO 'loanapp_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=loanapp_user
MYSQL_PASSWORD=secure_password_here
MYSQL_DATABASE=loanapproval_db

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Services
API_PORT=8000
STREAMLIT_PORT=8501
LOG_LEVEL=INFO
```

### 6. Verify Setup

```bash
python -c "
from config.settings import get_settings
from database.connection import DatabaseConnection

settings = get_settings()
DatabaseConnection.initialize()

if DatabaseConnection.health_check():
    print('✓ Setup successful!')
else:
    print('✗ Database connection failed')
"
```

## ▶️ Running the System

### Terminal 1: FastAPI Service

```bash
cd /home/ubuntu/Desktop/LoanApprovalSystem

# Activate venv if not already
source venv/bin/activate

# Start FastAPI service
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

### Terminal 2: Streamlit UI

```bash
cd /home/ubuntu/Desktop/LoanApprovalSystem

# Activate venv
source venv/bin/activate

# Start Streamlit
streamlit run frontend/streamlit_app.py

# Output:
# You can now view your Streamlit app in your browser.
# URL: http://localhost:8501
```

### Access the System

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **API Root**: http://localhost:8000

## 🌐 API Usage

### Submit Loan Application

**Endpoint:** `POST /api/v1/loan-applications`

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/loan-applications" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP-001",
    "age": 35,
    "income": 75000.00,
    "employment_type": "salaried",
    "employment_tenure_years": 5,
    "credit_score": 720,
    "loan_amount": 300000.00,
    "loan_tenure_months": 360,
    "existing_liabilities": 2000.00,
    "location": "New York, NY"
  }'
```

**Response:**

```json
{
  "case_id": "CASE_ABC123DEF456",
  "classification": "approved",
  "risk_score": 28.5,
  "confidence_level": 87.3,
  "key_decision_factors": [
    {
      "factor": "Credit Score",
      "value": "720 (Good)",
      "impact": "positive",
      "weight": 0.25
    },
    {
      "factor": "DTI Ratio",
      "value": "0.38 (Acceptable)",
      "impact": "positive",
      "weight": 0.25
    }
  ],
  "explanation": {
    "summary": "Application approved with low risk profile",
    "applicant_profile_assessment": "Stable employment, good income history",
    "financial_risk_assessment": "Strong financial metrics, acceptable debt levels",
    "decision_logic": "All major approval criteria met",
    "risk_mitigation_factors": ["Strong credit score", "Stable employment"]
  },
  "next_steps": "Application approved. Proceed with loan origination.",
  "created_at": "2024-07-02T10:30:45.123456",
  "audit_trace_id": "audit_xyz789"
}
```

### Get Application Status

**Endpoint:** `GET /api/v1/loan-applications/{case_id}`

```bash
curl "http://localhost:8000/api/v1/loan-applications/CASE_ABC123DEF456"
```

### Health Check

**Endpoint:** `GET /api/v1/health`

```bash
curl "http://localhost:8000/api/v1/health"
```

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_validators.py::TestDTICalculation -v
```

### Example Test Cases

```bash
# Test validators
python -m pytest tests/test_validators.py -v

# Test configuration
python -m pytest tests/test_config.py -v
```

### Manual Integration Test

```bash
# 1. Ensure all services are running

# 2. Submit test application
curl -X POST "http://localhost:8000/api/v1/loan-applications" \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# 3. Check response status and fields

# 4. Query decision by case ID
curl "http://localhost:8000/api/v1/loan-applications/CASE_XXX"

# 5. Verify database records
# Connect to MySQL and check:
# - applicants table
# - loan_applications table
# - loan_decisions table
# - audit_logs table
```

## 📊 Database Schema

### Key Tables

**applicants** - Applicant profile data
- applicant_id (PK)
- age, income, employment_type, employment_tenure_years
- location, created_at, updated_at

**loan_applications** - Application requests
- application_id (PK)
- applicant_id (FK)
- credit_score, loan_amount, loan_tenure_months
- existing_liabilities, status, created_at

**loan_decisions** - Final decisions
- case_id (PK)
- application_id (FK), applicant_id (FK)
- classification, risk_score, confidence_level
- decision_reasoning (JSON), key_factors (JSON)
- created_at

**audit_logs** - Complete audit trail
- audit_id (PK)
- case_id, event_type, event_description
- timestamp, status, metadata (JSON)

**notifications** - Notification records
- notification_id (PK)
- case_id, applicant_id (FK)
- notification_type, status, message

## ⚖️ Compliance & Safety

### Fairness Guardrails

✅ **Protected Attributes Excluded from Scoring:**
- Age is NOT used in decision scoring
- Location is NOT used in decision scoring
- Only used for regulatory validation/routing if needed

✅ **Decision Transparency:**
- Every decision includes reasoning
- Key factors clearly stated
- Confidence levels disclosed

✅ **Audit Trail:**
- Every decision logged to database
- All agent outputs recorded
- Timestamps and user/system identifiers
- Reviewable for regulatory inspection

### Regulatory Considerations

⚠️ **This is a case study implementation. Real production deployment requires:**

- **Legal Review** - Fair lending compliance, regulatory requirements
- **Fairness Audit** - Bias testing across demographics
- **Compliance Testing** - FCRA, ECOA, UDAAP requirements
- **Model Risk Review** - Model governance, validation testing
- **Documentation** - All design decisions documented
- **Testing** - Comprehensive edge case testing
- **Monitoring** - Post-deployment performance monitoring

### Important Disclaimer

> **THIS SYSTEM IS FOR EDUCATIONAL AND DEMONSTRATION PURPOSES ONLY.**
>
> It is NOT suitable for production banking use without extensive additional work:
> - Complete fairness and bias audit
> - Regulatory and legal compliance review
> - Model risk management approval
> - Integration with production banking infrastructure
> - Comprehensive staff training
> - Deployment and monitoring protocols
>
> DO NOT deploy this system to production without explicit approval from legal, compliance, risk, and fairness review teams.

## 🔍 Monitoring & Logging

### Log Locations

- **Console logs**: Real-time output in terminal
- **File logs**: `logs/loanapproval.log` (rotated, max 10MB)
- **Audit logs**: MySQL `audit_logs` table

### Log Levels

- **DEBUG** - Detailed diagnostic information
- **INFO** - Workflow progress, decisions made
- **WARNING** - Unusual conditions, retry attempts
- **ERROR** - Process failures, exceptions
- **CRITICAL** - System-level failures

## 🐛 Troubleshooting

### Common Issues

**Issue: "Cannot connect to API"**

```
Solution:
1. Verify FastAPI is running: ps aux | grep uvicorn
2. Check port 8000 is not in use: lsof -i :8000
3. Check API configuration in .env
```

**Issue: "Database connection refused"**

```
Solution:
1. Verify MySQL is running: systemctl status mysql
2. Check credentials in .env
3. Verify database exists: mysql -u root -p -e "SHOW DATABASES;"
```

**Issue: "Anthropic API key invalid"**

```
Solution:
1. Verify API key in .env
2. Check key has Claude Sonnet access
3. Verify key is not expired or rate-limited
```

**Issue: "Streamlit not loading"**

```
Solution:
1. Check Streamlit is running: ps aux | grep streamlit
2. Verify port 8501 is available
3. Check browser cache: Hard refresh (Ctrl+Shift+R)
```

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

### Database Inspection

```bash
# Connect to MySQL
mysql -u loanapp_user -p loanapproval_db

# View decisions
SELECT case_id, classification, risk_score, created_at 
FROM loan_decisions 
ORDER BY created_at DESC 
LIMIT 10;

# View audit trail
SELECT audit_id, event_type, timestamp, status 
FROM audit_logs 
WHERE case_id = 'CASE_ABC123'
ORDER BY timestamp ASC;
```

## 📚 Project Structure

```
LoanApprovalSystem/
├── config/                          # Configuration
│   └── settings.py
├── database/                        # Database layer
│   ├── connection.py
│   ├── models.py
│   └── schemas.py
├── api/                             # FastAPI service
│   ├── main.py
│   ├── routes.py
│   └── models.py
├── orchestration/                   # LangGraph workflow
│   ├── workflow.py
│   └── state.py
├── agents/                          # Agent implementations
│   ├── applicant_profile_agent.py
│   ├── financial_risk_agent.py
│   ├── loan_decision_agent.py
│   ├── compliance_agent.py
│   └── prompts.py
├── mcp_servers/                     # MCP server implementations
│   ├── applicant_db_server.py
│   ├── risk_rules_server.py
│   ├── decision_synthesis_server.py
│   └── notification_system_server.py
├── frontend/                        # Streamlit UI
│   └── streamlit_app.py
├── utils/                           # Utilities
│   ├── logging_config.py
│   ├── audit_trail.py
│   └── validators.py
├── tests/                           # Test suite
│   ├── test_validators.py
│   ├── test_api.py
│   ├── test_agents.py
│   └── test_workflow.py
├── setup_database.sql               # Database schema
├── requirements.txt                 # Dependencies
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

## 📖 Example Scenarios

### Scenario 1: Strong Applicant (Approval)

```json
{
  "applicant_id": "APP-STRONG-001",
  "age": 38,
  "income": 120000,
  "employment_type": "salaried",
  "employment_tenure_years": 8,
  "credit_score": 780,
  "loan_amount": 350000,
  "loan_tenure_months": 360,
  "existing_liabilities": 1200,
  "location": "California"
}
```

**Expected Result:** APPROVED (low risk)

### Scenario 2: Problematic Applicant (Rejection)

```json
{
  "applicant_id": "APP-RISKY-001",
  "age": 28,
  "income": 35000,
  "employment_type": "contract",
  "employment_tenure_years": 1,
  "credit_score": 520,
  "loan_amount": 200000,
  "loan_tenure_months": 360,
  "existing_liabilities": 2500,
  "location": "Texas"
}
```

**Expected Result:** REJECTED (high risk)

### Scenario 3: Mixed Signals (Manual Review)

```json
{
  "applicant_id": "APP-MIXED-001",
  "age": 45,
  "income": 65000,
  "employment_type": "self_employed",
  "employment_tenure_years": 4,
  "credit_score": 680,
  "loan_amount": 280000,
  "loan_tenure_months": 360,
  "existing_liabilities": 2000,
  "location": "Florida"
}
```

**Expected Result:** MANUAL_REVIEW (mixed signals)

## 🔗 External Resources

- [Claude API Documentation](https://docs.anthropic.com)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Model Context Protocol](https://modelcontextprotocol.io)

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🙋 Support

For issues, questions, or contributions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs in `logs/loanapproval.log`
3. Consult [README](#️-compliance--safety) compliance section
4. Test with example payloads provided above

---

**Built with ❤️ using Claude, LangGraph, and FastAPI**

*Last updated: July 2, 2024*
