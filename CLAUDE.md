# Mini-ERP Platform — Claude Code Context

## Project Overview
A full-stack ERP platform built as a portfolio project demonstrating progression from
basic CRUD through ML, RAG/LLM, Deep Learning, and Agentic AI.

**Stack:** FastAPI · PostgreSQL · Redis · Celery · React (TypeScript) · Docker · GCP

---

## Roadmap & Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| Week 0 | Setup & Infrastructure (GCP, GitHub, CI/CD, DB schema) | ✅ Done |
| Phase 1 | MVP mini-ERP CRUD (Workforce, Payroll, AP, Expenses, Procurement, GL) | ✅ Built — needs VM deploy |
| Phase 2 | Machine Learning (Attrition, Expense Violations, Payroll Anomaly, Invoice Classifier) | 🔄 Partial |
| Phase 3 | RAG + LLM (Duplicate Invoice, Finance Chat, OCR Pipeline) | 🔄 In Progress |
| Phase 4 | Deep Learning (LSTM Budget Forecaster, CNN Invoice Image Classifier) | ⏳ Pending |
| Phase 5 | AI Agents (Invoice Agent, Expense Audit Agent, Onboarding Agent) | ⏳ Pending |
| Phase 6 | Agentic Networks (Financial Close Network, Workforce Planning Network) | ⏳ Pending |
| Week 11 | Polish, Docs, Portfolio Deploy | ⏳ Pending |

---

## Repository Structure

```
mini-erp/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers (auth, workforce, payroll, ap, expenses, procurement, gl, admin)
│   │   ├── models/          # SQLAlchemy ORM models (per module + mlops)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic services
│   │   ├── ml/              # ML models, features, pipelines (Phase 2+)
│   │   ├── data/            # Seed scripts (seed_all.py runs all)
│   │   ├── core/            # config, database, security, permissions, logging
│   │   └── main.py          # FastAPI app + router registration
│   ├── alembic/             # DB migrations
│   ├── requirements.txt     # Python dependencies
│   └── .env.dev             # Dev environment variables (do not commit)
├── frontend/                # React + TypeScript + Tailwind (Vite)
├── infrastructure/
│   ├── db/                  # init.sql, init_addons.sql
│   ├── scripts/             # GCP provisioning scripts
│   └── nginx/               # Nginx configs
├── docker-compose.dev.yml   # Dev stack (backend, frontend, db, redis, celery)
├── docker-compose.prod.yml  # Production stack
└── CLAUDE.md                # This file
```

---

## Branch Strategy
- `main` — production only, never commit directly
- `develop` — all active development goes here
- `feature/*` — feature branches, PR into develop

**Always work on `develop` branch.**

---

## Database

**Schemas (PostgreSQL):**
- `auth` — users, roles, permissions, refresh tokens
- `hcm` — departments, job families, jobs, employees
- `payroll` — pay groups, periods, runs, payslips, components
- `ap` — vendors, invoices, invoice lines, vouchers
- `expenses` — categories, expense reports, expense lines
- `procurement` — purchase requisitions, purchase orders, PO lines, goods receipts
- `gl` — chart of accounts, fiscal periods, journals, journal lines, budgets
- `mlops` — ml_models, ml_model_metrics, ml_prediction_logs, ml_training_jobs

**Connection (dev):**
```
postgresql://erp_user:changeme@localhost:5432/mini_erp
```
Inside Docker: host is `db` not `localhost`.

---

## Running the App

### Start everything
```bash
docker compose -f docker-compose.dev.yml up -d --build
```

### Run migrations
```bash
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

### Seed the database
```bash
docker compose -f docker-compose.dev.yml exec backend python -m app.data.seed_all
```

### Check API health
```bash
curl http://localhost:8000/api/v1/health
```

### View API docs
```
http://<VM-IP>:8000/docs
```

### View logs
```bash
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f db
```

---

## API Structure

All endpoints are under `/api/v1/`:

| Prefix | Module | Key endpoints |
|--------|--------|---------------|
| `/auth` | Authentication | login, refresh, logout, me, users |
| `/workforce` | HCM | departments, job-families, jobs, employees, terminate |
| `/payroll` | Payroll | pay-groups, pay-periods, runs, payslips, components |
| `/ap` | Accounts Payable | vendors, invoices, vouchers |
| `/expenses` | Expenses | categories, reports (submit/approve/reject) |
| `/procurement` | Procurement | requisitions, orders, receipts |
| `/gl` | General Ledger | accounts, fiscal-periods, journals, budgets, trial-balance |
| `/admin` | Admin | roles, assign/revoke, stats |

---

## Environment Variables (.env.dev)

```env
APP_ENV=development
SECRET_KEY=<generate a strong key>
DATABASE_URL=postgresql+asyncpg://erp_user:changeme@db:5432/mini_erp
DATABASE_URL_SYNC=postgresql://erp_user:changeme@db:5432/mini_erp
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
MODELS_DIR=/app/models_store
UPLOAD_DIR=/app/uploads
LOG_LEVEL=INFO
```

---

## Key Rules & Conventions

### Code Style
- Python: follow existing patterns, async/await throughout, loguru for logging
- Always use `await db.flush()` not `await db.commit()` inside services (commit happens in `get_db`)
- Pydantic schemas: separate Create / Update / Response classes per resource
- All UUIDs stored as strings (UUID(as_uuid=False))

### GCP Free Tier — CRITICAL
- **Never** create new VM instances
- **Never** upgrade machine type
- **Never** create new Cloud SQL instances
- **Never** enable paid APIs
- Keep all data local on the VM where possible
- Avoid excessive egress (external data transfers)

### Git
- All work on `develop` branch
- Commit messages: `feat(module): description` / `fix(module): description`
- Never push to `main` directly

### ML Models (Phase 2+)
- Models saved to `MODELS_DIR=/app/models_store` as `.joblib` files
- Registered in `mlops.ml_models` DB table
- Always log predictions to `mlops.ml_prediction_logs`
- Use `SyncSessionLocal` (not async) for training pipelines

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `psql: no socket` | Postgres is in Docker — use `docker compose exec db psql ...` |
| `alembic can't find models` | Check `alembic/env.py` imports all model modules |
| `422 Unprocessable Entity` | Check Pydantic schema — missing required field |
| `403 Forbidden` | User doesn't have the required permission in RBAC |
| `relation does not exist` | Run `alembic upgrade head` first |
| ML model not found | Run training endpoint first: `POST /api/v1/mlops/train/{model_type}` |

---

## Contacts & Links
- GitHub: https://github.com/deepakkumarsray2026-dev/mini-erp
- VM IP: 34.13.57.203
- API Docs: http://34.13.57.203:8000/docs
