# Mini-ERP Platform

A full-stack Enterprise Resource Planning platform built as a portfolio project demonstrating progressive AI/ML integration — from basic CRUD through Machine Learning, Deep Learning, RAG/LLM, and Agentic AI.

**Live Demo:** `http://34.13.57.203:3000` &nbsp;|&nbsp; **API Docs:** `http://34.13.57.203:8000/docs`

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI · Python 3.11 · SQLAlchemy 2.0 (async) · Alembic |
| **Database** | PostgreSQL 15 |
| **Cache / Queue** | Redis 7 · Celery |
| **ML** | scikit-learn · imbalanced-learn · pandas · NumPy · joblib |
| **Frontend** | React 18 · TypeScript · Vite · Tailwind CSS |
| **State / Data** | Zustand · TanStack Query · React Hook Form |
| **Infrastructure** | Docker · Docker Compose · GCP (free tier) · Nginx |

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| **Week 0** | GCP setup, CI/CD, DB schema, RBAC | ✅ Done |
| **Phase 1** | MVP ERP — Workforce, Payroll, AP, Expenses, Procurement, GL | ✅ Done |
| **Phase 2** | Machine Learning — Attrition, Expense Violations, Payroll Anomaly, Invoice Classifier | ✅ Done |
| **Phase 3** | Deep Learning — LSTM Budget Forecaster, CNN Invoice Image Classifier | ⏳ Pending |
| **Phase 4** | RAG + LLM — Duplicate Invoice Detection, Finance Chat, OCR Pipeline | ⏳ Pending |
| **Phase 5** | AI Agents — Invoice Agent, Expense Audit Agent, Onboarding Agent | ⏳ Pending |
| **Phase 6** | Agentic Networks — Financial Close Network, Workforce Planning Network | ⏳ Pending |
| **Week 11** | Polish, Docs, Portfolio Deploy | ⏳ Pending |

---

## Architecture

### Current State — Phase 2 (Machine Learning)

```mermaid
graph TB
    subgraph Client["Browser / Client"]
        FE["React 18 + TypeScript\nVite · Tailwind CSS\nZustand · TanStack Query"]
    end

    subgraph Gateway["Gateway"]
        NG["Nginx\n(reverse proxy)"]
    end

    subgraph Backend["FastAPI Backend (Python 3.11)"]
        API["REST API\n/api/v1/*"]
        AUTH["JWT + RBAC\nauth.py"]
        SVC["Business Logic\nservices/"]
        ML["ML Layer\nscikit-learn · joblib\nSMOTE · TF-IDF"]
    end

    subgraph Storage["Storage"]
        PG["PostgreSQL 15\n8 schemas"]
        RD["Redis 7\ncache / queue"]
        FS["File System\n/app/models_store\n.joblib artifacts"]
    end

    subgraph Workers["Background Workers"]
        CW["Celery Worker\nasync tasks"]
    end

    FE -->|HTTP| NG
    NG -->|proxy :8000| API
    NG -->|proxy :3000| FE
    API --> AUTH
    API --> SVC
    API --> ML
    SVC --> PG
    ML --> PG
    ML --> FS
    API --> RD
    RD --> CW
    CW --> PG

    style Client fill:#dbeafe,stroke:#3b82f6
    style Backend fill:#dcfce7,stroke:#16a34a
    style Storage fill:#fef9c3,stroke:#ca8a04
    style Workers fill:#fce7f3,stroke:#db2777
    style Gateway fill:#f3f4f6,stroke:#6b7280
```

### Future State — Phase 6 (Agentic AI Platform)

```mermaid
graph TB
    subgraph Client["Browser / Client"]
        FE["React Frontend\n+ Chat UI\n+ Agent Console"]
    end

    subgraph Gateway["Gateway"]
        NG["Nginx + Auth Middleware"]
    end

    subgraph Backend["FastAPI Backend"]
        API["REST API\n/api/v1/*"]
        ML["Phase 2 — ML\nAttrition · Anomaly\nViolation · Classifier"]
        DL["Phase 3 — Deep Learning\nLSTM Budget Forecaster\nCNN Invoice Classifier"]
        RAG["Phase 4 — RAG + LLM\nDuplicate Invoice\nFinance Chat · OCR"]
        AGT["Phase 5 — AI Agents\nInvoice Agent\nExpense Audit Agent\nOnboarding Agent"]
        NET["Phase 6 — Agentic Networks\nFinancial Close Network\nWorkforce Planning Network"]
    end

    subgraph Storage["Storage"]
        PG["PostgreSQL 15"]
        RD["Redis 7"]
        FS["Model Store\n.joblib / .pt / .onnx"]
        VDB["Vector DB\n(pgvector / Chroma)"]
        OBJ["Object Store\nInvoice images · PDFs"]
    end

    subgraph LLM["LLM / Embeddings"]
        LLM_API["Anthropic Claude\n/ OpenAI API"]
    end

    subgraph Workers["Workers"]
        CW["Celery\nasync tasks"]
        LG["LangGraph\nagent runtime"]
    end

    FE --> NG --> API
    API --> ML & DL & RAG & AGT & NET
    ML & DL --> FS
    RAG --> VDB & OBJ & LLM_API
    AGT --> LG & LLM_API
    NET --> LG & LLM_API
    API --> RD --> CW
    CW & LG --> PG

    style Client fill:#dbeafe,stroke:#3b82f6
    style Backend fill:#dcfce7,stroke:#16a34a
    style Storage fill:#fef9c3,stroke:#ca8a04
    style Workers fill:#fce7f3,stroke:#db2777
    style LLM fill:#ede9fe,stroke:#7c3aed
    style Gateway fill:#f3f4f6,stroke:#6b7280
```

> **Note:** Both diagrams are updated as each phase is completed.

---

## Repository Structure

```
mini-erp/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # FastAPI routers
│   │   │   ├── auth.py
│   │   │   ├── workforce.py
│   │   │   ├── payroll.py
│   │   │   ├── accounts_payable.py
│   │   │   ├── expenses.py
│   │   │   ├── procurement.py
│   │   │   ├── general_ledger.py
│   │   │   ├── admin.py
│   │   │   └── mlops.py
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic
│   │   ├── ml/
│   │   │   ├── features/        # Feature engineering per model
│   │   │   ├── models/          # ML model train + predict functions
│   │   │   └── pipelines/       # Training & inference orchestration
│   │   ├── data/                # Seed scripts
│   │   └── core/                # Config, DB, security, logging
│   ├── alembic/                 # DB migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── modules/             # Feature modules (one per ERP domain)
│       ├── components/          # Shared UI components
│       ├── services/            # API client layer
│       └── store/               # Zustand global state
├── infrastructure/
│   ├── db/                      # init.sql
│   ├── scripts/                 # GCP provisioning
│   └── nginx/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── start.sh                     # One-command dev stack start
└── stop.sh
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/deepakkumarsray2026-dev/mini-erp.git
cd mini-erp
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env.dev
```

Edit `backend/.env.dev` and set a strong `SECRET_KEY`:

```env
APP_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql+asyncpg://erp_user:changeme@db:5432/mini_erp
DATABASE_URL_SYNC=postgresql://erp_user:changeme@db:5432/mini_erp
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
MODELS_DIR=/app/models_store
UPLOAD_DIR=/app/uploads
LOG_LEVEL=INFO
```

### 3. Start the stack

```bash
./start.sh
```

This builds all images, starts containers, waits for health checks, and runs migrations automatically.

Or manually:

```bash
docker compose -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.dev.yml exec -T -e PYTHONPATH=/app backend alembic upgrade head
```

### 4. Seed the database

```bash
docker compose -f docker-compose.dev.yml exec -T -e PYTHONPATH=/app backend python -m app.data.seed_all
```

### 5. Access the app

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

**Default credentials:**

| Username | Password | Role |
|---|---|---|
| `platform_admin` | `Admin@123!` | Platform Admin (full access) |
| `hr_admin` | `Admin@123!` | HR Admin |
| `finance_admin` | `Admin@123!` | Finance Admin |
| `workforce_user1` | `User@123!` | Workforce read/write |

---

## ERP Modules

### Phase 1 — Core ERP

| Module | Endpoints | Description |
|---|---|---|
| **Auth** | `/api/v1/auth/*` | JWT login, refresh, logout, RBAC |
| **Workforce** | `/api/v1/workforce/*` | Departments, jobs, employees, terminations |
| **Payroll** | `/api/v1/payroll/*` | Pay groups, periods, payroll runs, payslips |
| **Accounts Payable** | `/api/v1/ap/*` | Vendors, invoices, vouchers |
| **Expenses** | `/api/v1/expenses/*` | Categories, expense reports (submit/approve/reject) |
| **Procurement** | `/api/v1/procurement/*` | Requisitions, purchase orders, goods receipts |
| **General Ledger** | `/api/v1/gl/*` | Chart of accounts, journals, budgets, trial balance |
| **Admin** | `/api/v1/admin/*` | Role management, user stats |

### Phase 2 — Machine Learning

All ML endpoints are under `/api/v1/mlops/`.

#### Models

| Model | Algorithm | Task |
|---|---|---|
| **Attrition Predictor** | RandomForest + SMOTE | Binary: predict employee attrition risk |
| **Expense Violation Detector** | GradientBoosting / IsolationForest fallback | Binary: detect policy violations in expense lines |
| **Payroll Anomaly Detector** | RandomForest / IsolationForest fallback | Binary: flag anomalous payslips |
| **Invoice Classifier** | RandomForest + TF-IDF | Multi-class: categorise invoices into 10 spend categories |

#### Training a model

```bash
curl -X POST http://localhost:8000/api/v1/mlops/train/attrition_predictor \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"triggered_by": "manual"}'
```

Valid `model_type` values: `attrition_predictor`, `expense_violation`, `payroll_anomaly`, `invoice_classifier`

#### Batch Insights endpoints

```
GET /api/v1/mlops/insights/attrition-risk?limit=10
GET /api/v1/mlops/insights/expense-violations?limit=10
GET /api/v1/mlops/insights/payroll-anomalies?limit=10
GET /api/v1/mlops/insights/invoice-classifications?limit=10
```

These batch-score all entities and return the top N ranked by risk/confidence — used to power the AI dashboard.

#### MLOps registry endpoints

```
GET  /api/v1/mlops/models                          # List registered models
GET  /api/v1/mlops/models/{model_id}               # Model detail + metrics
GET  /api/v1/mlops/predictions                     # Prediction audit log
GET  /api/v1/mlops/jobs                            # Training job history
```

---

## Frontend Pages

| Route | Page |
|---|---|
| `/dashboard` | KPI dashboard |
| `/workforce/employees` | Employee list with attrition risk indicator |
| `/workforce/departments` | Department management |
| `/payroll/periods` | Pay period management |
| `/payroll/payslips` | Payslip browser |
| `/ap/vendors` | Vendor management |
| `/ap/invoices` | Invoice management |
| `/expenses/reports` | Expense report lifecycle |
| `/procurement/requisitions` | Purchase requisitions |
| `/procurement/orders` | Purchase orders |
| `/gl/accounts` | Chart of accounts |
| `/gl/journals` | Journal entries |
| `/gl/trial-balance` | Trial balance |
| `/admin/users` | User & role management |
| `/ai` | AI/MLOps dashboard (insights, model registry, prediction log) |

### AI Dashboard (`/ai`)

- **Insights tab** — Top 10 by attrition risk, expense violations, payroll anomalies, and invoice classifications. Rows exceeding 60% threshold highlighted in red. Each section has a "View All > 60%" modal.
- **Model Registry tab** — Trained model cards showing algorithm, version, training date, and evaluation metrics (accuracy, ROC-AUC, F1, CV-AUC).
- **Prediction Log tab** — Paginated audit trail of every inference call.

---

## Database Schema

PostgreSQL with 8 schemas:

| Schema | Tables |
|---|---|
| `auth` | users, roles, permissions, refresh_tokens |
| `hcm` | departments, job_families, jobs, employees |
| `payroll` | pay_groups, pay_periods, payroll_runs, payslips, payroll_components |
| `ap` | vendors, invoices, invoice_lines, vouchers |
| `expenses` | expense_categories, expense_reports, expense_lines |
| `procurement` | purchase_requisitions, purchase_orders, po_lines, goods_receipts |
| `gl` | accounts, fiscal_periods, journals, journal_lines, budgets |
| `mlops` | ml_models, ml_model_metrics, ml_prediction_logs, ml_training_jobs |

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production — merged from `develop` only |
| `develop` | Active development |
| `feature/*` | Feature branches, PR into `develop` |

---

## Useful Commands

```bash
# View logs
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend

# Stop everything
./stop.sh

# Run migrations
docker compose -f docker-compose.dev.yml exec -T -e PYTHONPATH=/app backend alembic upgrade head

# Open a DB shell
docker compose -f docker-compose.dev.yml exec db psql -U erp_user -d mini_erp

# Rebuild a single service
docker compose -f docker-compose.dev.yml up -d --build backend
```

---

## License

MIT
