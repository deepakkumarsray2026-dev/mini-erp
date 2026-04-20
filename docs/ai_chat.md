# Finance Chat — AI Chat Feature (Phase 3)

Natural-language querying of the Mini-ERP database using Text-to-SQL. Ask questions in plain English; the system translates them to SQL, executes against live data, and returns a formatted answer.

---

## Overview

Finance Chat uses a **tool-calling LLM loop**:

1. User sends a message.
2. The LLM receives the ERP database schema as context and a `run_sql` tool definition.
3. If the LLM needs data, it calls `run_sql` with a generated `SELECT` query.
4. The backend validates, wraps in a `LIMIT`, and executes against PostgreSQL.
5. Results are formatted as a markdown table and fed back to the LLM.
6. The LLM produces a natural-language answer — never raw JSON.
7. Both the user and assistant turns are persisted to `mlops.llm_chat_messages`.

---

## Architecture

```
Browser (ChatPage.tsx)
   │  POST /api/v1/llmops/chat/conversations/{id}/message
   ▼
llmops.py (FastAPI router)
   │  ai_service.send_message()
   ▼
chat_service.py
   ├── Load conversation history
   ├── _chat_anthropic()   or   _chat_openai_compatible()
   │       │
   │       ├── LLM call 1 — may return tool_use / tool_calls
   │       │       │
   │       │       └── _run_sql()          ← executes inside a SAVEPOINT
   │       │               │
   │       │               └── _format_sql_results()  ← markdown table
   │       │
   │       └── LLM call 2 — final natural-language answer
   │
   └── Return {content, sql_query, sql_results, latency_ms, tokens}
```

---

## LLM Provider Configuration

Set `LLM_PROVIDER` in `backend/.env.dev`:

| Provider | Value | Notes |
|---|---|---|
| Anthropic Claude | `anthropic` | Default. Requires `ANTHROPIC_API_KEY`. |
| Groq | `groq` | Free tier. Requires `GROQ_API_KEY`. Uses `GROQ_CHAT_MODEL`. |
| Ollama (local) | `ollama` | No API key. Requires `OLLAMA_BASE_URL`. |

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Or Groq:
# LLM_PROVIDER=groq
# GROQ_API_KEY=gsk_...
# GROQ_CHAT_MODEL=llama-3.3-70b-versatile

# Or Ollama:
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://host.docker.internal:11434
# OLLAMA_CHAT_MODEL=llama3.1
```

---

## API Reference

All endpoints require authentication (`Authorization: Bearer <token>`) and the `AI` module permission.

### Conversations

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/llmops/chat/conversations` | Create a new conversation |
| `GET` | `/api/v1/llmops/chat/conversations` | List all active conversations (50 most recent) |
| `GET` | `/api/v1/llmops/chat/conversations/{id}` | Get conversation with full message history |
| `DELETE` | `/api/v1/llmops/chat/conversations/{id}` | Archive a conversation |
| `POST` | `/api/v1/llmops/chat/conversations/{id}/message` | Send a message and receive LLM reply |

### Send message request/response

```json
// POST /api/v1/llmops/chat/conversations/{id}/message
// Request
{ "content": "What is the total AP outstanding balance?" }

// Response
{
  "message": {
    "id": "...",
    "role": "assistant",
    "content": "The total AP outstanding balance is $4,250,000.00 across 312 open invoices.",
    "sql_query": "SELECT SUM(total_amount) ...",
    "sql_results": { "columns": [...], "rows": [...], "row_count": 1 },
    "input_tokens": 1240,
    "output_tokens": 48,
    "latency_ms": 1832,
    "created_at": "2026-04-20T19:34:52Z"
  },
  "sql_query": "SELECT SUM(total_amount) ...",
  "sql_results": { ... },
  "latency_ms": 1832
}
```

---

## Database Schema Context

The LLM is provided with the full ERP schema and the following invoice status definitions, which are critical for AP queries:

```
ap.invoices.status values:
  DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, MATCHED, POSTED, PAID, CANCELLED

Business rules:
  "outstanding" = status NOT IN ('PAID', 'REJECTED', 'CANCELLED')
  "unpaid/open" = status IN ('SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'MATCHED', 'POSTED')
```

---

## SQL Safety

All queries are validated before execution:

- **Forbidden keywords** — `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `COPY`, `EXECUTE`
- **Must contain** `SELECT`
- **Row limit** — every query is wrapped: `SELECT * FROM (<user_query>) _q LIMIT <MAX_SQL_ROWS>`
- **Savepoint isolation** — each SQL execution runs inside a PostgreSQL `SAVEPOINT`. A failed query rolls back the savepoint only; the outer session transaction remains valid, preventing `InFailedSQLTransactionError` on subsequent operations.

---

## Frontend — ChatPage

Route: `/chat`

**Behaviour:**
- Opening the page shows a welcome screen with 6 example prompts.
- The input is **always enabled** — typing and pressing Enter auto-creates a new conversation if none is active.
- Clicking an example prompt creates a new conversation and sends the prompt immediately.
- Each assistant message optionally shows a collapsible **SQL Query** panel with the generated SQL and a results table (up to 20 rows previewed).
- Conversations are listed in the left sidebar, ordered by most-recent message. Titles are auto-generated from the first user message.

**Key files:**
```
frontend/src/modules/chat/pages/ChatPage.tsx
frontend/src/services/llm.service.ts
```

---

## Known Limitations

- Read-only access only — no write operations via chat.
- Conversation history sent to the LLM is capped at `CHAT_HISTORY_LIMIT` messages (default 20) to control token usage.
- Very complex multi-join queries may occasionally produce incorrect SQL — the system returns the LLM's error explanation rather than crashing.
- Groq/Ollama models using Llama may emit tool calls as inline text (`<function(run_sql ...)></function>`) rather than structured `tool_calls`. The backend detects and handles this format automatically.

---

## Example Queries

| Question | What it does |
|---|---|
| What is the total AP outstanding balance? | `SUM(total_amount)` on open invoices |
| Show department-wise AP outstanding balance | Joins `ap.invoices` → `hcm.departments` via GL |
| Which employees have the highest attrition risk? | Queries `hcm.employees.attrition_risk_score` |
| Top 5 vendors by invoice amount this year | Groups by vendor, filters by invoice date |
| List all invoices flagged as duplicates | Filters `ap.invoices.is_duplicate = true` |
| Which expense reports are pending approval? | Filters `expenses.expense_reports.status` |
| Budget vs actual spend by department | Queries `gl.budgets` joined to `hcm.departments` |
