# AI Cyber Assurance Agent — Architecture & Developer Handover

> This document covers the complete system architecture, logic flows, data contracts, and extension points. It is intended for any developer picking this project up fresh.

---

## Table of Contents

1. [What This System Does](#1-what-this-system-does)
2. [Technology Stack](#2-technology-stack)
3. [Directory Map](#3-directory-map)
4. [High-Level Architecture](#4-high-level-architecture)
5. [Data Flow — End to End](#5-data-flow--end-to-end)
6. [Agent Pipeline Logic](#6-agent-pipeline-logic)
7. [Each Agent Explained](#7-each-agent-explained)
8. [Data Contracts (Schemas)](#8-data-contracts-schemas)
9. [Utility Layer](#9-utility-layer)
10. [The Two Interfaces](#10-the-two-interfaces)
11. [Environment & Configuration](#11-environment--configuration)
12. [Error Handling Map](#12-error-handling-map)
13. [How to Extend the System](#13-how-to-extend-the-system)
14. [Key Design Decisions](#14-key-design-decisions)

---

## 1. What This System Does

The AI Cyber Assurance Agent automates the assessment of security controls. Given three inputs — a **control description**, a **requirement**, and **evidence** — it decides whether the evidence demonstrates compliance, identifies gaps, makes recommendations, and generates targeted follow-up questions when evidence is insufficient.

The output is a structured JSON report with seven fields:

| Field | Type | Description |
|---|---|---|
| `control_objective` | string | What the control aims to achieve |
| `requirement_assessment` | `"Met"` / `"Partially Met"` / `"Not Met"` | The verdict |
| `evidence_quality` | object | Completeness, relevance, reliability scores |
| `gaps_identified` | string[] | Specific evidence gaps |
| `recommendations` | string[] | Actionable remediation steps |
| `audit_opinion` | string | 2–4 sentence professional opinion |
| `follow_up_questions` | string[] | Questions for the auditee (empty if Met) |

---

## 2. Technology Stack

| Component | Technology | Why |
|---|---|---|
| AI / LLM | Anthropic Claude (`claude-opus-4-6`) | Multi-agent reasoning via the Messages API |
| Web UI | Streamlit | Rapid, no-JS Python web interface |
| Data validation | Pydantic v2 | Schema enforcement at the boundary |
| Environment management | python-dotenv | `.env` file for secrets |
| Spreadsheet parsing | openpyxl + csv (stdlib) | Read `.xlsx` and `.csv` control sheets |
| PDF parsing | pypdf | Extract text from PDF evidence files |
| Image OCR | Pillow + pytesseract | Extract text from screenshot evidence |
| Logging | Python stdlib `logging` | Console + rotating daily file logs |

Python version required: **3.10+** (uses `X | Y` union syntax and `match/case` in type hints).

---

## 3. Directory Map

```
ai-cyber-assurance-agent/
│
├── app.py                    # Streamlit web UI — the main user interface
├── main.py                   # CLI entry point — runs the pipeline from the terminal
├── requirements.txt          # All Python dependencies (pip install -r requirements.txt)
├── .env                      # Secrets — NEVER commit this file
├── .env.example              # Template showing required env vars (no real keys)
│
├── agents/                   # The three AI agents + the pipeline that runs them
│   ├── pipeline.py           # AuditPipeline — orchestrates agents in sequence
│   ├── auditor.py            # AuditorAgent — first-pass control assessment
│   ├── reviewer.py           # ReviewerAgent — quality review and strengthening
│   └── questioning.py        # QuestioningAgent — follow-up question generation
│
├── prompts/                  # System prompt templates injected into each agent
│   ├── auditor.txt           # Auditor instructions + JSON output format
│   ├── reviewer.txt          # Reviewer instructions + JSON output format
│   └── questioning.txt       # Questioning instructions + JSON array format
│
├── models/
│   └── schema.py             # Pydantic models: AuditInput, AuditOutput, EvidenceQuality
│
├── utils/
│   ├── formatter.py          # JSON parsing (robust, handles malformed responses)
│   ├── validator.py          # Input validation against AuditInput schema
│   └── logger.py             # Logger setup — console + daily file in logs/
│
├── data/
│   ├── sample_input.json     # Pre-built MFA example for testing
│   └── uploaded_controls.*   # Persisted last-uploaded spreadsheet (auto-created)
│
└── logs/
    └── audit_YYYYMMDD.log    # Daily rotating log file (auto-created on first run)
```

---

## 4. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
│                                                                 │
│   ┌──────────────────────┐      ┌──────────────────────────┐   │
│   │   Streamlit Web UI   │      │      CLI (main.py)       │   │
│   │      (app.py)        │      │    python main.py        │   │
│   └──────────┬───────────┘      └────────────┬─────────────┘   │
└──────────────┼──────────────────────────────┼─────────────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       VALIDATION LAYER                          │
│             utils/validator.py → models/schema.py               │
│        Pydantic: type checks + minimum length enforcement        │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT PIPELINE (pipeline.py)                  │
│                                                                 │
│   ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│   │   Auditor   │───▶│   Reviewer   │───▶│   Questioning    │  │
│   │   Agent     │    │   Agent      │    │   Agent          │  │
│   └─────────────┘    └──────────────┘    └──────────────────┘  │
│                                                  │              │
│                         Merge follow_up_questions into output   │
└──────────────────────────────────────────────────┼─────────────┘
                                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANTHROPIC CLAUDE API                          │
│              Each agent makes one API call                       │
│           System prompts use ephemeral cache_control             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow — End to End

```
USER INPUT
  control (str)
  requirement (str)
  evidence (str)
       │
       ▼
validate_input()               ← utils/validator.py
  Pydantic AuditInput model
  min-length business checks
       │
       ├── FAIL ──▶ ValueError raised → shown to user
       │
       ▼
AuditorAgent.assess()          ← agents/auditor.py
  Formats auditor.txt prompt with {control, requirement, evidence}
  Calls Claude API (max_tokens=2048)
  parse_json_response(raw_text) → dict
       │
       ▼
ReviewerAgent.review()         ← agents/reviewer.py
  Formats reviewer.txt prompt with original inputs + auditor JSON
  Calls Claude API (max_tokens=2048)
  parse_json_response(raw_text) → dict (refined assessment)
       │
       ▼
QuestioningAgent.generate_questions()   ← agents/questioning.py
  Checks: assessment in {"Partially Met", "Not Met"} AND gaps exist
       │
       ├── SKIP ──▶ returns []   (if "Met" or no gaps)
       │
       ▼
  Formats questioning.txt prompt with gaps + assessment
  Calls Claude API (max_tokens=1024)
  parse_json_list(raw_text) → list[str]
       │
       ▼
Merge: reviewed_output["follow_up_questions"] = questions
       │
       ▼
FINAL OUTPUT dict
  returned to app.py or main.py
  displayed in UI tabs / printed to terminal / written to JSON file
```

---

## 6. Agent Pipeline Logic

```
pipeline.run(input_data)
│
├── Step 0: validate_input(input_data)
│     ├── OK  → AuditInput object
│     └── ERR → raise ValueError (stops pipeline)
│
├── Step 1: auditor.assess(audit_input)
│     └── Returns: initial_assessment dict
│
├── Step 2: reviewer.review(audit_input, initial_assessment)
│     └── Returns: reviewed_assessment dict
│
└── Step 3: questioner.generate_questions(audit_input, reviewed_assessment)
      │
      ├── assessment == "Met" AND no gaps?
      │     └── Return []   (no API call made)
      │
      ├── no gaps at all?
      │     └── Return []   (no API call made)
      │
      └── gaps exist AND assessment is "Partially Met" or "Not Met"?
            └── Call API → Return list[str]
```

**Total API calls per audit run: 2 or 3**
- Always: Auditor (1) + Reviewer (1)
- Conditional: Questioning (1) — only when evidence is insufficient

---

## 7. Each Agent Explained

### AuditorAgent (`agents/auditor.py`)

**Role:** First-pass assessment. Acts as a junior auditor doing the initial review.

**Input:** `AuditInput` (control, requirement, evidence)

**Output:** JSON dict with all 7 fields (`follow_up_questions` is always `[]`)

**System prompt persona:**
> "You are a senior cyber assurance auditor... You never fabricate, assume, or speculate. You always return valid JSON."

**Prompt file:** `prompts/auditor.txt` — contains 6-step assessment instructions and the exact JSON schema to return.

**API call config:**
- `max_tokens`: 2048
- `cache_control`: `ephemeral` on system prompt (cached across calls)

---

### ReviewerAgent (`agents/reviewer.py`)

**Role:** Quality reviewer. Acts as a senior manager checking the auditor's work. Can tighten verdicts, add missed gaps, and strengthen reasoning.

**Input:** `AuditInput` + `auditor_output` dict (as JSON string embedded in the prompt)

**Output:** Refined JSON dict (same shape as Auditor output, `follow_up_questions` always `[]`)

**System prompt persona:**
> "You are a senior cyber assurance review manager... identify missed risks, correct weak reasoning, and ensure opinions are defensible."

**Prompt file:** `prompts/reviewer.txt` — 5-step review instructions. Explicitly told to leave `follow_up_questions` empty (Questioning Agent handles this).

**Key behaviour:** Can only use information present in the original evidence — cannot introduce new facts.

---

### QuestioningAgent (`agents/questioning.py`)

**Role:** Generates targeted, answerable follow-up questions to obtain missing evidence.

**Input:** `AuditInput` + `reviewed_output` dict (uses `requirement_assessment` and `gaps_identified`)

**Output:** `list[str]` — 0 to 5 questions, or empty list

**System prompt persona:**
> "You generate targeted, specific, and answerable follow-up questions only when evidence is clearly insufficient."

**Prompt file:** `prompts/questioning.txt` — strict rules: max 5 questions, no vague questions, no questions if evidence already answers them.

**Skip logic (no API call made if):**
- Assessment is `"Met"` and no gaps
- `gaps_identified` list is empty

---

## 8. Data Contracts (Schemas)

### Input: `AuditInput` (`models/schema.py`)

```python
class AuditInput(BaseModel):
    control: str       # min_length=1, stripped of whitespace
    requirement: str   # min_length=1, stripped of whitespace
    evidence: str      # min_length=1, stripped of whitespace
```

Additional business-logic minimums enforced in `validator.py`:
- `control`: 10 characters minimum
- `requirement`: 10 characters minimum
- `evidence`: 5 characters minimum

### Output: `AuditOutput` (`models/schema.py`)

```python
class AuditOutput(BaseModel):
    control_objective: str
    requirement_assessment: str          # "Met" | "Partially Met" | "Not Met"
    evidence_quality: EvidenceQuality    # completeness, relevance, reliability
    gaps_identified: List[str]
    recommendations: List[str]
    audit_opinion: str
    follow_up_questions: List[str]       # empty if assessment is Met
```

> Note: The pipeline works with plain `dict` objects at runtime, not Pydantic model instances. The `AuditOutput` model exists for documentation and type reference. Pydantic validation is only enforced on **input** via `validate_input()`.

---

## 9. Utility Layer

### `utils/formatter.py` — JSON Parsing

Claude sometimes wraps JSON in markdown code blocks or adds prose. `parse_json_response()` handles all of this with 6 fallback strategies:

1. Direct `json.loads()`
2. Extract from ` ```json ... ``` ` block
3. Extract from ` ``` ... ``` ` block (no language tag)
4. Find balanced `{ }` in the text
5. Reconstruct if the model dropped outer braces
6. Parse bare `key: value` lines

`parse_json_list()` does the same for arrays (used by the Questioning Agent).

**`load_prompt(name)`** — reads `prompts/{name}.txt` and returns the template string. Called once per agent on init.

---

### `utils/validator.py` — Input Validation

Wraps Pydantic validation in a tuple-return pattern so callers don't need try/except:

```python
audit_input, error = validate_input(data)
if error:
    raise ValueError(error)
```

Returns `(AuditInput, None)` on success, `(None, error_str)` on failure.

---

### `utils/logger.py` — Logging

Every module calls `get_logger(__name__)`. Each logger gets:
- **Console handler**: level from `LOG_LEVEL` env var (default `INFO`)
- **File handler**: always `DEBUG`, writes to `logs/audit_YYYYMMDD.log`

Handlers are only added once (idempotency check prevents duplicate log lines if `get_logger` is called multiple times for the same module name).

---

## 10. The Two Interfaces

### Streamlit Web UI (`app.py`)

**Session state** — Streamlit re-runs the entire script on every interaction. State is preserved via `st.session_state`:

| Key | Type | Purpose |
|---|---|---|
| `pipeline` | `AuditPipeline` | Shared pipeline instance (initialised once per session) |
| `form_control` | str | Bound to the Control text area |
| `form_requirement` | str | Bound to the Requirement text area |
| `form_evidence` | str | Bound to the Evidence text area |
| `audit_result` | dict or None | Last successful audit result |
| `audit_error` | str or None | Last error message |
| `spreadsheet_rows` | list[dict] | Parsed rows from uploaded spreadsheet |
| `spreadsheet_file_name` | str | Name of last uploaded spreadsheet |
| `sheet_row_index` | int | Selected row index from spreadsheet |
| `uploaded_evidence_names` | list[str] | Names of uploaded evidence files |

**Spreadsheet persistence** — When a spreadsheet is uploaded, it is saved to `data/uploaded_controls.{csv|xlsx}`. On next page load, it is auto-reloaded so the user doesn't need to re-upload after a refresh.

**Evidence file support:**

| Format | Processing |
|---|---|
| `.txt`, `.md` | Decoded as UTF-8 |
| `.csv` | Parsed row by row, joined as comma-separated text |
| `.json` | Pretty-printed JSON |
| `.pdf` | Text extracted via `pypdf` |
| `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff` | OCR via `pytesseract` (requires Tesseract installed on OS) |

**Column normalisation for spreadsheets** — `_normalize_spreadsheet_row()` maps many possible column header variations to the three canonical fields:
- `control`, `control_name`, `control_description`, `c`, `control_label` → `control`
- `requirement`, `detailed_adequacy_requirements`, `dx`, `adequacy` → `requirement`
- `evidence`, `evidence_requirements`, `ex` → `evidence`

---

### CLI (`main.py`)

**Input modes** (in priority order):
1. `--control`, `--requirement`, `--evidence` flags (inline text)
2. `--input path/to/file.json` (JSON file)
3. No arguments → defaults to `data/sample_input.json`

**Output modes:**
1. Formatted human-readable report printed to stdout (always)
2. Raw JSON printed to stdout after the report
3. `--output report.json` flag saves JSON to a file

---

## 11. Environment & Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic API key from console.anthropic.com |
| `MODEL` | No | `claude-opus-4-6` | Claude model to use |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |

All variables are loaded from `.env` via `python-dotenv` at startup.

**To use a different Claude model**, set `MODEL=claude-sonnet-4-6` in `.env`. All three agents use the same model (set centrally in `AuditPipeline.__init__`).

---

## 12. Error Handling Map

| Where | What can go wrong | What happens |
|---|---|---|
| `validate_input()` | Missing fields, too short | Returns error string → `ValueError` raised |
| Any agent | `ANTHROPIC_API_KEY` not set | `ValueError` raised in `AuditPipeline.__init__` |
| Any agent | API call fails | `anthropic.APIError` propagates up |
| Any agent | Claude returns malformed JSON | `parse_json_response()` tries 6 fallbacks; raises `ValueError` if all fail |
| `app.py` | Any `ValueError` | Shown as `st.error()` in UI |
| `app.py` | Any other exception | Shown as unexpected error message |
| `main.py` | `ValueError` | Printed to stderr, `sys.exit(1)` |
| `main.py` | Other exception | Printed to stderr, `sys.exit(1)` |
| Evidence upload (UI) | Unsupported file type | Warning shown, file skipped |
| Evidence upload (UI) | Tesseract not installed | RuntimeError shown as warning |
| Spreadsheet upload | Parse error | Warning shown, returns empty list |

---

## 13. How to Extend the System

### Add a new agent

1. Create `agents/new_agent.py` following the pattern of `auditor.py`
2. Create `prompts/new_agent.txt` with instructions and expected JSON format
3. Add the agent to `pipeline.py`:
   - Import and instantiate in `AuditPipeline.__init__`
   - Call it in the correct sequence within `AuditPipeline.run()`
4. If the agent produces new output fields, add them to `AuditOutput` in `models/schema.py`

### Change the model

In `.env`:
```
MODEL=claude-sonnet-4-6
```

All three agents use the same model. To use different models per agent, pass `model` as a parameter to each agent's `__init__` instead of using the shared `self.model`.

### Add a new evidence file format (UI)

In `app.py`, extend `_load_evidence_file()`:
```python
if filename.endswith(".docx"):
    # parse .docx here
    return extracted_text
```
Also add the extension to the `type=None` file uploader check near line 599.

### Add a new spreadsheet column mapping

In `app.py`, extend `_normalize_spreadsheet_row()`. Add new header variations to the relevant `if` block (control, requirement, or evidence).

### Switch output format (CLI)

In `main.py`, extend `print_report()` or add a new `--format` argument to output CSV, Markdown, or HTML alongside the existing JSON.

---

## 14. Key Design Decisions

**Why three agents instead of one?**
A single prompt asking for a full assessment tends to be inconsistent. Splitting into Auditor (draft) → Reviewer (critique) → Questioning (targeted gaps) mirrors how real audit teams work and produces more rigorous output.

**Why are system prompts cached?**
Each agent uses `cache_control: ephemeral` on its system prompt. This tells Anthropic's API to cache the prompt prefix, reducing latency and token cost on repeated calls with the same agent instructions. The user message (with the actual control/evidence) changes every time but the system role stays the same.

**Why does the pipeline use plain dicts instead of Pydantic models throughout?**
Strict Pydantic validation on Claude's output would break when the model returns a field name with slightly different casing or adds an unexpected key. Using dicts with `.get()` calls makes the pipeline tolerant of minor response variation. Pydantic is only enforced on user input (where we control the format).

**Why is `follow_up_questions` handled separately?**
The Reviewer is explicitly told to leave `follow_up_questions` as `[]`. If the Reviewer generated questions, it might generate them based on assessment reasoning rather than evidence gaps. Keeping it separate ensures questions are always tied to specific identified gaps.

**Why is the spreadsheet persisted to disk?**
Streamlit re-runs the whole script on every interaction. Without persisting the uploaded file to `data/uploaded_controls.*`, users would lose their loaded spreadsheet on every page refresh.
