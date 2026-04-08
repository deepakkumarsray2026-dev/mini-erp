"""
seed_ml_patterns.py
Injects realistic ML-labelled training patterns into existing ERP data.
Run AFTER the main seed scripts so employees / payslips / expenses / invoices exist.
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import text
from app.core.database import SyncSessionLocal
from loguru import logger


# ── helpers ───────────────────────────────────────────────────────────────────

def _rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ── 1. Attrition labels on employees ─────────────────────────────────────────

def seed_attrition_labels(session) -> None:
    """
    Mark ~20 % of employees as terminated (high-risk profile) and
    set attrition_risk_score for the rest so the model has a target.
    """
    rows = session.execute(
        text("SELECT id, satisfaction_score, performance_rating, overtime_monthly_avg, "
             "       base_salary, employment_type, hire_date "
             "FROM hcm.employees")
    ).fetchall()

    if not rows:
        logger.warning("No employees found – skipping attrition labels")
        return

    for row in rows:
        emp_id, sat, perf, ot, salary, etype, hire = row

        # derive a synthetic risk score (0-1)
        risk = 0.0
        if sat is not None:
            risk += (1.0 - float(sat)) * 0.35
        if perf is not None:
            risk += (1.0 - float(perf) / 5.0) * 0.25
        if ot is not None:
            risk += min(float(ot) / 40.0, 1.0) * 0.20
        if etype in ("contract", "intern"):
            risk += 0.15
        risk += random.uniform(-0.05, 0.05)
        risk = max(0.0, min(1.0, risk))

        # label ~20 % as churned (terminated)
        terminated = risk > 0.65 and random.random() < 0.55
        term_date  = _rand_date(date(2023, 1, 1), date(2024, 12, 31)) if terminated else None
        status     = "terminated" if terminated else "active"

        session.execute(
            text("""UPDATE hcm.employees
                    SET attrition_risk_score = :risk,
                        employment_status    = :status,
                        termination_date     = :tdate
                    WHERE id = :eid"""),
            {"risk": round(risk, 4), "status": status, "tdate": term_date, "eid": emp_id},
        )

    logger.info(f"Attrition labels set on {len(rows)} employees")


# ── 2. Expense violation flags ────────────────────────────────────────────────

VIOLATION_TYPES = ["over_limit", "missing_receipt", "weekend_spend",
                   "unapproved_category", "duplicate_merchant"]

def seed_expense_violations(session) -> None:
    lines = session.execute(
        text("""SELECT el.id, el.amount, el.expense_date, ec.daily_limit, el.receipt_path
                FROM expenses.expense_lines el
                JOIN expenses.expense_categories ec ON ec.id = el.category_id""")
    ).fetchall()

    if not lines:
        logger.warning("No expense lines found – skipping violation seeding")
        return

    flagged = 0
    for line_id, amount, exp_date, limit, receipt in lines:
        vtype = None
        if limit and float(amount) > float(limit) * 1.2:
            vtype = "over_limit"
        elif receipt is None and random.random() < 0.15:
            vtype = "missing_receipt"
        elif exp_date and exp_date.weekday() >= 5 and random.random() < 0.25:
            vtype = "weekend_spend"
        elif random.random() < 0.05:
            vtype = random.choice(VIOLATION_TYPES)

        if vtype:
            session.execute(
                text("UPDATE expenses.expense_lines SET is_violation=true, violation_type=:vt WHERE id=:id"),
                {"vt": vtype, "id": line_id},
            )
            flagged += 1

    # roll up to parent report
    session.execute(text("""
        UPDATE expenses.expense_reports er
        SET is_flagged      = true,
            violation_score = sub.score
        FROM (
            SELECT report_id,
                   LEAST(1.0, COUNT(*) * 0.25) AS score
            FROM expenses.expense_lines
            WHERE is_violation = true
            GROUP BY report_id
        ) sub
        WHERE er.id = sub.report_id
    """))

    logger.info(f"Flagged {flagged} expense lines as violations")


# ── 3. Payroll anomaly flags ──────────────────────────────────────────────────

def seed_payroll_anomalies(session) -> None:
    slips = session.execute(
        text("""SELECT ps.id, ps.gross_pay, ps.net_pay, ps.income_tax,
                       ps.employee_ni, ps.employee_pension,
                       e.base_salary
                FROM payroll.payslips ps
                JOIN hcm.employees e ON e.id = ps.employee_id""")
    ).fetchall()

    if not slips:
        logger.warning("No payslips found – skipping anomaly seeding")
        return

    anomalies = 0
    for slip_id, gross, net, tax, ni, pension, salary in slips:
        reason = None
        gross_f  = float(gross)
        salary_f = float(salary)
        monthly  = salary_f / 12

        # gross > 1.5× monthly (overtime spike or error)
        if gross_f > monthly * 1.5:
            reason = "gross_exceeds_1.5x_monthly"
        # negative net pay
        elif float(net) < 0:
            reason = "negative_net_pay"
        # tax > 60 % of gross
        elif float(tax) / max(gross_f, 1) > 0.60:
            reason = "excessive_tax_rate"
        # random 3 % noise
        elif random.random() < 0.03:
            reason = "statistical_outlier"

        if reason:
            session.execute(
                text("UPDATE payroll.payslips SET is_anomalous=true, anomaly_reason=:r WHERE id=:id"),
                {"r": reason, "id": slip_id},
            )
            anomalies += 1

    logger.info(f"Flagged {anomalies} payslips as anomalous")


# ── 4. Invoice category labels ────────────────────────────────────────────────

INVOICE_CATEGORIES = [
    "utilities", "software_saas", "office_supplies", "professional_services",
    "travel", "marketing", "hardware", "maintenance", "consulting", "insurance",
]

def seed_invoice_categories(session) -> None:
    invoices = session.execute(
        text("SELECT id, description, total_amount FROM ap.invoices WHERE category IS NULL")
    ).fetchall()

    if not invoices:
        logger.info("Invoices already have categories or none found")
        return

    for inv_id, desc, amount in invoices:
        desc_lower = (desc or "").lower()
        if any(k in desc_lower for k in ["electric", "gas", "water", "utility"]):
            cat = "utilities"
        elif any(k in desc_lower for k in ["software", "saas", "licence", "license", "subscription"]):
            cat = "software_saas"
        elif any(k in desc_lower for k in ["consult", "advisory", "professional"]):
            cat = "professional_services"
        elif any(k in desc_lower for k in ["travel", "hotel", "flight", "transport"]):
            cat = "travel"
        elif any(k in desc_lower for k in ["market", "advert", "campaign"]):
            cat = "marketing"
        elif any(k in desc_lower for k in ["hardware", "equipment", "laptop", "server"]):
            cat = "hardware"
        elif any(k in desc_lower for k in ["office", "stationery", "supplies"]):
            cat = "office_supplies"
        else:
            cat = random.choice(INVOICE_CATEGORIES)

        session.execute(
            text("UPDATE ap.invoices SET category=:cat WHERE id=:id"),
            {"cat": cat, "id": inv_id},
        )

    logger.info(f"Categories assigned to {len(invoices)} invoices")


# ── entry point ───────────────────────────────────────────────────────────────

def run_all() -> None:
    with SyncSessionLocal() as session:
        logger.info("Seeding ML training patterns …")
        seed_attrition_labels(session)
        seed_expense_violations(session)
        seed_payroll_anomalies(session)
        seed_invoice_categories(session)
        session.commit()
        logger.info("ML pattern seeding complete ✓")


if __name__ == "__main__":
    run_all()
