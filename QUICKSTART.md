# 🚀 Quick Start Guide

Get the Loan Approval System up and running in 5 minutes.

## Prerequisites

- Python 3.8+
- MySQL 8.0+ running locally
- Anthropic API key

## Step 1: Setup Database (2 minutes)

```bash
# Access MySQL
mysql -u root -p

# In MySQL shell:
CREATE DATABASE loanapproval_db;
CREATE USER 'loanapp_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON loanapproval_db.* TO 'loanapp_user'@'localhost';
FLUSH PRIVILEGES;
USE loanapproval_db;
SOURCE setup_database.sql;
EXIT;
```

## Step 2: Configure Environment (1 minute)

```bash
# Copy template
cp .env.example .env

# Edit .env - Replace with your values:
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# MYSQL_PASSWORD=secure_password_here
```

## Step 3: Install & Run (2 minutes)

### Terminal 1: FastAPI Server

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Streamlit UI

```bash
source venv/bin/activate
streamlit run frontend/streamlit_app.py
```

## Step 4: Test

Open http://localhost:8501 and submit a test application!

### Test Payload (Approved)

```json
{
  "applicant_id": "TEST-001",
  "age": 35,
  "income": 75000,
  "employment_type": "salaried",
  "employment_tenure_years": 5,
  "credit_score": 720,
  "loan_amount": 300000,
  "loan_tenure_months": 360,
  "existing_liabilities": 2000,
  "location": "New York, NY"
}
```

### Test via API

```bash
curl -X POST http://localhost:8000/api/v1/loan-applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "TEST-001",
    "age": 35,
    "income": 75000,
    "employment_type": "salaried",
    "employment_tenure_years": 5,
    "credit_score": 720,
    "loan_amount": 300000,
    "loan_tenure_months": 360,
    "existing_liabilities": 2000,
    "location": "New York, NY"
  }'
```

## 🎉 Success!

If you see a decision response with classification, risk score, and reasoning, the system is working!

### Next Steps

- Review the [README.md](README.md) for detailed documentation
- Check the database with: `mysql -u loanapp_user -p loanapproval_db`
- Try different test cases (see README for examples)
- Read the [Architecture](#️-architecture) section in README

### Troubleshooting

**API won't start?**
- Check port 8000 is free: `lsof -i :8000`
- Verify .env has correct API key

**Database error?**
- Verify MySQL is running: `systemctl status mysql`
- Check credentials in .env

**Streamlit won't load?**
- Hard refresh browser: Ctrl+Shift+R
- Check port 8501 is free: `lsof -i :8501`

---

🏦 **You're now running an AI-powered loan approval system!**
