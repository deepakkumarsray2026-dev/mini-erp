"""
Finance Chat service — Text-to-SQL with provider-agnostic LLM support.

Supported providers (set LLM_PROVIDER in .env.dev):
  - "ollama"    — local Ollama (no API key, default)
  - "anthropic" — Anthropic Claude API
  - "groq"      — Groq API (free tier, OpenAI-compatible)

Flow:
  1. Load conversation history
  2. Send to LLM with a run_sql tool
  3. If LLM calls run_sql: validate → execute → feed results back
  4. LLM generates final natural-language response
  5. Persist both turns
"""
import json
import re
import time

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.llmops import LLMChatMessage

# ---------------------------------------------------------------------------
# ERP schema context
# ---------------------------------------------------------------------------

_SCHEMA_CONTEXT = """
You are a Finance Chat assistant for the Mini-ERP platform.
You have read-only access to a PostgreSQL database via the run_sql tool.
Use it to answer the user's question accurately and concisely.
Always use schema-qualified table names (e.g. hcm.employees).

DATABASE SCHEMA:

Schema: hcm
  employees(id, employee_id, first_name, last_name, email, hire_date, termination_date,
            employment_status, employment_type, department_id, job_id, manager_id,
            base_salary, currency, satisfaction_score, performance_rating,
            attrition_risk_score, is_active)
  departments(id, code, name, parent_id, manager_id, cost_center, is_active)
  jobs(id, code, title, grade_min, grade_max, salary_min, salary_max)

Schema: payroll
  payslips(id, payroll_run_id, employee_id, gross_pay, net_pay, income_tax,
           employee_ni, pension, is_anomalous, anomaly_reason)
  payroll_runs(id, pay_period_id, status, total_gross, total_net, run_at, anomaly_flags)
  pay_periods(id, fiscal_year, period_number, start_date, end_date, pay_date, status)

Schema: ap
  vendors(id, vendor_id, name, status, payment_terms_days, risk_score, is_active)
  invoices(id, invoice_number, vendor_id, po_id, invoice_date, due_date, currency,
           subtotal, tax_amount, total_amount, status, description, category,
           is_duplicate, ocr_extracted)
    -- status values: 'DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED',
    --                'MATCHED', 'POSTED', 'PAID', 'CANCELLED'
    -- "outstanding" invoices = status NOT IN ('PAID','REJECTED','CANCELLED')
    -- "unpaid/open" invoices = status IN ('SUBMITTED','UNDER_REVIEW','APPROVED','MATCHED','POSTED')
  invoice_lines(id, invoice_id, description, quantity, unit_price, amount, tax_rate, gl_account_code)

Schema: expenses
  expense_reports(id, report_number, employee_id, title, total_amount, currency,
                  status, violation_score, is_flagged)
  expense_lines(id, report_id, category_id, expense_date, merchant, description,
                amount, is_violation, violation_type)
  expense_categories(id, code, name, daily_limit, requires_receipt)

Schema: procurement
  purchase_orders(id, po_number, vendor_id, issued_date, total_amount, currency, status)
  purchase_requisitions(id, pr_number, requested_by, department_id, total_amount, status)

Schema: gl
  chart_of_accounts(id, account_code, account_name, account_type, is_active)
  journals(id, journal_number, fiscal_period_id, journal_date, description,
           total_debit, total_credit, status)
  journal_lines(id, journal_id, account_code, description, debit, credit, department_id)
  budgets(id, fiscal_year, period_number, account_code, department_id,
          budgeted_amount, actual_amount, forecasted_amount, variance)
  fiscal_periods(id, fiscal_year, period_number, start_date, end_date, status)

RULES:
- Only generate SELECT queries. Never INSERT, UPDATE, DELETE, DROP, or CREATE.
- Always qualify table names with schema (e.g. hcm.employees, ap.invoices).
- Limit results: add LIMIT 100 unless user asks for more.
- Format amounts with currency when presenting to the user.
- If the question can't be answered from the DB, say so clearly.
- NEVER output raw JSON or data structures in your final answer. Always present
  results as natural language, formatted numbers, or a markdown table.
"""

# ---------------------------------------------------------------------------
# SQL results formatter
# ---------------------------------------------------------------------------

def _format_sql_results(results: dict) -> str:
    """Convert SQL result dict to a markdown table for LLM consumption."""
    if results.get("error"):
        return f"Error: {results['error']}"
    columns: list[str] = results.get("columns", [])
    rows: list[dict] = results.get("rows", [])
    row_count: int = results.get("row_count", 0)
    if not columns or not rows:
        return "Query returned no rows."
    header = "| " + " | ".join(columns) + " |"
    sep    = "| " + " | ".join("---" for _ in columns) + " |"
    body   = "\n".join(
        "| " + " | ".join(str(row.get(c, "")) for c in columns) + " |"
        for row in rows
    )
    suffix = f"\n\n({row_count} rows)" if row_count > len(rows) else ""
    return f"{header}\n{sep}\n{body}{suffix}"


# ---------------------------------------------------------------------------
# Inline tool-call parser
# Some Groq/Ollama models emit tool calls as text rather than structured
# tool_calls, e.g.: <function(run_sql {"query": "...", ...})</function>
# ---------------------------------------------------------------------------

def _extract_inline_tool_call(content: str) -> dict | None:
    """Return parsed JSON args if the content is an embedded function call, else None."""
    m = re.search(r'<function\(\s*run_sql\s+(.*?)\s*</function>', content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip().rstrip(')'))
        except (json.JSONDecodeError, ValueError):
            pass
    return None


# ---------------------------------------------------------------------------
# SQL safety guard
# ---------------------------------------------------------------------------

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|COPY|EXECUTE)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> None:
    if _FORBIDDEN.search(sql):
        raise ValueError("Query contains forbidden SQL statements.")
    if not re.search(r"\bSELECT\b", sql, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")


# ---------------------------------------------------------------------------
# SQL execution
# ---------------------------------------------------------------------------

async def _run_sql(query: str, db: AsyncSession) -> dict:
    _validate_sql(query)
    safe = query.rstrip().rstrip(";")
    wrapped = f"SELECT * FROM ({safe}) _q LIMIT {settings.MAX_SQL_ROWS}"
    # Use a savepoint so that a bad SQL query doesn't abort the outer transaction.
    # Without this, a failed query leaves the DB session in an aborted state,
    # preventing the subsequent conversation-timestamp flush from succeeding.
    async with db.begin_nested():
        result = await db.execute(text(wrapped))
        rows = result.fetchall()
        columns = list(result.keys())
    data = [dict(zip(columns, row)) for row in rows]
    for row in data:
        for k, v in row.items():
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat()
            elif v is not None and not isinstance(v, (str, int, float, bool, dict, list)):
                row[k] = str(v)
    return {"columns": columns, "rows": data, "row_count": len(data)}


# ---------------------------------------------------------------------------
# Provider: Anthropic
# ---------------------------------------------------------------------------

async def _chat_anthropic(messages: list[dict], db: AsyncSession) -> dict:
    import anthropic

    _TOOL = {
        "name": "run_sql",
        "description": "Execute a read-only SELECT query against the ERP database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PostgreSQL SELECT query."},
                "explanation": {"type": "string", "description": "What this query retrieves."},
            },
            "required": ["query", "explanation"],
        },
    }

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    sql_query = sql_results = None
    total_in = total_out = 0

    resp = await client.messages.create(
        model=settings.CHAT_MODEL,
        max_tokens=2048,
        system=_SCHEMA_CONTEXT,
        tools=[_TOOL],
        messages=messages,
    )
    total_in  += resp.usage.input_tokens
    total_out += resp.usage.output_tokens

    if resp.stop_reason == "tool_use":
        tool_block = next(b for b in resp.content if b.type == "tool_use")
        sql_query = tool_block.input.get("query", "")
        try:
            sql_results = await _run_sql(sql_query, db)
            tool_content = json.dumps(sql_results)
        except Exception as exc:
            tool_content = json.dumps({"error": str(exc)})

        resp2 = await client.messages.create(
            model=settings.CHAT_MODEL,
            max_tokens=2048,
            system=_SCHEMA_CONTEXT,
            tools=[_TOOL],
            messages=messages + [
                {"role": "assistant", "content": resp.content},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": tool_block.id, "content": tool_content}
                ]},
            ],
        )
        total_in  += resp2.usage.input_tokens
        total_out += resp2.usage.output_tokens
        final_text = next((b.text for b in resp2.content if hasattr(b, "text")), "")
    else:
        final_text = next((b.text for b in resp.content if hasattr(b, "text")), "")

    return {"content": final_text, "sql_query": sql_query, "sql_results": sql_results,
            "input_tokens": total_in, "output_tokens": total_out}


# ---------------------------------------------------------------------------
# Provider: OpenAI-compatible (Ollama or Groq)
# ---------------------------------------------------------------------------

async def _chat_openai_compatible(messages: list[dict], db: AsyncSession) -> dict:
    from openai import AsyncOpenAI

    provider = settings.LLM_PROVIDER
    if provider == "ollama":
        client = AsyncOpenAI(base_url=f"{settings.OLLAMA_BASE_URL}/v1", api_key="ollama")
        model  = settings.OLLAMA_CHAT_MODEL
    else:  # groq
        client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=settings.GROQ_API_KEY)
        model  = settings.GROQ_CHAT_MODEL

    _TOOL = {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Execute a read-only SELECT query against the ERP database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "PostgreSQL SELECT query."},
                    "explanation": {"type": "string", "description": "What this query retrieves."},
                },
                "required": ["query", "explanation"],
            },
        },
    }

    # Prepend system message (OpenAI format)
    oai_messages = [{"role": "system", "content": _SCHEMA_CONTEXT}] + messages

    sql_query = sql_results = None
    total_in = total_out = 0

    resp = await client.chat.completions.create(
        model=model,
        max_tokens=2048,
        tools=[_TOOL],
        tool_choice="auto",
        messages=oai_messages,
    )
    total_in  += resp.usage.prompt_tokens if resp.usage else 0
    total_out += resp.usage.completion_tokens if resp.usage else 0

    msg = resp.choices[0].message

    if msg.tool_calls:
        tool_call = msg.tool_calls[0]
        sql_query = json.loads(tool_call.function.arguments).get("query", "")
        try:
            sql_results = await _run_sql(sql_query, db)
            tool_content = _format_sql_results(sql_results)
        except Exception as exc:
            sql_results = None
            tool_content = f"Error: {exc}"

        resp2 = await client.chat.completions.create(
            model=model,
            max_tokens=2048,
            messages=oai_messages + [
                msg,
                {"role": "tool", "tool_call_id": tool_call.id,
                 "content": f"{tool_content}\n\nPresent this as a clear, formatted answer. Do not output raw JSON."},
            ],
        )
        total_in  += resp2.usage.prompt_tokens if resp2.usage else 0
        total_out += resp2.usage.completion_tokens if resp2.usage else 0
        final_text = resp2.choices[0].message.content or ""
    else:
        # Some Groq/Ollama models embed the tool call as plain text instead of
        # using the structured tool_calls field.  Detect and handle that here.
        inline = _extract_inline_tool_call(msg.content or "")
        if inline:
            sql_query = inline.get("query", "")
            try:
                sql_results = await _run_sql(sql_query, db)
                tool_content = _format_sql_results(sql_results)
            except Exception as exc:
                sql_results = None
                tool_content = f"Error: {exc}"

            resp2 = await client.chat.completions.create(
                model=model,
                max_tokens=2048,
                messages=oai_messages + [
                    {"role": "assistant", "content": msg.content},
                    {"role": "user", "content": (
                        f"Here are the SQL query results:\n\n{tool_content}\n\n"
                        "Please present this as a clear, formatted answer in plain English. "
                        "Do not output raw JSON or data structures."
                    )},
                ],
            )
            total_in  += resp2.usage.prompt_tokens if resp2.usage else 0
            total_out += resp2.usage.completion_tokens if resp2.usage else 0
            final_text = resp2.choices[0].message.content or ""
        else:
            final_text = msg.content or ""

    return {"content": final_text, "sql_query": sql_query, "sql_results": sql_results,
            "input_tokens": total_in, "output_tokens": total_out}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def chat(conversation_id: str, user_message: str, db: AsyncSession) -> dict:
    start = time.time()

    # Load history
    hist_result = await db.execute(
        select(LLMChatMessage)
        .where(LLMChatMessage.conversation_id == conversation_id)
        .order_by(LLMChatMessage.created_at.desc())
        .limit(settings.CHAT_HISTORY_LIMIT)
    )
    history = list(reversed(hist_result.scalars().all()))
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": user_message})

    provider = settings.LLM_PROVIDER
    logger.info(f"Chat via provider={provider}")

    if provider == "anthropic":
        result = await _chat_anthropic(messages, db)
    else:
        result = await _chat_openai_compatible(messages, db)

    result["latency_ms"] = int((time.time() - start) * 1000)
    return result


async def generate_title(first_message: str) -> str:
    """Generate a short title from the first user message."""
    try:
        provider = settings.LLM_PROVIDER
        prompt = "Generate a short (3-6 word) title for a finance chat based on this question. Reply with only the title."
        if provider == "anthropic":
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            resp = await client.messages.create(
                model=settings.CHAT_MODEL, max_tokens=30,
                system=prompt,
                messages=[{"role": "user", "content": first_message}],
            )
            return next((b.text.strip() for b in resp.content if hasattr(b, "text")), first_message[:50])
        else:
            from openai import AsyncOpenAI
            if provider == "ollama":
                client = AsyncOpenAI(base_url=f"{settings.OLLAMA_BASE_URL}/v1", api_key="ollama")
                model  = settings.OLLAMA_CHAT_MODEL
            else:
                client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=settings.GROQ_API_KEY)
                model  = settings.GROQ_CHAT_MODEL
            resp = await client.chat.completions.create(
                model=model, max_tokens=30,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": first_message},
                ],
            )
            return (resp.choices[0].message.content or first_message[:50]).strip()
    except Exception:
        return first_message[:50]
