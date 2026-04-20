# Changelog

All notable changes to the Mini-ERP platform are documented here, organised by phase and version.

---

## Phase 3 — RAG + LLM

### v3.2.0 — Finance Chat bug fixes & UX improvements (2026-04-20)

#### Fixed
- **`InFailedSQLTransactionError` on failed SQL queries** — SQL execution in `_run_sql()` is now wrapped in a PostgreSQL `SAVEPOINT` (`db.begin_nested()`). A bad query rolls back only the savepoint, leaving the session valid for the subsequent conversation-timestamp flush.
- **Inline tool-call format not handled** — Groq/Ollama models (Llama family) sometimes emit tool calls as `<function(run_sql {...})</function>` in the message content instead of the structured `tool_calls` field. Added `_extract_inline_tool_call()` to detect and execute these, then call the LLM a second time for a natural-language answer.
- **Raw JSON echoed in chat responses** — The follow-up LLM call now receives SQL results pre-formatted as a markdown table (via `_format_sql_results()`) rather than raw JSON. Added a "never output raw JSON" rule to the system prompt.
- **AP outstanding balance unresolvable** — Added all `InvoiceStatus` enum values (`DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `MATCHED`, `POSTED`, `PAID`, `CANCELLED`) and business-rule comments to `_SCHEMA_CONTEXT` so the LLM knows what "outstanding" means.
- **Input frozen on chat page load** — Removed `!activeConv` from the textarea's `disabled` condition. The input is now always enabled; sending a message auto-creates a conversation if none is active.

#### Changed
- `send()` in `ChatPage.tsx` auto-creates a conversation when the user sends the first message with no active conversation, mirroring the example-prompt behaviour.

---

### v3.1.0 — Finance Chat, Duplicate Invoice Detection, OCR Pipeline (2026-04-15)

#### Added

**Backend**
- `backend/app/api/v1/llmops.py` — new FastAPI router for all Phase 3 LLM/RAG endpoints (`/api/v1/llmops/*`).
- `backend/app/services/ai_service.py` — orchestration layer for conversation management, message routing, duplicate-invoice detection, and OCR job creation.
- `backend/app/ml/llm/chat_service.py` — Text-to-SQL engine with provider-agnostic LLM support (Anthropic / Groq / Ollama), SQL safety validation, and conversation history.
- `backend/app/ml/llm/embedding_service.py` — pgvector-based invoice embedding and cosine-similarity duplicate detection.
- `backend/app/ml/llm/ocr_service.py` — Invoice image OCR via Claude Vision API.
- `backend/app/tasks/ocr_tasks.py` — Celery task for async OCR processing.
- `backend/app/models/llmops.py` — SQLAlchemy models: `LLMConversation`, `LLMChatMessage`, `LLMDocumentJob`, `InvoiceEmbedding`.
- Alembic migrations: `a1b2c3d4e5f6_phase3_llm_tables.py`, `b2c3d4e5f6a1_phase3_embeddings_pgvector.py`.
- New config vars: `LLM_PROVIDER`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `GROQ_CHAT_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, `CHAT_MODEL`, `CHAT_HISTORY_LIMIT`, `MAX_SQL_ROWS`.

**Frontend**
- `frontend/src/modules/chat/pages/ChatPage.tsx` — Finance Chat UI with conversation sidebar, message bubbles, collapsible SQL query panel, and example prompts.
- `frontend/src/services/llm.service.ts` — API client for all LLM/chat endpoints.
- `/chat` route added to `router.tsx`.
- "AI Chat" entry added to `Sidebar.tsx`.

**Infrastructure**
- `pgvector` extension enabled in `infrastructure/db/init.sql`.
- `docker-compose.dev.yml` updated with `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `OLLAMA_BASE_URL` env vars.

#### LLM endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/llmops/chat/conversations` | Create conversation |
| `GET` | `/api/v1/llmops/chat/conversations` | List conversations |
| `GET` | `/api/v1/llmops/chat/conversations/{id}` | Get conversation + messages |
| `DELETE` | `/api/v1/llmops/chat/conversations/{id}` | Archive conversation |
| `POST` | `/api/v1/llmops/chat/conversations/{id}/message` | Send message / get LLM reply |
| `POST` | `/api/v1/llmops/invoices/{id}/duplicate-check` | Check single invoice for duplicates |
| `GET` | `/api/v1/llmops/invoices/duplicates` | List all flagged duplicate invoices |
| `POST` | `/api/v1/llmops/embeddings/reindex` | Reindex all invoice embeddings (admin) |
| `POST` | `/api/v1/llmops/ocr/upload` | Upload invoice image, returns job ID |
| `GET` | `/api/v1/llmops/ocr/jobs` | List OCR jobs |
| `GET` | `/api/v1/llmops/ocr/jobs/{id}` | Get OCR job status + extracted data |

---

## Phase 2 — Machine Learning

### v2.0.0 — ML Models & AI Dashboard (2026-03-XX)

#### Added
- **Attrition Predictor** — RandomForest + SMOTE. Predicts employee attrition risk from HR features.
- **Expense Violation Detector** — GradientBoosting / IsolationForest fallback. Flags policy-violating expense lines.
- **Payroll Anomaly Detector** — RandomForest / IsolationForest fallback. Identifies anomalous payslips.
- **Invoice Classifier** — RandomForest + TF-IDF. Categorises invoices into 10 spend categories.
- `mlops` schema: `ml_models`, `ml_model_metrics`, `ml_prediction_logs`, `ml_training_jobs`.
- Batch insights endpoints for all four models.
- AI Dashboard (`/ai`) with Insights, Model Registry, and Prediction Log tabs.
- Model versioning and evaluation metrics (accuracy, ROC-AUC, F1, CV-AUC) stored per training run.

---

## Phase 1 — Core ERP

### v1.0.0 — MVP ERP (2026-02-XX)

#### Added
- **Auth** — JWT authentication, refresh tokens, RBAC with roles and permissions.
- **Workforce (HCM)** — Departments, job families, jobs, employees, terminations.
- **Payroll** — Pay groups, pay periods, payroll runs, payslips, payroll components.
- **Accounts Payable** — Vendors, invoices (full status lifecycle), invoice lines, vouchers.
- **Expenses** — Categories, expense reports (submit → approve/reject), expense lines.
- **Procurement** — Purchase requisitions, purchase orders, PO lines, goods receipts.
- **General Ledger** — Chart of accounts, fiscal periods, journals, journal lines, budgets, trial balance.
- **Admin** — Role management, user stats.
- Full async FastAPI backend with SQLAlchemy 2.0, Alembic migrations, and Celery worker.
- React 18 + TypeScript frontend with TanStack Query, Zustand, and Tailwind CSS.
- Docker Compose dev stack (backend, frontend, PostgreSQL, Redis, Celery).
- GCP free-tier deployment with Nginx reverse proxy.

---

## Week 0 — Infrastructure

### v0.1.0 — Project scaffolding (2026-01-XX)

#### Added
- GCP VM provisioning (free tier `e2-micro`).
- GitHub repository, branch strategy (`main` / `develop` / `feature/*`).
- CI/CD pipeline skeleton.
- PostgreSQL 15 with 8 schema namespaces.
- Docker Compose stack with health checks.
- Base `CLAUDE.md` project context file.
