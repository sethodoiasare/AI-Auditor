# AI Cyber Assurance Agent

A production-ready multi-agent AI system for evidence-based cyber security control assessment. Built on the Anthropic Claude API using a structured three-agent pipeline.

---

## Overview

The AI Cyber Assurance Agent automates the structured assessment of security controls by replicating the methodology of an expert cyber assurance auditor. Given a **control description**, a **requirement**, and **evidence**, the system evaluates whether the evidence sufficiently demonstrates compliance, identifies gaps, provides recommendations, and generates targeted follow-up questions when evidence is insufficient.

The system is designed around a strict principle: **all findings must be grounded in the provided evidence**. The agents do not hallucinate, fabricate, or assume information not present in the input.

---

## Features

| Feature | Description |
|---|---|
| **Multi-Agent Pipeline** | Three specialised agents run in sequence: Auditor → Reviewer → Questioning |
| **Evidence-Based Reasoning** | All assessments strictly derived from provided evidence — no hallucination |
| **Structured JSON Output** | Consistent, machine-readable audit results every time |
| **Intelligent Gap Detection** | Automatically identifies weaknesses, ambiguities, and missing evidence |
| **Conditional Follow-Up Questions** | Generated only when evidence is insufficient (Partially Met / Not Met) |
| **Dual Interface** | Streamlit web UI and CLI for flexible usage |
| **Prompt Caching** | Agent system prompts are cached via Anthropic's API for efficiency |
| **Production-Ready** | Structured logging, input validation, error handling, environment management |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AuditPipeline                        │
│                                                         │
│   Input → Validate → Auditor → Reviewer → Questioning   │
│                                      ↓                  │
│                               Final Output              │
└─────────────────────────────────────────────────────────┘
```

### Agent Roles

| Agent | Role | Output |
|---|---|---|
| **Auditor Agent** | Performs the initial control assessment based on control, requirement, and evidence | Initial draft JSON assessment |
| **Reviewer Agent** | Quality-reviews the auditor output, identifies missed risks, corrects weak reasoning | Strengthened JSON assessment |
| **Questioning Agent** | Generates targeted follow-up questions only when gaps exist (Partially Met / Not Met) | List of follow-up questions |

### Directory Structure

```
ai-cyber-assurance-agent/
│
├── app.py                    # Streamlit web interface
├── main.py                   # CLI entry point
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore
├── .env.example              # Environment variable template
│
├── agents/
│   ├── __init__.py
│   ├── auditor.py            # Initial control assessment agent
│   ├── reviewer.py           # Assessment review and strengthening agent
│   ├── questioning.py        # Follow-up question generation agent
│   └── pipeline.py           # Agent orchestration pipeline
│
├── prompts/
│   ├── auditor.txt           # Auditor system instructions
│   ├── reviewer.txt          # Reviewer system instructions
│   └── questioning.txt       # Questioning system instructions
│
├── utils/
│   ├── __init__.py
│   ├── formatter.py          # JSON parsing and output formatting
│   ├── validator.py          # Input validation
│   └── logger.py             # Logging configuration
│
├── models/
│   ├── __init__.py
│   └── schema.py             # Pydantic data models
│
├── data/
│   └── sample_input.json     # Sample audit input for testing
│
└── logs/                     # Auto-created on first run
    └── audit_YYYYMMDD.log
```

---

## Example Input

```json
{
  "control": "Access Control - Multi-Factor Authentication (MFA): All privileged user accounts must be protected with multi-factor authentication to prevent unauthorized access to critical systems.",
  "requirement": "All privileged users (including Global Administrators, Security Administrators, and Exchange Administrators) must authenticate using multi-factor authentication (MFA) before accessing any critical system or administrative console.",
  "evidence": "Screenshot of Azure AD Conditional Access policy showing MFA enforcement for the 'Global Administrators' group. Policy is enabled and last modified 3 months ago. No sign-in logs or MFA usage reports provided. Coverage for other privileged roles not evidenced."
}
```

## Example Output

```json
{
  "control_objective": "Ensure all privileged user accounts are protected from unauthorised access through mandatory multi-factor authentication on all critical system access attempts.",
  "requirement_assessment": "Partially Met",
  "evidence_quality": {
    "completeness": "Evidence is incomplete. Only the Global Administrators group is evidenced. Security Administrators, Exchange Administrators, and other privileged roles are not covered. No operational evidence (sign-in logs, MFA reports) has been provided.",
    "relevance": "The Conditional Access policy screenshot is directly relevant to the MFA requirement. However, its scope is limited to one privileged role, reducing its sufficiency.",
    "reliability": "A screenshot of a policy configuration is moderately reliable as design evidence. It does not confirm operational effectiveness. Sign-in logs or MFA challenge reports are required to confirm enforcement in practice."
  },
  "gaps_identified": [
    "MFA policy coverage evidenced only for Global Administrators — Security Administrators, Exchange Administrators, and other privileged roles are not addressed.",
    "No operational evidence provided (e.g., sign-in logs, MFA usage reports) to confirm the policy is enforced in practice and not bypassed.",
    "Privileged service accounts and break-glass/emergency administrator accounts are not referenced — their MFA status is unknown.",
    "Policy was last modified 3 months ago with no evidence of change management approval or regular review."
  ],
  "recommendations": [
    "Provide Conditional Access policies or equivalent evidence covering all privileged roles, not just Global Administrators.",
    "Supplement with Azure AD sign-in logs or an MFA usage/compliance report demonstrating enforcement in production.",
    "Document how privileged service accounts and break-glass accounts are handled, including any compensating controls.",
    "Provide change management records for the Conditional Access policy modification."
  ],
  "audit_opinion": "The evidence partially satisfies the MFA requirement. A Conditional Access policy enforcing MFA for Global Administrators is documented; however, coverage for other privileged roles is absent and operational effectiveness has not been demonstrated. The assessment is Partially Met pending additional evidence covering full privileged role scope and operational enforcement.",
  "follow_up_questions": [
    "Can you provide the complete list of Conditional Access policies enforcing MFA, including all privileged roles in scope?",
    "Can you provide Azure AD sign-in logs or an MFA compliance report confirming MFA challenges are being issued and completed for all privileged users?",
    "How are privileged service accounts and break-glass/emergency administrator accounts managed under the MFA policy?",
    "Has the Conditional Access policy modification 3 months ago been reviewed and approved through a formal change management process?"
  ]
}
```

---

## How to Run Locally

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai-cyber-assurance-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Open .env and add your ANTHROPIC_API_KEY
```

### 5. Run the Streamlit UI

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 6. Run the CLI

```bash
# Using the built-in sample input
python main.py

# Using a custom JSON file
python main.py --input data/sample_input.json

# Using command-line arguments
python main.py \
  --control "Access Control — MFA" \
  --requirement "All privileged users must use MFA." \
  --evidence "Conditional Access policy screenshot for Global Admins."

# Save output to a file
python main.py --output report.json
```

---

## Environment Variables

| Variable | Description | Required | Default |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | **Yes** | — |
| `MODEL` | Claude model to use | No | `claude-opus-4-6` |
| `LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | No | `INFO` |

---

## Input Schema

```json
{
  "control": "string — The security control description [C]",
  "requirement": "string — The specific requirement to be demonstrated [Dx]",
  "evidence": "string — The evidence provided to demonstrate compliance [Ex]"
}
```

## Output Schema

```json
{
  "control_objective": "string",
  "requirement_assessment": "Met | Partially Met | Not Met",
  "evidence_quality": {
    "completeness": "string",
    "relevance": "string",
    "reliability": "string"
  },
  "gaps_identified": ["string"],
  "recommendations": ["string"],
  "audit_opinion": "string",
  "follow_up_questions": ["string"]
}
```

---

## Future Improvements

| Improvement | Description |
|---|---|
| **Batch Processing** | Accept multiple controls in a single run and produce a consolidated report |
| **Evidence Upload** | Support PDF, DOCX, and image uploads with automated evidence extraction |
| **Control Framework Mapping** | Map assessments to ISO 27001, NIST CSF, SOC 2, CIS Controls |
| **Risk Scoring** | Quantitative gap severity scoring and aggregated risk posture view |
| **Audit Trail** | Persistent audit history with database storage and search |
| **Report Export** | Export audit results to PDF or Word with formatted templates |
| **Human-in-the-Loop** | Reviewer approval workflow before finalising assessments |
| **REST API** | FastAPI endpoint for enterprise integration and automation |
| **Multi-language Support** | Evidence and control input in languages other than English |

---

## Notes on AI Assessments

All assessments produced by this system are AI-generated and based solely on the evidence and context provided. They should be reviewed and validated by a qualified human auditor before being used for compliance, certification, or reporting purposes.

This system is designed to **assist** auditors, not to replace them.
