"""
Regenerate docs/mini_erp_user_guide.pdf
Includes all original sections + Phase 3 Finance Chat additions.
Run: python3 scripts/generate_user_guide.py
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import os

# ── Colour palette ──────────────────────────────────────────────────────────
NAVY      = HexColor("#0F2B5B")
BLUE      = HexColor("#0057AE")
LIGHT_BLUE= HexColor("#5BA4F5")
DARK_BG   = HexColor("#0F1826")
MID_GREY  = HexColor("#64748B")
LIGHT_GREY= HexColor("#F1F5F9")
WHITE     = colors.white
BLACK     = colors.black
GREEN     = HexColor("#16A34A")
AMBER     = HexColor("#D97706")
RED       = HexColor("#DC2626")
PURPLE    = HexColor("#7C3AED")
TEAL      = HexColor("#0891B2")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm

# ── Style helpers ───────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    def ps(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        "h1": ps("H1", fontSize=26, textColor=WHITE, fontName="Helvetica-Bold",
                 spaceAfter=4, leading=32),
        "h1_sub": ps("H1Sub", fontSize=11, textColor=LIGHT_BLUE, fontName="Helvetica",
                     spaceAfter=0),
        "h2": ps("H2", fontSize=16, textColor=NAVY, fontName="Helvetica-Bold",
                 spaceBefore=8, spaceAfter=4),
        "h3": ps("H3", fontSize=12, textColor=BLUE, fontName="Helvetica-Bold",
                 spaceBefore=6, spaceAfter=3),
        "body": ps("Body", fontSize=9, textColor=HexColor("#1E293B"),
                   leading=14, spaceAfter=4, alignment=TA_JUSTIFY),
        "bullet": ps("Bullet", fontSize=9, textColor=HexColor("#1E293B"),
                     leading=14, leftIndent=12, bulletIndent=0, spaceAfter=3),
        "note": ps("Note", fontSize=8, textColor=HexColor("#475569"),
                   leading=12, leftIndent=8, rightIndent=8,
                   borderPad=4, backColor=LIGHT_GREY,
                   borderWidth=0.5, borderColor=HexColor("#CBD5E1"),
                   borderRadius=3, spaceAfter=6),
        "tip": ps("Tip", fontSize=8, textColor=HexColor("#1E40AF"),
                  leading=12, leftIndent=8, rightIndent=8,
                  borderPad=4, backColor=HexColor("#EFF6FF"),
                  borderWidth=0.5, borderColor=BLUE,
                  borderRadius=3, spaceAfter=6),
        "warning": ps("Warning", fontSize=8, textColor=HexColor("#7F1D1D"),
                      leading=12, leftIndent=8, rightIndent=8,
                      borderPad=4, backColor=HexColor("#FEF2F2"),
                      borderWidth=0.5, borderColor=RED,
                      borderRadius=3, spaceAfter=6),
        "toc_title": ps("TocTitle", fontSize=13, textColor=NAVY, fontName="Helvetica-Bold",
                        spaceBefore=12, spaceAfter=6),
        "toc_section": ps("TocSection", fontSize=9, textColor=MID_GREY,
                          fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2),
        "toc_item": ps("TocItem", fontSize=9, textColor=HexColor("#1E293B"),
                       leading=14, leftIndent=12, spaceAfter=2),
        "section_label": ps("SectionLabel", fontSize=7, textColor=BLUE,
                            fontName="Helvetica-Bold", spaceBefore=0, spaceAfter=2,
                            tracking=2),
        "section_sub": ps("SectionSub", fontSize=10, textColor=MID_GREY,
                          fontName="Helvetica", spaceAfter=8),
        "caption": ps("Caption", fontSize=8, textColor=MID_GREY,
                      alignment=TA_CENTER, spaceAfter=4),
        "small": ps("Small", fontSize=8, textColor=MID_GREY, leading=12),
        "route": ps("Route", fontSize=9, textColor=BLUE, fontName="Helvetica-Oblique",
                    spaceAfter=6),
        "version": ps("Version", fontSize=9, textColor=LIGHT_BLUE,
                      alignment=TA_CENTER),
        "confidential": ps("Confidential", fontSize=7, textColor=MID_GREY,
                           alignment=TA_CENTER),
        "toc_new": ps("TocNew", fontSize=9, textColor=GREEN,
                      leading=14, leftIndent=12, spaceAfter=2, fontName="Helvetica-Bold"),
    }


S = make_styles()

# ── Canvas callbacks ─────────────────────────────────────────────────────────
def _header_footer(canv: canvas.Canvas, doc):
    canv.saveState()
    # Header bar
    canv.setFillColor(NAVY)
    canv.rect(0, PAGE_H - 14 * mm, PAGE_W, 14 * mm, fill=1, stroke=0)
    canv.setFont("Helvetica-Bold", 9)
    canv.setFillColor(WHITE)
    canv.drawString(MARGIN, PAGE_H - 9 * mm, "Mini ERP · End-User Guide")
    canv.setFont("Helvetica", 8)
    canv.setFillColor(LIGHT_BLUE)
    canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 9 * mm, "Version 2.0  ·  April 2026")
    # Footer
    canv.setFillColor(LIGHT_GREY)
    canv.rect(0, 0, PAGE_W, 10 * mm, fill=1, stroke=0)
    canv.setFont("Helvetica", 7)
    canv.setFillColor(MID_GREY)
    canv.drawString(MARGIN, 3.5 * mm, "Mini ERP · Portfolio Project  |  Confidential")
    canv.drawRightString(PAGE_W - MARGIN, 3.5 * mm, f"Page {doc.page}")
    canv.restoreState()


def _cover_page(canv: canvas.Canvas, doc):
    """Render the cover page without header/footer chrome."""
    canv.saveState()
    # Full-bleed background
    canv.setFillColor(DARK_BG)
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Top accent stripe
    canv.setFillColor(BLUE)
    canv.rect(0, PAGE_H - 6 * mm, PAGE_W, 6 * mm, fill=1, stroke=0)
    # Left accent stripe
    canv.setFillColor(BLUE)
    canv.rect(0, 0, 4 * mm, PAGE_H, fill=1, stroke=0)

    # Title
    canv.setFont("Helvetica-Bold", 36)
    canv.setFillColor(WHITE)
    canv.drawString(MARGIN + 8 * mm, PAGE_H * 0.62, "Mini ERP")

    # Version / date
    canv.setFont("Helvetica", 11)
    canv.setFillColor(LIGHT_BLUE)
    canv.drawString(MARGIN + 8 * mm, PAGE_H * 0.56, "Version 2.0  ·  April 2026")

    # Module chips
    modules = [
        "Workforce & HR", "Payroll", "Accounts Payable",
        "Expenses", "Procurement", "General Ledger",
        "AI / MLOps", "Finance Chat  ★ New", "Administration",
    ]
    y = PAGE_H * 0.49
    x = MARGIN + 8 * mm
    chip_h = 7 * mm
    chip_gap = 2 * mm
    canv.setFont("Helvetica", 8.5)
    for mod in modules:
        w = canv.stringWidth(mod, "Helvetica", 8.5) + 10 * mm
        is_new = "★ New" in mod
        canv.setFillColor(BLUE if not is_new else GREEN)
        canv.roundRect(x, y, w, chip_h, 3, fill=1, stroke=0)
        canv.setFillColor(WHITE)
        canv.drawString(x + 5 * mm, y + 2 * mm, mod)
        x += w + chip_gap
        if x > PAGE_W - MARGIN - 40 * mm:
            x = MARGIN + 8 * mm
            y -= chip_h + chip_gap

    # Sub-title
    canv.setFont("Helvetica-Bold", 14)
    canv.setFillColor(WHITE)
    canv.drawString(MARGIN + 8 * mm, PAGE_H * 0.25, "End-User Guide")

    # Footer
    canv.setFont("Helvetica", 7)
    canv.setFillColor(MID_GREY)
    canv.drawString(MARGIN + 8 * mm, 8 * mm, "Mini ERP · Portfolio Project  |  Confidential")
    canv.restoreState()


# ── Reusable flowable helpers ────────────────────────────────────────────────
def rule(color=HexColor("#CBD5E1"), thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=4)


def section_header(num: str, title: str, subtitle: str, route: str):
    return [
        Paragraph(f"SECTION {num}", S["section_label"]),
        Paragraph(title, S["h2"]),
        rule(BLUE, 1.5),
        Paragraph(route, S["route"]),
        Paragraph(subtitle, S["section_sub"]),
    ]


def bullet(text: str):
    return Paragraph(f"→  {text}", S["bullet"])


def two_col(items: list[str]):
    """Render a list of bullets in two columns."""
    mid = (len(items) + 1) // 2
    left  = [bullet(t) for t in items[:mid]]
    right = [bullet(t) for t in items[mid:]]
    # Pad shorter column
    while len(left) < len(right):
        left.append(Spacer(1, 14))
    while len(right) < len(left):
        right.append(Spacer(1, 14))
    rows = [[l, r] for l, r in zip(left, right)]
    t = Table(rows, colWidths=[(PAGE_W - 2 * MARGIN) / 2] * 2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    return t


def info_table(rows: list[tuple], col_widths=None):
    col_widths = col_widths or [55 * mm, None]
    if col_widths[-1] is None:
        col_widths[-1] = PAGE_W - 2 * MARGIN - sum(col_widths[:-1])
    data = [[Paragraph(str(c), S["small"]) if not isinstance(c, Paragraph) else c
             for c in row] for row in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",       (0, 0), (-1, -1), 0.3, HexColor("#CBD5E1")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def badge(text: str, color=BLUE):
    t = Table([[Paragraph(f"<font color='white'><b>{text}</b></font>",
                          ParagraphStyle("b", fontSize=7, leading=10))]],
              colWidths=[len(text) * 5.5 + 8])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, 0), color),
        ("ROUNDEDCORNERS", (0, 0), (0, 0), [3]),
        ("LEFTPADDING",  (0, 0), (0, 0), 4),
        ("RIGHTPADDING", (0, 0), (0, 0), 4),
        ("TOPPADDING",   (0, 0), (0, 0), 2),
        ("BOTTOMPADDING",(0, 0), (0, 0), 2),
    ]))
    return t


# ── Page builders ────────────────────────────────────────────────────────────

def cover():
    return []          # rendered entirely by _cover_page callback


def toc():
    story = [
        Paragraph("Table of Contents", S["toc_title"]),
        rule(NAVY, 1),
        Spacer(1, 4),
        Paragraph("INTRODUCTION", S["toc_section"]),
        Paragraph("Application Overview  ·  3", S["toc_item"]),
        Paragraph("Getting Started &amp; Login  ·  5", S["toc_item"]),
        Spacer(1, 3),
        Paragraph("01  Login Page  ·  6", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("CORE NAVIGATION", S["toc_section"]),
        Paragraph("02  Dashboard  ·  7", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("WORKFORCE MANAGEMENT", S["toc_section"]),
        Paragraph("03  Employees  ·  8", S["toc_item"]),
        Paragraph("04  Departments  ·  9", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("PAYROLL", S["toc_section"]),
        Paragraph("05  Pay Periods  ·  10", S["toc_item"]),
        Paragraph("06  Payslips  ·  11", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("ACCOUNTS PAYABLE", S["toc_section"]),
        Paragraph("07  Vendors  ·  12", S["toc_item"]),
        Paragraph("08  Invoices  ·  13", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("EXPENSES", S["toc_section"]),
        Paragraph("09  Expense Reports  ·  14", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("PROCUREMENT", S["toc_section"]),
        Paragraph("10  Purchase Requisitions  ·  15", S["toc_item"]),
        Paragraph("11  Purchase Orders  ·  16", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("GENERAL LEDGER", S["toc_section"]),
        Paragraph("12  Chart of Accounts  ·  17", S["toc_item"]),
        Paragraph("13  Journal Entries  ·  18", S["toc_item"]),
        Paragraph("14  Trial Balance  ·  19", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("AI &amp; MLOPS", S["toc_section"]),
        Paragraph("15a  AI Insights  ·  20", S["toc_item"]),
        Paragraph("15b  Model Registry  ·  21", S["toc_item"]),
        Paragraph("15c  Prediction Log  ·  22", S["toc_item"]),
        Paragraph("15d  Finance Chat (AI Chat)  ★ New in v2.0  ·  23", S["toc_new"]),
        Spacer(1, 4),
        Paragraph("ADMINISTRATION", S["toc_section"]),
        Paragraph("16  User Management  ·  26", S["toc_item"]),
        Spacer(1, 4),
        Paragraph("APPENDIX", S["toc_section"]),
        Paragraph("A  Invoice Status Reference  ·  27", S["toc_item"]),
        Paragraph("B  Keyboard Shortcuts &amp; Tips  ·  27", S["toc_item"]),
        Paragraph("C  Phase Roadmap  ·  28", S["toc_item"]),
    ]
    return story


def app_overview():
    modules = [
        ("Workforce Management",
         "Manage employees, departments, job titles, and employment lifecycle from "
         "hiring to termination."),
        ("Payroll",
         "Process pay periods, generate payslips, manage pay groups, and track "
         "gross/net compensation with deductions."),
        ("Accounts Payable",
         "Track vendors, manage invoices through full approval lifecycle "
         "(draft → approved → paid), and reconcile payments."),
        ("Expenses",
         "Submit and approve employee expense reports with multi-status workflow -- "
         "draft, submitted, approved, rejected, paid."),
        ("Procurement",
         "Raise purchase requisitions, convert them to purchase orders, and track "
         "delivery status through goods receipt."),
        ("General Ledger",
         "Maintain the chart of accounts, post journal entries, manage fiscal "
         "periods, and view the trial balance."),
        ("AI / MLOps",
         "Machine-learning models surface attrition risk, expense violations, "
         "payroll anomalies, and invoice mis-classifications in real time."),
        ("Finance Chat  ★",
         "Ask questions about your ERP data in plain English -- the AI translates "
         "them to SQL, queries live data, and returns a formatted answer. "
         "New in Phase 3."),
        ("Administration",
         "Manage platform users, assign roles, and control access permissions "
         "across every module."),
    ]
    data = []
    for name, desc in modules:
        is_new = "★" in name
        name_p = Paragraph(
            f"<font color='{'#16A34A' if is_new else '#0057AE'}'><b>{name}</b></font>",
            ParagraphStyle("mn", fontSize=9, leading=13))
        desc_p = Paragraph(desc, S["small"])
        data.append([name_p, desc_p])

    mod_table = Table(data, colWidths=[52 * mm, PAGE_W - 2 * MARGIN - 52 * mm])
    mod_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",       (0, 0), (-1, -1), 0.3, HexColor("#CBD5E1")),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 7), (-1, 7), HexColor("#F0FDF4")),  # Finance Chat row
    ]))

    stack_data = [
        [Paragraph("<b>Layer</b>", S["small"]),
         Paragraph("<b>Technology</b>", S["small"])],
        ["Backend",  "FastAPI · Python 3.11 · SQLAlchemy 2.0 (async) · Alembic"],
        ["Database", "PostgreSQL 15 · pgvector (Phase 3 embeddings)"],
        ["Cache / Queue", "Redis 7 · Celery"],
        ["ML / LLM", "scikit-learn · joblib · Anthropic Claude · Groq · Ollama"],
        ["Frontend", "React 18 · TypeScript · Vite · Tailwind CSS"],
        ["Infrastructure", "Docker · Docker Compose · GCP free tier · Nginx"],
    ]
    stack_table = info_table(stack_data, col_widths=[45 * mm, None])

    roles_data = [
        [Paragraph("<b>Role</b>", S["small"]),
         Paragraph("<b>Username</b>", S["small"]),
         Paragraph("<b>Access Level</b>", S["small"])],
        ["Platform Admin", "platform_admin", "Full access to all modules + administration"],
        ["HR Admin", "hr_admin", "Full HR, workforce, and payroll access"],
        ["Finance Admin", "finance_admin", "Full AP, expenses, GL, and procurement access"],
        ["Workforce User", "workforce_user1", "Read-only workforce module"],
        ["Payroll User", "payroll_user1", "Read-only payroll module"],
        ["AP User", "ap_user1", "Read-only accounts payable"],
        ["GL User", "gl_user1", "Read-only general ledger"],
    ]
    roles_table = info_table(roles_data, col_widths=[38 * mm, 42 * mm, None])

    return [
        Paragraph("Application Overview", S["h2"]),
        rule(NAVY, 1),
        Paragraph(
            "Mini ERP is a unified enterprise resource planning platform covering HR, payroll, "
            "finance, procurement, and AI-driven insights in a single web application. "
            "Phase 3 adds <b>Finance Chat</b> -- natural-language queries over all ERP data.",
            S["body"]),
        Spacer(1, 6),
        mod_table,
        Spacer(1, 10),
        Paragraph("Technology Stack", S["h3"]),
        stack_table,
        Spacer(1, 10),
        Paragraph("User Roles &amp; Access", S["h3"]),
        roles_table,
        PageBreak(),
    ]


def getting_started():
    steps = [
        ("1  Open the application",
         "Navigate to the Mini ERP URL in your web browser (Chrome or Edge recommended). "
         "The application is hosted at <font color='#0057AE'>http://34.13.57.203:3000</font>."),
        ("2  Sign in with your credentials",
         "Enter your username and password on the Login page. Your account will have been "
         "set up by the Platform Administrator."),
        ("3  Explore the Dashboard",
         "After login you land on the Dashboard, which shows high-level counts across "
         "employees, invoices, expenses, and purchase orders."),
        ("4  Navigate using the sidebar",
         "The collapsible left sidebar groups all modules. Click any menu item to jump to "
         "that section. Your role determines which modules are accessible."),
        ("5  Use search and filters",
         "Most list pages include a search bar and status filter dropdown. Type to search "
         "by name, number, or email."),
        ("6  Create &amp; edit records (Admin only)",
         "Users with Admin roles see action buttons and pencil edit icons. Standard users "
         "have read-only access."),
        ("7  Try Finance Chat  ★",
         "Click <b>AI Chat</b> in the sidebar to open Finance Chat. Type any question about "
         "your financial data in plain English and press Enter. No SQL knowledge required."),
    ]
    data = []
    for title, desc in steps:
        data.append([
            Paragraph(f"<b>{title}</b>", ParagraphStyle("st", fontSize=9, textColor=BLUE,
                                                         fontName="Helvetica-Bold", leading=13)),
            Paragraph(desc, S["small"]),
        ])
    step_table = Table(data, colWidths=[48 * mm, PAGE_W - 2 * MARGIN - 48 * mm])
    step_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",       (0, 0), (-1, -1), 0.3, HexColor("#CBD5E1")),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 6), (-1, 6), HexColor("#F0FDF4")),  # Finance Chat step
    ]))

    creds_data = [
        [Paragraph("<b>Role</b>", S["small"]),
         Paragraph("<b>Credentials</b>", S["small"])],
        ["Platform Administrator", "platform_admin / Admin@123!"],
        ["HR Administrator", "hr_admin / Admin@123!"],
        ["Finance Administrator", "finance_admin / Admin@123!"],
        ["Module-specific users", "workforce_user1, payroll_user1, etc. / User@123!"],
    ]
    creds_table = info_table(creds_data, col_widths=[55 * mm, None])

    return [
        Paragraph("Getting Started", S["h2"]),
        rule(NAVY, 1),
        Paragraph(
            "Follow these steps to begin using Mini ERP for the first time.",
            S["body"]),
        Spacer(1, 6),
        step_table,
        Spacer(1, 10),
        Paragraph("Default Login Credentials (Demo)", S["h3"]),
        creds_table,
        PageBreak(),
    ]


def _section_page(num, title, route, subtitle, bullets_left, bullets_right=None,
                  note=None, tip=None, warning=None, extra=None):
    story = section_header(num, title, subtitle, route)
    story.append(Spacer(1, 6))
    if bullets_right:
        story.append(two_col(bullets_left + (bullets_right or [])))
        # Actually split them
        story = section_header(num, title, subtitle, route)
        story.append(Spacer(1, 6))
        mid = len(bullets_left)
        all_b = bullets_left + bullets_right
        half = mid
        left_b  = all_b[:half]
        right_b = all_b[half:]
        rows = []
        for l, r in zip(left_b, right_b):
            rows.append([bullet(l), bullet(r)])
        if len(left_b) > len(right_b):
            rows.append([bullet(left_b[-1]), Spacer(1, 14)])
        t = Table(rows, colWidths=[(PAGE_W - 2 * MARGIN) / 2] * 2)
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
        story.append(t)
    else:
        for b in bullets_left:
            story.append(bullet(b))
    if note:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Note:</b> {note}", S["note"]))
    if tip:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Tip:</b> {tip}", S["tip"]))
    if warning:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Important:</b> {warning}", S["warning"]))
    if extra:
        story += extra
    story.append(PageBreak())
    return story


def page_login():
    return _section_page(
        "1", "Login Page", "/login",
        "Sign in to Mini ERP and securely access your organisation's data",
        [
            "Enter your username and password then click <b>Sign in</b>",
            "Invalid credentials show an inline error message",
            "After successful login you are redirected to the Dashboard",
            "Sessions are maintained via secure JWT tokens stored in the browser",
            "Each user's access is governed by their assigned role",
            "Contact your Platform Admin if you are locked out",
        ],
        tip="Use platform_admin / Admin@123! for full admin access in the demo environment.",
    )


def page_dashboard():
    return _section_page(
        "2", "Dashboard", "/dashboard",
        "Your at-a-glance view of key ERP metrics",
        [
            "<b>Total Employees</b> -- active headcount from the workforce module",
            "<b>AP Invoices</b> -- total invoices across all statuses",
            "<b>Expense Reports</b> -- all expense reports in the system",
            "<b>Purchase Orders</b> -- total POs raised with vendors",
            "Getting Started panel with quick-links to commonly used pages",
            "Data refreshes automatically on each visit",
        ],
    )


def page_employees():
    return _section_page(
        "3", "Employees", "/workforce/employees",
        "Manage employees, departments, and organisational structure",
        [
            "Search employees by name or email in real-time",
            "Attrition risk badge -- green (&lt;40%), amber (40–60%), red (&gt;60%)",
            "Status badges: active, inactive, on leave, terminated",
            "Paginated table -- 20 records per page with navigation",
            "<b>Admin:</b> Add a new employee via the <b>Add Employee</b> button",
            "<b>Admin:</b> Edit department, job title, or status via the pencil icon",
        ],
        note="Attrition Risk scores are generated by the <b>attrition_predictor</b> ML model. "
             "An employee showing &gt;60% risk should be flagged for a retention conversation. "
             "If all scores show --, go to AI / MLOps → Model Registry and train the model first.",
    )


def page_departments():
    return _section_page(
        "4", "Departments", "/workforce/departments",
        "Manage employees, departments, and organisational structure",
        [
            "View all departments with headcount and manager details",
            "Department codes are used as reference identifiers in other modules",
            "Cost centre linking for GL expense allocation",
            "<b>Admin:</b> Create new departments and assign managers",
            "<b>Admin:</b> Edit department name, code, or manager",
            "Changes to departments are reflected immediately in the Employees page",
        ],
    )


def page_pay_periods():
    return _section_page(
        "5", "Pay Periods", "/payroll/periods",
        "Manage pay periods, process payroll runs, and view employee payslips",
        [
            "View all pay periods with start date, end date, and status",
            "Statuses: open, closed, processed, approved",
            "Each period is linked to a pay group (e.g. Monthly Staff)",
            "<b>Admin:</b> Create new pay periods for a pay group",
            "<b>Admin:</b> Close or process a period to trigger payslip generation",
            "Closed periods are locked to prevent retroactive edits",
        ],
    )


def page_payslips():
    return _section_page(
        "6", "Payslips", "/payroll/payslips",
        "Manage pay periods, process payroll runs, and view employee payslips",
        [
            "Employee name linked to their HR profile",
            "Pay period name for quick identification",
            "Gross Pay shown in standard currency format",
            "Deductions displayed in red for quick identification",
            "Net Pay highlighted in green -- the take-home amount",
            "Status badge: draft, processed, approved, paid",
        ],
    )


def page_vendors():
    return _section_page(
        "7", "Vendors", "/ap/vendors",
        "Manage vendors, invoices, and outgoing payments",
        [
            "View vendor name, code, and contact information",
            "Payment terms stored per vendor (e.g. Net 30, Net 60)",
            "Active / inactive status for controlling whether new orders can be raised",
            "Vendor currency and bank details for payment processing",
            "<b>Admin:</b> Register new vendors with the <b>Add Vendor</b> button",
            "<b>Admin:</b> Update vendor details or mark a vendor inactive",
        ],
    )


def page_invoices():
    status_data = [
        [Paragraph("<b>Status</b>", S["small"]),
         Paragraph("<b>Meaning</b>", S["small"]),
         Paragraph("<b>Outstanding?</b>", S["small"])],
        ["DRAFT",        "Created but not yet submitted",         "No"],
        ["SUBMITTED",    "Submitted for review",                  "Yes"],
        ["UNDER_REVIEW", "Being reviewed by finance team",        "Yes"],
        ["APPROVED",     "Approved, awaiting payment",            "Yes"],
        ["MATCHED",      "Matched against a purchase order",      "Yes"],
        ["POSTED",       "Posted to the general ledger",          "Yes"],
        ["PAID",         "Payment has been made",                 "No"],
        ["REJECTED",     "Rejected -- will not be paid",           "No"],
        ["CANCELLED",    "Cancelled by requester or admin",       "No"],
    ]
    status_table = info_table(status_data, col_widths=[35 * mm, 80 * mm, None])

    story = section_header("8", "Invoices", "Manage vendors, invoices, and outgoing payments",
                           "/ap/invoices")
    story += [
        Spacer(1, 6),
        bullet("Filter invoices by status: All, draft, submitted, approved, paid, overdue, cancelled"),
        bullet("Invoice number, vendor, issue date, and due date at a glance"),
        bullet("Total Amount vs Paid Amount columns to track outstanding balance"),
        bullet("Overdue invoices flagged automatically past due date"),
        bullet("<b>Admin:</b> Create new invoices -- select vendor, dates, amounts, and description"),
        bullet("<b>Admin:</b> Update invoice status to advance through the approval workflow"),
        Spacer(1, 6),
        Paragraph("Invoice Status Reference", S["h3"]),
        status_table,
        Spacer(1, 6),
        Paragraph(
            "<b>Outstanding balance</b> = invoices with status SUBMITTED, UNDER_REVIEW, APPROVED, "
            "MATCHED, or POSTED. You can also ask Finance Chat: "
            "<i>What is the total AP outstanding balance?</i>",
            S["tip"]),
        Paragraph(
            "Once an invoice is marked PAID or CANCELLED it cannot be reversed through the UI. "
            "Contact your Finance Administrator for corrections.",
            S["warning"]),
        PageBreak(),
    ]
    return story


def page_expenses():
    return _section_page(
        "9", "Expense Reports", "/expenses/reports",
        "Submit, review, and approve employee expense claims",
        [
            "Filter by status: draft, submitted, approved, rejected, paid",
            "Report title, submitting employee, total amount, and submission date visible",
            "Status badge tracks position in the approval workflow",
            "<b>Admin:</b> Approve a submitted report with the green tick button",
            "<b>Admin:</b> Reject a report -- a reason must be provided",
            "<b>Admin:</b> Create new expense reports on behalf of employees",
        ],
        note="The AI module can flag expense lines with a violation risk &gt;60% based on policy "
             "rules and historical patterns. Check AI / MLOps → Insights → Expense Violation Risk "
             "before approving high-value reports.",
    )


def page_requisitions():
    return _section_page(
        "10", "Purchase Requisitions", "/procurement/requisitions",
        "Raise purchase requisitions and manage purchase orders",
        [
            "View all PRs with requester, department, and requested amount",
            "Statuses: draft, submitted, approved, rejected, converted to PO",
            "Justification and required-by date captured per requisition",
            "<b>Admin:</b> Approve or reject submitted requisitions",
            "<b>Admin:</b> Create new requisitions on behalf of a department",
            "Approved PRs can be converted directly into a Purchase Order",
        ],
    )


def page_orders():
    return _section_page(
        "11", "Purchase Orders", "/procurement/orders",
        "Raise purchase requisitions and manage purchase orders",
        [
            "Filter by status: draft, sent, acknowledged, partially received, received, cancelled",
            "PO number, vendor, order date, expected delivery, and total amount",
            "Track delivery progress from sent → acknowledged → received",
            "<b>Admin:</b> Create new POs linked to a vendor with order details",
            "<b>Admin:</b> Update PO status and adjust expected delivery date",
            "Cancelled POs are retained for audit trail purposes",
        ],
    )


def page_coa():
    return _section_page(
        "12", "Chart of Accounts", "/gl/accounts",
        "Chart of accounts, journal entries, and financial reporting",
        [
            "Account types: asset, liability, equity, revenue, expense -- colour-coded by badge",
            "Account codes follow standard accounting numbering conventions",
            "Normal balance indicated (debit/credit) per account type",
            "Active / inactive status controls whether the account accepts postings",
            "<b>Admin:</b> Add new accounts with code, name, type, and normal balance",
            "<b>Admin:</b> Edit or deactivate accounts (accounts with postings cannot be deleted)",
        ],
    )


def page_journals():
    return _section_page(
        "13", "Journal Entries", "/gl/journals",
        "Chart of accounts, journal entries, and financial reporting",
        [
            "Journal reference number, description, and posting date",
            "Source indicates whether the journal was auto-generated or manually created",
            "Total debit and credit amounts -- must balance for a valid journal",
            "Status: draft journals are editable; posted journals are locked",
            "<b>Admin:</b> Create manual journal entries with multiple debit/credit lines",
            "<b>Admin:</b> Post a draft journal to make it permanent in the ledger",
        ],
        warning="Posted journals cannot be edited or reversed through the UI. Any correction "
                "requires creating a reversing journal entry. Contact your Finance Administrator.",
    )


def page_trial_balance():
    return _section_page(
        "14", "Trial Balance", "/gl/trial-balance",
        "Chart of accounts, journal entries, and financial reporting",
        [
            "All active GL accounts listed with total debits and credits",
            "Account type colour-coded: asset (blue), liability (red), equity (purple), "
            "revenue (green), expense (orange)",
            "Totals row at the bottom showing overall debit and credit sums",
            "<b>Balanced</b> (green) badge when debits = credits; "
            "<b>Out of Balance</b> (red) if discrepancy exists",
            "Read-only report -- no editing from this view",
            "Refreshed automatically from the latest posted journal entries",
        ],
    )


def page_ai_insights():
    return _section_page(
        "9", "AI Insights Tab", "/ai → Insights",
        "Machine-learning powered insights, model registry, and prediction audit log",
        [
            "<b>Attrition Risk</b> -- top 10 employees most likely to leave",
            "<b>Expense Violation Risk</b> -- top 10 expense lines suspected of policy breach",
            "<b>Invoice Classifications</b> -- AI-predicted spend category vs actual",
            "<b>Payroll Anomalies</b> -- top 10 payslips with statistically unusual pay",
            "Risk bar shows colour-coded percentage (green &lt;40%, amber 40–60%, red &gt;60%)",
            "<b>View All &gt;60%</b> button expands to a full modal of high-risk records",
        ],
        note="If a section shows Model not trained, go to the Model Registry tab and train "
             "the relevant model first. Models must be trained before predictions are available.",
    )


def page_model_registry():
    return _section_page(
        "9", "Model Registry Tab", "/ai → Model Registry",
        "Machine-learning powered insights, model registry, and prediction audit log",
        [
            "<b>Attrition Predictor</b> -- predicts employee attrition risk using HR features",
            "<b>Expense Violation</b> -- detects expense lines that breach policy or norms",
            "<b>Payroll Anomaly</b> -- identifies statistically unusual payslips",
            "<b>Invoice Classifier</b> -- classifies invoices into spend categories via TF-IDF",
            "Metrics displayed: Accuracy, ROC-AUC, F1 Score, CV-AUC (cross-validation)",
            "Use the Refresh button to reload model status from the server",
        ],
    )


def page_prediction_log():
    return _section_page(
        "9", "Prediction Log Tab", "/ai → Prediction Log",
        "Machine-learning powered insights, model registry, and prediction audit log",
        [
            "Model ID (shortened UUID) identifies which model made the prediction",
            "Entity type/ID shows what record was scored (employee, payslip, expense, invoice)",
            "Prediction label: high_risk, violation, anomalous, or low_risk / normal",
            "Probability percentage -- the model's confidence in the prediction",
            "Latency in milliseconds for performance monitoring",
            "Paginated -- 20 rows per page; newest predictions first",
        ],
    )


def page_finance_chat():
    """Two-page Finance Chat section -- new in v2.0 / Phase 3."""

    example_data = [
        [Paragraph("<b>Question</b>", S["small"]),
         Paragraph("<b>What it queries</b>", S["small"])],
        ["What is the total AP outstanding balance?",
         "SUM of invoice total_amount where status NOT IN (PAID, REJECTED, CANCELLED)"],
        ["Show department-wise AP outstanding balance",
         "Groups outstanding invoices by department via GL cost centre"],
        ["Which employees have the highest attrition risk?",
         "Orders hcm.employees by attrition_risk_score DESC"],
        ["Top 5 vendors by invoice amount this year",
         "Groups ap.invoices by vendor, filtered by invoice_date year"],
        ["List all invoices flagged as duplicates",
         "Filters ap.invoices WHERE is_duplicate = true"],
        ["Which expense reports are pending approval?",
         "Filters expenses.expense_reports WHERE status = SUBMITTED"],
        ["Budget vs actual spend by department",
         "Joins gl.budgets with hcm.departments"],
        ["What is our payroll cost this month?",
         "SUM payroll.payslips.gross_pay for current pay period"],
    ]
    example_table = info_table(example_data, col_widths=[75 * mm, None])

    flow_data = [
        [Paragraph("<b>Step</b>", S["small"]),
         Paragraph("<b>What happens</b>", S["small"])],
        ["1  User types a question",
         "Natural language question entered in the chat input and submitted with Enter"],
        ["2  LLM receives schema context",
         "The full ERP database schema + invoice status definitions are sent to the LLM as context"],
        ["3  LLM generates SQL",
         "The LLM calls the run_sql tool with a validated SELECT query"],
        ["4  Backend executes query",
         "Query is safety-checked, wrapped with a row limit, and run against PostgreSQL in a savepoint"],
        ["5  Results formatted",
         "Query results are converted to a markdown table and fed back to the LLM"],
        ["6  LLM answers in plain English",
         "The LLM produces a natural-language summary -- never raw JSON"],
        ["7  Response displayed",
         "Answer shown in the chat; a collapsible SQL panel shows the generated query + data"],
    ]
    flow_table = info_table(flow_data, col_widths=[48 * mm, None])

    provider_data = [
        [Paragraph("<b>Provider</b>", S["small"]),
         Paragraph("<b>Config key</b>", S["small"]),
         Paragraph("<b>Notes</b>", S["small"])],
        ["Anthropic Claude", "LLM_PROVIDER=anthropic", "Default. Best quality. Requires ANTHROPIC_API_KEY."],
        ["Groq",             "LLM_PROVIDER=groq",      "Free tier. Fast. Requires GROQ_API_KEY."],
        ["Ollama (local)",   "LLM_PROVIDER=ollama",    "No API key. Requires local Ollama instance."],
    ]
    provider_table = info_table(provider_data, col_widths=[38 * mm, 52 * mm, None])

    story = section_header("9", "Finance Chat (AI Chat)  ★ New in v2.0",
                           "Ask your ERP data questions in plain English",
                           "/chat")
    story += [
        Paragraph(
            "Finance Chat is a natural-language interface to all ERP data. "
            "Type a question in plain English, and the AI automatically generates and executes "
            "the correct SQL query, then presents the result in a clear, formatted answer. "
            "No SQL knowledge required.",
            S["body"]),
        Spacer(1, 6),
        Paragraph("How it works -- end to end", S["h3"]),
        flow_table,
        Spacer(1, 8),
        Paragraph("Example questions you can ask", S["h3"]),
        example_table,
        PageBreak(),

        # Page 2 of Finance Chat
        Paragraph("SECTION 9  (continued)", S["section_label"]),
        Paragraph("Finance Chat -- Using the Interface", S["h2"]),
        rule(BLUE, 1.5),
        Spacer(1, 6),
        Paragraph("Opening the chat", S["h3"]),
        bullet("Click <b>AI Chat</b> in the left sidebar to navigate to <font color='#0057AE'>/chat</font>"),
        bullet("The welcome screen displays 6 example prompts -- click any to start immediately"),
        bullet("The text input is always enabled -- just start typing and press <b>Enter</b>"),
        bullet("A new conversation is created automatically when you send your first message"),
        Spacer(1, 8),
        Paragraph("During a conversation", S["h3"]),
        bullet("Each assistant reply shows the answer in plain English"),
        bullet("Click the <b>SQL Query</b> panel below any answer to expand the generated SQL and raw data table"),
        bullet("Latency (ms) and token counts are shown per message"),
        bullet("Press <b>Shift+Enter</b> to add a newline without sending"),
        Spacer(1, 8),
        Paragraph("Managing conversations", S["h3"]),
        bullet("Past conversations are listed in the left panel, ordered by most-recent message"),
        bullet("Conversation titles are auto-generated from your first question"),
        bullet("Click the trash icon on a conversation to archive it"),
        bullet("Click <b>New conversation</b> to start a fresh chat session"),
        Spacer(1, 8),
        Paragraph("LLM Provider configuration (Admin)", S["h3"]),
        provider_table,
        Spacer(1, 8),
        Paragraph("Security &amp; data access", S["h3"]),
        bullet("Finance Chat is <b>read-only</b> -- it can only generate SELECT queries"),
        bullet("Forbidden keywords (INSERT, UPDATE, DELETE, DROP, etc.) are blocked server-side"),
        bullet("All queries are wrapped in a row limit (default 500 rows) to prevent data dumps"),
        bullet("Full audit trail: every conversation and message is persisted to the database"),
        bullet("Access is controlled by the AI module permission in RBAC -- Finance Admin and above"),
        Spacer(1, 8),
        Paragraph(
            "Requires ANTHROPIC_API_KEY (or GROQ_API_KEY / local Ollama) to be configured "
            "in the backend environment. Contact your Platform Administrator if Finance Chat "
            "shows a 503 error.",
            S["note"]),
        Paragraph(
            "Results are generated by an AI model and may occasionally be incorrect for very "
            "complex queries. Always verify critical financial figures against the source module "
            "(e.g. AP → Invoices) before using them in reports.",
            S["warning"]),
        PageBreak(),
    ]
    return story


def page_user_management():
    return _section_page(
        "10", "User Management", "/admin/users",
        "Manage platform users, roles, and access permissions",
        [
            "View all platform users with username, email, and assigned role",
            "Account status: active or inactive shown per user",
            "Role badge indicates the user's permission level",
            "<b>Admin:</b> Create new user accounts and assign them a role",
            "<b>Admin:</b> Deactivate user accounts to revoke access without deleting data",
            "<b>Admin:</b> Reassign roles to adjust a user's module permissions",
        ],
        note="Only the Platform Administrator (platform_admin) can access this page. "
             "If you need a new user account or a role change, contact your Platform Administrator.",
    )


def appendix():
    roadmap_data = [
        [Paragraph("<b>Phase</b>", S["small"]),
         Paragraph("<b>Description</b>", S["small"]),
         Paragraph("<b>Status</b>", S["small"])],
        ["Week 0",   "GCP setup, CI/CD, DB schema, RBAC",                                    "✅ Done"],
        ["Phase 1",  "MVP ERP -- Workforce, Payroll, AP, Expenses, Procurement, GL",          "✅ Done"],
        ["Phase 2",  "Machine Learning -- Attrition, Expense Violations, Payroll Anomaly, Invoice Classifier", "✅ Done"],
        ["Phase 3",  "RAG + LLM -- Finance Chat, Duplicate Invoice Detection, OCR Pipeline",  "🔄 In Progress"],
        ["Phase 4",  "Deep Learning -- LSTM Budget Forecaster, CNN Invoice Classifier",       "⏳ Pending"],
        ["Phase 5",  "AI Agents -- Invoice Agent, Expense Audit Agent, Onboarding Agent",     "⏳ Pending"],
        ["Phase 6",  "Agentic Networks -- Financial Close Network, Workforce Planning Network","⏳ Pending"],
        ["Week 11",  "Polish, Docs, Portfolio Deploy",                                        "⏳ Pending"],
    ]
    roadmap_table = info_table(roadmap_data, col_widths=[22 * mm, 110 * mm, None])

    changelog_data = [
        [Paragraph("<b>Version</b>", S["small"]),
         Paragraph("<b>Date</b>", S["small"]),
         Paragraph("<b>Summary</b>", S["small"])],
        ["v2.0.0", "Apr 2026",
         "Phase 3: Finance Chat (Text-to-SQL), Duplicate Invoice Detection, OCR Pipeline, pgvector"],
        ["v2.0.1", "Apr 2026",
         "Bug fixes: savepoint isolation, inline tool-call detection, AP status enum context, "
         "frozen chat input"],
        ["v1.0.0", "Feb 2026",
         "Phase 1 MVP: full ERP CRUD across 7 modules + RBAC"],
        ["v1.1.0", "Mar 2026",
         "Phase 2 ML: 4 ML models, AI insights dashboard, model registry, prediction log"],
    ]
    changelog_table = info_table(changelog_data, col_widths=[18 * mm, 20 * mm, None])

    shortcuts = [
        ("Enter",         "Send message (Finance Chat)"),
        ("Shift+Enter",   "New line without sending (Finance Chat)"),
        ("Ctrl+/",        "Toggle sidebar collapse"),
        ("Esc",           "Close modal / cancel action"),
    ]
    shortcuts_data = [[Paragraph("<b>Key</b>", S["small"]),
                       Paragraph("<b>Action</b>", S["small"])]] + shortcuts
    shortcuts_table = info_table(shortcuts_data, col_widths=[40 * mm, None])

    story = [
        Paragraph("Appendix", S["h2"]),
        rule(NAVY, 1),
        Spacer(1, 6),
        Paragraph("A  Phase Roadmap", S["h3"]),
        roadmap_table,
        Spacer(1, 10),
        Paragraph("B  Version Changelog", S["h3"]),
        changelog_table,
        Spacer(1, 10),
        Paragraph("C  Keyboard Shortcuts", S["h3"]),
        shortcuts_table,
    ]
    return story


# ── Document assembly ─────────────────────────────────────────────────────────

def build():
    out_path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "mini_erp_user_guide.pdf"
    )
    out_path = os.path.abspath(out_path)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=18 * mm,
        bottomMargin=14 * mm,
        title="Mini ERP End-User Guide",
        author="Mini ERP Portfolio Project",
        subject="User Guide v2.0",
    )

    story = []

    # Cover (rendered via onFirstPage callback)
    story.append(PageBreak())

    # Inner pages use header/footer
    story += toc()
    story.append(PageBreak())
    story += app_overview()
    story += getting_started()
    story += page_login()
    story += page_dashboard()
    story += page_employees()
    story += page_departments()
    story += page_pay_periods()
    story += page_payslips()
    story += page_vendors()
    story += page_invoices()
    story += page_expenses()
    story += page_requisitions()
    story += page_orders()
    story += page_coa()
    story += page_journals()
    story += page_trial_balance()
    story += page_ai_insights()
    story += page_model_registry()
    story += page_prediction_log()
    story += page_finance_chat()    # ★ New section
    story += page_user_management()
    story += appendix()

    def first_page(canv, doc):
        _cover_page(canv, doc)

    def later_pages(canv, doc):
        _header_footer(canv, doc)

    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
    print(f"PDF written to {out_path}")
    import pypdf
    r = pypdf.PdfReader(out_path)
    print(f"Total pages: {len(r.pages)}")


if __name__ == "__main__":
    build()
