# FINTELLIGENCE — AI-Powered Financial Crime Investigation & Intelligence Platform
# suma
FINTELLIGENCE is an end-to-end, production-grade financial crime intelligence platform engineered to assist compliance officers, forensic accountants, and financial intelligence units (FIUs). It ingests bank statements across multiple institutions, normalizes transactions into a canonical schema while preserving strict account identities, runs eight deterministic financial crime detectors, maps fund flows with NetworkX, identifies circular fund cycles and multi-hop layering chains, traces FIFO fund allocations, and exposes an authorized Model Context Protocol (MCP) evidence layer to an autonomous AI investigation agent.

---

## 1. Project Overview

FINTELLIGENCE addresses the acute investigative challenge of analyzing disparate bank statements belonging to a single subject across multiple commercial banks. By decoupling deterministic mathematical analysis from probabilistic LLM synthesis, the system guarantees zero-hallucination factual grounding: financial calculations and fraud patterns are computed deterministically, while the AI agent acts as a specialized investigative assistant retrieving authorized evidence.

---

## 2. Problem Statement

Financial crime investigations routinely stall due to:
- **Disparate Statement Formats**: Digital PDFs, scanned images, Excel workbooks, and CSV exports with incompatible column aliases and date formats.
- **Account Identity Collapse**: Naive systems merge accounts under a single name, obscuring inter-account transit and circular routing.
- **Premature Data Deletion**: Discarding failed, reversed, or returned transactions, losing crucial behavioral red flags.
- **Hallucinated Financial Evidence**: General-purpose LLMs fabricating transaction IDs, balances, and suspicion scores.
- **Unexplainable Risk Scores**: "Black-box" ML classifiers that cannot withstand judicial or regulatory scrutiny.

---

## 3. Architecture

```
                    ┌───────────────────┐
                    │   React Frontend  │
                    │ (Vite, Tailwind,  │
                    │  Flow, Recharts)  │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Flask Backend   │
                    │ (Python 3.12,     │
                    │  JWT, SQLAlchemy) │
                    └─────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        File Service      Case Service     AI Service
             │                                 │
             ▼                                 ▼
       Parser / OCR                     Investigation Agent
    (fitz, pdfplumber,                         │
     openpyxl, cv2)                            ▼
             │                            LLM Provider
             ▼                         ┌───────┴───────┐
       Normalization                   ▼               ▼
             │                      Ollama          Claude
             ▼
          MySQL 8 (23 Relational Tables)
             │
             ▼
     Financial Analysis Engine
             │
     ┌───────┼────────┐
     ▼       ▼        ▼
   8       Score    Evidence Service
Detectors            │
                     ▼
              ┌──────┼──────┐
              ▼      ▼      ▼
             SQL   Graph   RAG
              │      │      │
              └──────┼──────┘
                     ▼
             18 MCP Tools
                     │
                     ▼
              Investigation Agent
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
         Q&A       Reports    Memory
                     │
                     ▼
               Human Feedback (HITL)
                     │
                     ▼
            Evaluation Framework
```

---

## 4. Technology Stack

- **Frontend**: React 18, Vite, Tailwind CSS, React Router v6, Axios, Recharts, React Flow (`reactflow`), Lucide React.
- **Backend**: Python 3.12+, Flask 3.0, Flask-SQLAlchemy 3.1, Flask-Migrate, Flask-JWT-Extended, Flask-CORS, Flask-Limiter, Pydantic v2.
- **Database**: MySQL 8.0 Community Server with PyMySQL and SQLAlchemy ORM.
- **Document Processing**: `pdfplumber`, `PyMuPDF` (`fitz`), `openpyxl`, `pandas`, `Pillow`, `OpenCV` (`cv2`), `pytesseract`.
- **Graph & Network Analytics**: `NetworkX` 3.x.
- **AI Agent & LLM**: Provider-independent `LLMProvider` abstraction supporting Ollama (local open-source models), Anthropic Claude, and a deterministic local fallback engine.
- **Tool Protocol**: Model Context Protocol (MCP) compliant tool layer.

---

## 5. Database Design

FINTELLIGENCE persists all state across 23 relational tables in MySQL 8:

1. `users`: System users, password hashes (Werkzeug PBKDF2), and roles (`admin`, `investigator`, `viewer`).
2. `persons`: Subject personal identity, PAN/SSN/Passport, address, contact details.
3. `cases`: Primary investigation cases, status, priority, and cached suspicion score.
4. `accounts`: Institutional bank accounts (`account_number`, `bank_name`, `account_type`, `currency`).
5. `bank_statements`: Document metadata, original filename, hashed secure storage path, file type, extraction method, and processing error state.
6. `transactions`: Canonical schema storing amounts, debits, credits, balances, dates, counterparties, and provenance.
7. `transaction_validation`: Validation statuses (`VALID`, `WARNING`, `INVALID`) and data discrepancy issue logs.
8. `detector_results`: Output records of the 8 detectors (trigger boolean, severity, metrics JSON, evidence).
9. `suspicious_transactions`: Foreign-keyed links connecting individual transactions to flagging detectors.
10. `fund_flow_edges`: Directed edges representing aggregated flows between accounts and counterparties.
11. `circular_flows`: Closed-loop cyclical paths (`A -> B -> C -> A`), circulating volume, and duration.
12. `circular_flow_transactions`: Transaction sequence links within a circular flow.
13. `layering_chains`: Multi-hop transit chains (`A -> B -> C -> D`) identifying layered movements.
14. `layering_chain_transactions`: Ordered transactions forming layering chains.
15. `money_trails`: FIFO fund allocations matching credit inflows to subsequent debit outflows.
16. `money_trail_links`: Step-by-step traversal links for money trails.
17. `evidence_records`: Authorized evidence objects cited by the AI investigation agent.
18. `investigations`: Investigation chat sessions scoped to case and user.
19. `investigation_messages`: User questions and structured assistant responses (`facts`, `patterns`, `evidence`, `limitations`, `next_steps`).
20. `investigation_tool_calls`: Audit of every MCP tool executed by the agent with inputs, outputs, and execution duration.
21. `investigator_feedback`: Human-in-the-loop assessments (`Correct`, `Incorrect`, `False Positive`, `Needs Review`) with comments.
22. `investigation_reports`: 17-section structured compliance reports in JSON and Markdown.
23. `audit_logs`: System and security event audit trail with automated secret sanitization.

---

## 6. Processing Pipeline

1. **Upload**: Accepts multi-statement batches (`PDF`, `scanned PDF`, `CSV`, `XLSX`, `XLS`, `PNG`, `JPG`).
2. **Parser Dispatch**:
   - Digital PDF: `pdfplumber` structured table extraction and `PyMuPDF` text streams.
   - Scanned PDF / Images: Page rendering -> OpenCV preprocessing (grayscale, noise reduction, Otsu thresholding) -> Tesseract OCR.
   - CSV / Excel: Dialect detection, column alias matching, and automated header discovery.
3. **Canonical Normalization**: Standardizes diverse bank terms (`Withdrawal`, `Dr`, `Debit` -> `debit`; `Deposit`, `Cr`, `Credit` -> `credit`).
4. **Validation & Status Classification**:
   - Classifies status into `SUCCESS`, `FAILED`, `REVERSED`, `RETURNED`, `REFUNDED`, `PENDING`, `UNKNOWN`.
   - Records validation issues without silently discarding records.
5. **Detection & Scoring**: Runs all 8 detectors and computes the explainable Suspicion Score.
6. **Graph Traversal**: Builds NetworkX graph, extracts simple cycles, DFS layering paths, and computes FIFO trails.
7. **Evidence Persistence**: Records all findings into `evidence_records`.

---

## 7. Eight Deterministic Financial Crime Detectors

1. **Large Transaction Detector**: Flags transactions exceeding configured threshold (default: ₹50,000).
2. **Structuring Detector**: Flags clusters of repeated transactions near or below regulatory reporting thresholds (₹40,000–₹50,000) within 7 days. Strictly phrases findings as: *"Transaction pattern is consistent with the configured structuring rule."*
3. **Transaction Velocity Detector**: Detects rapid movement where incoming credits are followed by outgoing debits within a configurable window (default: 3,600 seconds).
4. **Pass-Through Detector**: Identifies accounts where outgoing funds constitute a high ratio (>= 90%) of recent incoming funds within 48 hours.
5. **Dormant Account Revival Detector**: Identifies accounts with prolonged inactivity (>= 90 days) followed by sudden high-value revival transactions (>= ₹20,000).
6. **Cash Cycling Detector**: Detects matching or near-identical reciprocal cash/fund movements (within 80%–95% volume match) occurring within 24 hours.
7. **High-Risk Time Detector**: Configurable monitoring window (default: 00:00 to 05:00 AM) identifying unusual off-hours disbursements without unsupported behavioral claims.
8. **Beneficiary Burst Detector**: Flags rapid disbursement fan-out to 4 or more distinct counterparties within 24 hours with individual amounts exceeding ₹5,000.

---

## 8. Suspicion Scoring

The Suspicion Score is an explainable **Investigation Risk Indicator** (0 to 100). It is strictly NOT described as a "probability of fraud".

Configurable Weights:
- Large Transaction: 10
- Structuring: 20
- Transaction Velocity: 15
- Pass-Through: 15
- Dormant Revival: 10
- Cash Cycling: 15
- High-Risk Time: 5
- Beneficiary Burst: 10
**Maximum Score**: 100.0

*Rule*: The AI investigation agent NEVER recalculates this score; it only retrieves and explains the deterministic score.

---

## 9. Graph Analysis

Using NetworkX:
- **Nodes**: Verified bank accounts and external counterparties.
- **Edges**: Directed transactions weighted by volume and count.
- **Circular Flows**: Detects closed-loop paths (`A -> B -> C -> A`) up to 5 hops, calculating circulating bottleneck volume and cycle duration in days.
- **Layering Chains**: Discovers multi-hop transit paths (`A -> B -> C -> D`) using DFS traversal, measuring hops, transit duration in hours, and intermediary conduits.

---

## 10. FIFO Money Trail

FINTELLIGENCE implements First-In-First-Out fund matching:
- Chronological credits entering an account are depleted sequentially against subsequent debits.
- Each link records source transaction, transit account, destination transaction, and allocated amount.
- *Mandatory Disclosure*: Reports explicitly state: *"FIFO allocation indicates temporal sequencing of fund availability and dispersal. It does not definitively prove physical currency provenance."*

---

## 11. Evidence Layer

An abstraction service (`EvidenceService`) mediates all access between the database/graph layers and the AI agent. The AI agent never executes arbitrary SQL or touches raw storage paths.

Evidence format:
- `evidence_id`, `case_id`, `entity_type`, `entity_id`, `source`, `source_statement`, `source_page`, `transaction_id`, `evidence_type`, `evidence_data`, `created_at`.

---

## 12. Retrieval Architecture

Hybrid Retrieval Strategy:
- **SQL Retrieval**: Structured financial facts (transactions, balances, scores, dates, accounts, statements, history).
- **Graph Retrieval**: Relational account topologies, fund flows, circular loops, layering chains, and FIFO trails.
- **Vector / Text RAG**: Unstructured case notes, police reports, and regulatory documentation. Vector search is strictly prohibited from serving authoritative transaction figures.

---

## 13. MCP Architecture

18 Model Context Protocol compliant tools registered:
- `get_case`
- `get_person`
- `get_accounts`
- `get_statements`
- `get_statement`
- `get_transactions`
- `get_transaction`
- `search_transactions`
- `search_statements`
- `get_suspicious_transactions`
- `get_detector_results`
- `get_detector_result`
- `get_related_transactions`
- `get_fund_flow`
- `get_circular_flows`
- `get_layering_chains`
- `get_money_trail`
- `get_investigation_history`

---

## 14. AI Agent Architecture

The investigation agent executes a multi-turn reasoning loop:
1. Receives investigator inquiry with case context.
2. Selects minimum appropriate MCP tools dynamically (never blindly calls all tools).
3. Executes tools via authorized `EvidenceService`.
4. Synthesizes a grounded response formatted as:
   - `ANSWER`
   - `FACTS`
   - `DETECTED PATTERNS`
   - `EVIDENCE` (Citations with transaction ID, statement filename, and page)
   - `INTERPRETATION`
   - `LIMITATIONS`
   - `NEXT INVESTIGATION STEPS`
5. Stores conversation, tool calls, and execution metrics in investigation memory.

---

## 15. Ollama Setup (Default Local LLM)

FINTELLIGENCE defaults to local Ollama execution without requiring paid APIs:
1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull the default model:
   ```bash
   ollama pull llama3:8b
   ```
3. Ensure Ollama is running at `http://localhost:11434`.
4. Configure in `.env`:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3:8b
   ```
*Note*: If Ollama is offline or not installed, the platform automatically utilizes its high-fidelity deterministic engine so that testing and investigations never fail.

---

## 16. Optional Claude Setup

To configure Anthropic Claude:
1. Obtain an API key from Anthropic Console.
2. Configure in `.env`:
   ```env
   LLM_PROVIDER=claude
   ANTHROPIC_API_KEY=sk-ant-api03-...
   CLAUDE_MODEL=claude-3-5-sonnet-20241022
   ```

---

## 17. Frontend Setup

```bash
cd frontend
npm install
npm run build
npm run dev
```
The React frontend starts at `http://localhost:5173`.

---

## 18. Backend Setup

```bash
cd backend
py -m pip install -r requirements.txt
```

---

## 19. MySQL Setup

Ensure MySQL 8.0 is running on localhost (port 3306):
```sql
CREATE DATABASE IF NOT EXISTS fintelligence CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 20. Environment Variables

Create `backend/.env` (or copy from `.env.example`):
```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/fintelligence
JWT_SECRET_KEY=fintelligence_jwt_super_secret_key_2026_change_in_prod
SECRET_KEY=fintelligence_flask_session_secret_key_2026

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# Optional Claude configuration
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-3-5-sonnet-20241022

UPLOAD_FOLDER=uploads
MAX_UPLOAD_SIZE_MB=25
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## 21. Running Locally

1. **Seed Database with Multi-Statement Case**:
   ```powershell
   $env:PYTHONPATH="backend"
   py backend/sample_data/seed_database.py
   ```
2. **Start Backend Server**:
   ```powershell
   $env:PYTHONPATH="backend"
   py backend/run.py
   ```
   Runs on `http://localhost:5000`.
3. **Start Frontend Server**:
   ```powershell
   cd frontend
   npm run dev
   ```
   Opens at `http://localhost:5173`.
4. **Log in**:
   - Username: `investigator`
   - Password: `password123`

---

## 22. Running Tests

Run the full pytest suite (16 tests including detectors, parsers, auth, and evaluation suite):
```powershell
$env:PYTHONPATH="backend"
py -m pytest backend/tests/ -v
```

---

## 23. Evaluation Methodology

The agent evaluation suite (`backend/tests/test_evaluation_suite.py`) verifies:
- **Trap Case Resistance**: When asked about non-existent transaction `T999`, agent strictly returns *"Transaction T999 was not found in the available case evidence"* without hallucinating.
- **Cycle Non-Existence**: When queried for a circular loop with an arbitrary account `999999`, agent accurately answers that no such cycle exists.
- **Tool Selection Accuracy**: Verifies that minimum relevant MCP tools are dispatched dynamically.
- **Evidence Grounding Rate**: Confirms citations reference real statement files and pages.
- **Failed Transaction Integrity**: Confirms failed and reversed transactions are never included in money flow calculations.

---

## 24. Security Considerations

- **Authentication**: JWT access tokens with 24-hour expiration.
- **Password Security**: PBKDF2 with SHA-256 via Werkzeug.
- **Case Isolation**: SQL queries are strictly foreign-keyed and filtered by `case_id`.
- **Secret Sanitization**: Passwords, API tokens, and secrets are automatically scrubbed from audit logs.
- **File System Protection**: Stored filenames use random UUID prefixes; source paths are never exposed to the frontend.

---

## 25. Limitations

- Forensic scope is bounded strictly by the statement date ranges and banks uploaded to each case.
- Cash hand-to-hand transactions without recorded bank deposit or withdrawal cannot be tracked.
- OCR accuracy is subject to scan resolution, orientation, and image quality.

---

## 26. Future Improvements

- Automated SWIFT / MT940 statement parser plugin.
- Distributed Celery / Redis task queue for massive statement archives (> 1,000 pages).
- Native sidecar container integration for standalone enterprise MCP clients.
