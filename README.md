# ClaimResolve AI — AI-Powered Medical Claim Denial Management Platform

**ClaimResolve AI** is an enterprise-grade medical insurance claim denial management SaaS platform. It combines FastAPI, React 19, PostgreSQL/pgvector RAG architecture, LLM reasoning, and automated appeal generation with source document citations to reverse denied hospital claims.

---

## 🌟 Key Features

1. **Multi-Tenant Hospital Architecture & RBAC**
   - Organization data isolation
   - Role-Based Access Control: `Organization Admin`, `Billing Specialist`, `Reviewer`
   - Secure JWT authentication with bcrypt password hashing

2. **Enterprise Denial Operations Dashboard**
   - KPI metrics: Recovered Revenue, Active Denied Claims, Success Rate, Resolution Turnaround
   - Interactive charts: Monthly revenue recovery area trends, denial root causes pie chart, payer distribution bar charts
   - High-priority claims action queue

3. **Claims Management & Ingestion**
   - Full claim lifecycle tracking: `Uploaded` → `Processing` → `Analysis Complete` → `Appeal Drafted` → `Pending Review` → `Submitted` → `Approved` / `Rejected`
   - Manual claim creation and filtering by CARC denial codes, payers, and dates
   - Patient reference linking with masked policy numbers

4. **Document Ingestion Pipeline**
   - Multi-format parser: PDF (PyMuPDF `fitz`), DOCX, and TXT with OCR fallback for scanned letters
   - Categorization: Denial Letters, Patient Clinical Records, Payer Policy Guidelines, Billing Documents
   - Semantic chunking with page number preservation and 1536-dimensional vector embeddings

5. **5-Step AI Claim Analysis Engine**
   - **Step 1: Denial Analysis**: Extracts denial code (e.g., CO-50, CO-16), reason, and payer requirements
   - **Step 2: Clinical Evidence Retrieval**: Semantic vector search across EHR notes, labs, and operative reports
   - **Step 3: Payer Policy Retrieval**: Vector matching against governing payer clinical policy bulletins
   - **Step 4: Evidence Comparison & Gap Analysis**: Compares payer requirements against patient records, evaluates evidence strength (`Strong`, `Moderate`, `Weak`, `Insufficient`), and identifies missing clinical documentation
   - **Step 5: Evidence-Backed Appeal Generation**: Generates formal reconsideration letter with strict source document and page number citations

6. **Interactive Appeal Workspace & PDF Exporter**
   - Multi-version appeal letter editor with live draft saving
   - Administrative approval gate before submission
   - Verified Citations Table displaying exact document title, page number, and confidence score
   - Professional PDF Export powered by ReportLab (includes hospital letterhead, EOB reference table, and exhibit index)

7. **Realistic Synthetic Healthcare Dataset & Scenarios**
   - Pre-seeded with 20 synthetic patients, 30 medical claims, 5 payer policies, and 4 detailed scenarios:
     - **Scenario 1**: Medical necessity dispute with documented conservative therapy (CO-50)
     - **Scenario 2**: Missing clinical documentation with operative report attached (CO-16)
     - **Scenario 3**: Incorrect billing code / unbundling dispute (CO-4)
     - **Scenario 4**: Coverage criteria dispute with verified imaging timeline (CO-197)

---

## 🚀 Running Locally

The application is already running in your local workspace:

- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Backend REST API**: [http://localhost:8000](http://localhost:8000)
- **Swagger / OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Interactive ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Demo Credentials
- **Email**: `admin@hospital.org`
- **Password**: `Hospital123!`
- **Organization**: Memorial Regional Health System

---

## 🛠 Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, TanStack React Query v5, Lucide Icons, Recharts
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, PyMuPDF, ReportLab
- **Database & Vectors**: PostgreSQL with `pgvector` (production) / Async SQLite + Vector fallback (local sandbox)
- **AI & RAG Engine**: Provider abstraction supporting OpenAI (`gpt-4o`, `text-embedding-3-small`), Anthropic (`claude-3-5-sonnet`), and deterministic healthcare LLM engine

---

## 🐳 Running via Docker Compose

To run the complete production stack (PostgreSQL 16 with pgvector, FastAPI backend, and Nginx React frontend):

```bash
docker-compose up --build
```

Services started:
- `claimresolve-postgres`: PostgreSQL 16 with `pgvector` on port `5432`
- `claimresolve-backend`: FastAPI on port `8000`
- `claimresolve-frontend`: Nginx serving production React app on port `3000`

---

## 🧪 Running Automated Tests

To execute the automated test suite covering authentication, multi-tenant isolation, document processing, AI citation correctness, and PDF export:

```bash
cd backend
source .venv/bin/activate
pytest -v
```

All 6 test suites pass out of the box with zero external dependencies.

