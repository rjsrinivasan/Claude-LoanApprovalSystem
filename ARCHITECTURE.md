# 🏗️ System Architecture

Comprehensive guide to the Intelligent Loan Approval System architecture, components, and interactions.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Workflow Execution](#workflow-execution)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [Security Model](#security-model)
- [Scalability Considerations](#scalability-considerations)

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Tier                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Streamlit Web Application (Port 8501)            │   │
│  │   - Form submission                                │   │
│  │   - Results display                                │   │
│  │   - Chat-style interface                           │   │
│  └──────────────────┬──────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │ HTTP/JSON
┌─────────────────────┴───────────────────────────────────────┐
│                  API Tier                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ FastAPI Application (Port 8000)                    │   │
│  │  - /api/v1/loan-applications (POST)                │   │
│  │  - /api/v1/loan-applications/{case_id} (GET)       │   │
│  │  - /api/v1/health (GET)                            │   │
│  │ - Request validation                               │   │
│  │ - Response serialization                           │   │
│  └──────────────────┬──────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │ Workflow invocation
┌─────────────────────┴───────────────────────────────────────┐
│            Orchestration Tier (LangGraph)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Validate  │→ │Applicant │→ │Financial │→ │Loan      │   │
│  │Request   │  │Profile   │  │Risk      │  │Decision  │   │
│  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘   │
│                                                    │        │
│                                              ┌─────▼─────┐  │
│                                              │Compliance │  │
│                                              │Agent      │  │
│                                              └───────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │ Tool execution
┌─────────────────────┴───────────────────────────────────────┐
│            Agent & MCP Tier                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Applicant │  │Risk      │  │Decision  │  │Notif.    │   │
│  │DB Server │  │Rules Srv │  │Synth Srv │  │Sys Srv   │   │
│  │(Port     │  │(Port     │  │(Port     │  │(Port     │   │
│  │3001)     │  │3002)     │  │3003)     │  │3004)     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
┌───────┴─────────────┴─────────────┴─────────────┴─────────┐
│                  Data Tier                                 │
│              MySQL Database                               │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Tables:                                          │    │
│  │  - applicants                                    │    │
│  │  - loan_applications                             │    │
│  │  - loan_decisions                                │    │
│  │  - audit_logs                                    │    │
│  │  - notifications                                 │    │
│  │  - risk_rules                                    │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Presentation Layer

**File:** `frontend/streamlit_app.py`

```
Streamlit Application
├── Submit Tab
│   ├── Form Builder (Pydantic models)
│   ├── Input Validation
│   ├── API Integration
│   └── Result Display
├── Results Tab
│   ├── Application History
│   ├── Decision Summary
│   └── Audit Trail Display
└── Sidebar
    ├── Configuration
    └── About/Help
```

**Key Features:**
- Conversational UI for loan applications
- Real-time API integration
- Session state management
- Error handling and feedback
- Responsive design

### 2. API Layer

**Files:** `api/main.py`, `api/routes.py`, `api/models.py`

```
FastAPI Application
├── Middleware
│   ├── CORS
│   ├── Logging
│   └── Error Handling
├── Routes
│   ├── POST /api/v1/loan-applications
│   ├── GET /api/v1/loan-applications/{case_id}
│   ├── GET /api/v1/health
│   └── GET / (root)
├── Models (Pydantic)
│   ├── LoanApplicationRequest
│   ├── LoanApplicationResponse
│   └── ErrorResponse
└── Lifespan Management
    ├── Startup (DB init)
    └── Shutdown (DB cleanup)
```

**Responsibilities:**
- Input validation
- Request routing
- Response serialization
- Error handling
- OpenAPI documentation

### 3. Orchestration Layer

**Files:** `orchestration/workflow.py`, `orchestration/state.py`

```
LangGraph Workflow
├── State Management
│   ├── Input validation
│   ├── Intermediate outputs
│   ├── Final results
│   └── Error tracking
├── Nodes
│   ├── validate_application
│   ├── run_applicant_profile_agent
│   ├── run_financial_risk_agent
│   ├── run_loan_decision_agent
│   └── run_compliance_agent
├── Edges
│   ├── Linear flow for success path
│   └── Conditional routing for errors
└── Compilation
    └── StateGraph.compile()
```

**Flow Control:**
```
START
  ↓
VALIDATE → ERROR? → YES → COMPLIANCE (error) → END
  ↓ NO
APPLICANT_PROFILE (parallel start)
FINANCIAL_RISK (parallel start)
  ↓ (both complete)
LOAN_DECISION
  ↓
COMPLIANCE (persistence)
  ↓
END
```

### 4. Agent Layer

**Files:** `agents/*.py`

```
Agent Framework
├── Applicant Profile Agent
│   ├── Gets applicant info from ApplicantDB MCP
│   ├── Analyzes employment risk
│   ├── Checks application completeness
│   └── Returns: income_stability_score, employment_risk_level
├── Financial Risk Agent
│   ├── Calculates DTI ratio
│   ├── Evaluates credit risk
│   ├── Assesses loan amount risk
│   ├── Detects anomalies
│   └── Returns: dti_ratio, credit_risk_level, anomalies
├── Loan Decision Agent
│   ├── Synthesizes applicant + financial outputs
│   ├── Calls Claude for reasoning
│   ├── Applies decision thresholds
│   └── Returns: classification, risk_score, confidence, reasoning
└── Compliance Agent
    ├── Persists decision to DB
    ├── Generates case ID
    ├── Creates audit trail
    ├── Triggers notifications
    └── Returns: case_id, status
```

**Agent Communication:**
- All agents use Anthropic SDK
- Claude Sonnet 4.6 as default LLM
- JSON-based responses
- Error handling with fallbacks

### 5. MCP Server Layer

**Files:** `mcp_servers/*.py`

```
FastMCP Servers (Real Database Backend)

ApplicantDB Server (Port 3001)
├── Tools:
│   ├── get_applicant_info(applicant_id)
│   ├── analyze_employment_risk(employment_type, tenure)
│   ├── check_application_completeness(applicant_id)
│   └── analyze_income_stability(...)
└── Database: applicants table

RiskRulesDB Server (Port 3002)
├── Tools:
│   ├── fetch_risk_rules()
│   ├── calculate_dti_ratio(...)
│   ├── evaluate_credit_risk(credit_score)
│   ├── evaluate_loan_amount_risk(...)
│   └── detect_anomalies(...)
└── Database: risk_rules table

DecisionSynthesis Server (Port 3003)
├── Tools:
│   ├── synthesize_decision_inputs(...)
│   ├── apply_decision_thresholds(...)
│   └── get_decision_templates()
└── Database: None (stateless)

NotificationSystem Server (Port 3004)
├── Tools:
│   ├── persist_decision(...)
│   ├── generate_case_id()
│   ├── log_audit_trail(...)
│   └── trigger_notification(...)
└── Database: loan_decisions, audit_logs, notifications tables
```

### 6. Database Layer

**Files:** `database/models.py`, `database/connection.py`, `database/schemas.py`

```
Database Architecture
├── Connection Management
│   ├── SQLAlchemy engine
│   ├── Connection pooling (10-20 connections)
│   ├── Health checks
│   └── Automatic reconnection
├── ORM Models
│   ├── Applicant
│   ├── LoanApplication
│   ├── LoanDecision
│   ├── RiskRule
│   ├── AuditLog
│   └── Notification
└── Schemas (Pydantic)
    ├── Request models
    ├── Response models
    └── Conversion utilities
```

## Data Flow

### Complete Request-to-Response Flow

```
1. USER SUBMISSION
   └─ Streamlit form → JSON payload

2. API RECEPTION
   └─ FastAPI /loan-applications endpoint
      └─ Pydantic validation
      └─ Save to applicants table
      └─ Create loan_application record

3. WORKFLOW INITIALIZATION
   └─ LangGraph creates WorkflowState
      └─ Populates application_data

4. VALIDATION NODE
   └─ Check required fields
   └─ Validate ranges
   └─ Log audit event

5. AGENT EXECUTION (Parallel)
   ├─ Applicant Profile Agent
   │  └─ Query ApplicantDB MCP
   │  └─ Calculate income stability
   │  └─ Return profile scores
   └─ Financial Risk Agent
      └─ Query RiskRulesDB MCP
      └─ Calculate financial metrics
      └─ Detect anomalies
      └─ Return risk assessment

6. DECISION SYNTHESIS
   └─ Loan Decision Agent
      └─ Receive both agent outputs
      └─ Build Claude prompt
      └─ Call Claude Sonnet
      └─ Parse JSON response
      └─ Return classification + reasoning

7. COMPLIANCE & PERSISTENCE
   └─ Compliance Agent
      └─ Call NotificationSystem MCP
      └─ Persist to loan_decisions
      └─ Generate case_id
      └─ Create audit_logs entries
      └─ Create notification record

8. RESPONSE GENERATION
   └─ Format LoanApplicationResponse
      └─ Include case_id, classification, risk_score
      └─ Include explanation and factors
      └─ Return to API

9. UI DISPLAY
   └─ Streamlit renders response
      └─ Show decision status
      └─ Display risk score
      └─ Show key factors
      └─ Display reasoning

10. DATABASE PERSISTENCE
    └─ All decisions in loan_decisions
    └─ All events in audit_logs
    └─ All notifications in notifications
```

## Workflow Execution

### State Transitions

```
┌─────────────────┐
│  WorkflowState  │ (Pydantic model)
├─────────────────┤
│ application_    │ ← Input from API
│ data            │
│                 │
│ applicant_      │ ← From node 1
│ profile_output  │
│                 │
│ financial_risk_ │ ← From node 2
│ output          │
│                 │
│ decision_       │ ← From node 3
│ output          │
│                 │
│ compliance_     │ ← From node 4
│ output          │
│                 │
│ case_id         │ ← Final result
│ classification  │
│ risk_score      │
│ confidence_     │
│ level           │
│                 │
│ errors[]        │ ← Error tracking
│ audit_events[]  │ ← Event log
└─────────────────┘
```

### Conditional Routing

```
[Validate] 
    ↓
  Has errors?
    ├─ YES → [Compliance (error mode)] → END
    └─ NO → [Applicant Profile + Financial Risk] (parallel)
               ↓
           [Loan Decision]
               ↓
           [Compliance (success mode)]
               ↓
             END
```

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────────┐
│   applicants        │
├─────────────────────┤
│ applicant_id (PK)   │◄─┐
│ age                 │  │
│ income              │  │
│ employment_type     │  │
│ employment_tenure   │  │ One-to-Many
│ location            │  │
│ created_at          │  │
└─────────────────────┘  │
                         │
                    ┌────┴────────────────────┐
                    │                         │
        ┌───────────┴────────┐    ┌──────────┴────────────┐
        │                    │    │                       │
┌───────▼──────────┐    ┌────▼────────────┐    ┌─────────▼─────────┐
│loan_applications │    │loan_decisions   │    │notifications      │
├──────────────────┤    ├─────────────────┤    ├───────────────────┤
│application_id(PK)│    │case_id (PK)     │    │notification_id(PK)│
│applicant_id(FK)  │◄───┤application_id   │    │case_id            │
│credit_score      │    │applicant_id(FK) │    │applicant_id(FK)   │
│loan_amount       │    │classification   │    │notification_type  │
│loan_tenure_      │    │risk_score       │    │status             │
│months            │    │confidence_level │    │message            │
│existing_         │    │decision_        │    │sent_at            │
│liabilities       │    │reasoning (JSON) │    │created_at         │
│status            │    │key_factors(JSON)│    └───────────────────┘
│created_at        │    │created_at       │
└───────────────────    └─────────────────┘
                               │
                               │ References
                               │
                        ┌──────▼────────┐
                        │audit_logs     │
                        ├───────────────┤
                        │audit_id (PK)  │
                        │case_id        │
                        │event_type     │
                        │event_desc     │
                        │timestamp      │
                        │status         │
                        │metadata (JSON)│
                        └────────────────┘

┌──────────────────┐
│risk_rules        │ (Configuration table)
├──────────────────┤
│rule_id (PK)      │
│rule_name         │
│rule_type         │
│threshold_approve │
│threshold_review  │
│active            │
└──────────────────┘
```

### Sample Queries

```sql
-- Get latest decisions
SELECT case_id, applicant_id, classification, risk_score, created_at
FROM loan_decisions
ORDER BY created_at DESC
LIMIT 10;

-- Audit trail for a case
SELECT audit_id, event_type, timestamp, status
FROM audit_logs
WHERE case_id = 'CASE_ABC123'
ORDER BY timestamp ASC;

-- Decision statistics
SELECT 
  classification,
  COUNT(*) as count,
  AVG(risk_score) as avg_risk,
  AVG(confidence_level) as avg_confidence
FROM loan_decisions
WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY classification;
```

## API Design

### Request/Response Contract

```
POST /api/v1/loan-applications

Request:
{
  "applicant_id": string,
  "age": int (18-100),
  "income": float (> 0),
  "employment_type": "salaried" | "self_employed" | "contract" | "retired",
  "employment_tenure_years": int (>= 0),
  "credit_score": int (300-850),
  "loan_amount": float (> 0),
  "loan_tenure_months": int (> 0),
  "existing_liabilities": float (>= 0),
  "location": string (optional)
}

Response (200 OK):
{
  "case_id": string,
  "classification": "approved" | "rejected" | "manual_review",
  "risk_score": float (0-100),
  "confidence_level": float (0-100),
  "key_decision_factors": [
    {
      "factor": string,
      "value": string,
      "impact": "positive" | "negative" | "neutral",
      "weight": float
    }
  ],
  "explanation": {
    "summary": string,
    "applicant_profile_assessment": string,
    "financial_risk_assessment": string,
    "decision_logic": string,
    "risk_mitigation_factors": [string]
  },
  "next_steps": string,
  "created_at": ISO8601 datetime,
  "audit_trace_id": string
}

Error Response (400/500):
{
  "error": string,
  "error_code": string,
  "details": object (optional),
  "timestamp": ISO8601 datetime
}
```

## Security Model

### Data Protection

```
┌──────────────┐
│ User Input   │ (Untrusted)
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ API Input Validation     │ Pydantic models
│ - Type checking          │ - Range validation
│ - Range validation       │ - Enum validation
│ - Format validation      │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Agent Execution          │
│ - Sandboxed prompts      │
│ - Structured output      │
│ - Error handling         │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Database Operations      │ Parameterized queries
│ - Parameterized queries  │ SQLAlchemy ORM
│ - Transaction safety     │ Connection pooling
│ - Access control         │ Role-based (user)
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Response Serialization   │ JSON validation
│ - Type validation        │ Pydantic models
│ - Sensitive data mask    │ Audit trail
└──────────────────────────┘
```

### Secret Management

```
Environment Variables (.env)
├── ANTHROPIC_API_KEY → Passed to Anthropic SDK
├── MYSQL_PASSWORD → Used in connection string
├── DB_CONNECTION_STRING → Built from components
└── LOG_LEVEL → Configuration

No Secrets in:
├── Source code
├── Logs (redacted)
├── Database (encryption at rest recommended)
└── Response payloads
```

## Scalability Considerations

### Horizontal Scaling

```
Load Balancer
├─ API Instance 1
├─ API Instance 2
└─ API Instance 3
    ↓ (all share)
   DB (MySQL)

Scaling Strategy:
- Stateless API instances
- Shared database connection pool
- Request routing via load balancer
- Session state in database (if needed)
```

### Vertical Scaling

```
Performance Tuning:
├─ Connection pooling (current: 10-20)
├─ Query optimization with indexes
├─ Agent parallelization
├─ Response caching (future)
└─ Async MCP servers (future)
```

### Database Optimization

```
Indexes:
- applicant_id (search)
- case_id (lookup)
- created_at (sorting)
- classification (reporting)

Query patterns:
- Single decision lookup: O(1) indexed
- Audit trail: O(n) indexed by case_id
- Statistics: O(n) full scan (infrequent)
```

---

**This architecture is designed for clarity, maintainability, and scalability.**

For deployment considerations, see IMPLEMENTATION_NOTES.md.
