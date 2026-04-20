#!/usr/bin/env python3
"""Convert USER_GUIDE.md to mini_erp_user_guide.pdf using WeasyPrint."""

import base64
import re
from pathlib import Path

import markdown
from weasyprint import HTML, CSS

DOCS_DIR = Path(__file__).parent
MD_FILE = DOCS_DIR / "USER_GUIDE.md"
PDF_FILE = DOCS_DIR / "mini_erp_user_guide.pdf"
SCREENSHOTS_DIR = DOCS_DIR / "screenshots"


def inline_images(html: str) -> str:
    """Replace relative image src paths with base64 data URIs."""
    def replace_src(m):
        src = m.group(1)
        img_path = DOCS_DIR / src
        if img_path.exists():
            ext = img_path.suffix.lstrip(".")
            mime = "jpeg" if ext in ("jpg", "jpeg") else ext
            data = base64.b64encode(img_path.read_bytes()).decode()
            return f'src="data:image/{mime};base64,{data}"'
        return m.group(0)

    return re.sub(r'src="([^"]+)"', replace_src, html)


CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

@page {
    size: A4;
    margin: 20mm 18mm 22mm 18mm;
    @bottom-center {
        content: "Mini-ERP Platform User Guide  ·  v3.2.0  ·  " counter(page) " / " counter(pages);
        font-size: 8pt;
        color: #6b7280;
        font-family: Inter, sans-serif;
    }
}

@page :first {
    @bottom-center { content: none; }
}

* { box-sizing: border-box; }

body {
    font-family: Inter, -apple-system, sans-serif;
    font-size: 10pt;
    line-height: 1.65;
    color: #1f2937;
    background: #ffffff;
    margin: 0;
    padding: 0;
}

/* ── Cover / title ─────────────────────────────── */
h1:first-of-type {
    font-size: 28pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 3px solid #3b82f6;
    padding-bottom: 10pt;
    margin-top: 0;
}

/* ── Headings ───────────────────────────────────── */
h1 { font-size: 20pt; font-weight: 700; color: #0f172a; margin-top: 28pt; }
h2 { font-size: 15pt; font-weight: 600; color: #1e3a5f; margin-top: 22pt; border-bottom: 1px solid #dbeafe; padding-bottom: 4pt; }
h3 { font-size: 12pt; font-weight: 600; color: #1e40af; margin-top: 16pt; }
h4 { font-size: 10.5pt; font-weight: 600; color: #374151; margin-top: 12pt; }

/* ── Phase section headers ──────────────────────── */
h2[id*="phase"] {
    background: #eff6ff;
    padding: 6pt 10pt;
    border-left: 4px solid #3b82f6;
    border-radius: 3pt;
}

/* ── Paragraphs & lists ─────────────────────────── */
p { margin: 6pt 0; }
ul, ol { margin: 6pt 0; padding-left: 20pt; }
li { margin: 3pt 0; }

/* ── Code ───────────────────────────────────────── */
code {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 8.5pt;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 3pt;
    padding: 1pt 4pt;
    color: #1e293b;
}

pre {
    background: #0f172a;
    border-radius: 5pt;
    padding: 12pt;
    margin: 10pt 0;
    overflow-x: auto;
    page-break-inside: avoid;
}

pre code {
    background: transparent;
    border: none;
    color: #e2e8f0;
    font-size: 8pt;
    padding: 0;
    line-height: 1.55;
}

/* ── Tables ─────────────────────────────────────── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0;
    font-size: 9pt;
    page-break-inside: avoid;
}

thead {
    background: #1e3a5f;
    color: #ffffff;
}

thead th {
    padding: 7pt 9pt;
    text-align: left;
    font-weight: 600;
    letter-spacing: 0.02em;
}

tbody tr:nth-child(even) { background: #f8fafc; }
tbody tr:hover { background: #eff6ff; }

tbody td {
    padding: 6pt 9pt;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
}

/* Status badges in tables */
td:first-child code { font-weight: 600; color: #1e40af; }

/* ── Images / screenshots ───────────────────────── */
img {
    max-width: 100%;
    height: auto;
    border: 1px solid #e2e8f0;
    border-radius: 6pt;
    box-shadow: 0 2pt 8pt rgba(0,0,0,0.10);
    margin: 10pt auto;
    display: block;
    page-break-inside: avoid;
}

/* ── Blockquote / callout ───────────────────────── */
blockquote {
    border-left: 4px solid #3b82f6;
    background: #eff6ff;
    padding: 8pt 14pt;
    margin: 10pt 0;
    border-radius: 0 4pt 4pt 0;
    color: #1e3a5f;
}

/* ── Horizontal rule ────────────────────────────── */
hr {
    border: none;
    border-top: 1px solid #dbeafe;
    margin: 18pt 0;
}

/* ── Strong / em ────────────────────────────────── */
strong { font-weight: 600; color: #0f172a; }

/* ── Page breaks ────────────────────────────────── */
h2 { page-break-before: auto; }
h1 { page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }

/* ── Document history special styling ──────────── */
table:first-of-type thead { background: #0f172a; }

/* ── Footer area ────────────────────────────────── */
.footer { font-size: 8pt; color: #6b7280; text-align: center; margin-top: 24pt; }
"""


def build_pdf():
    print(f"Reading {MD_FILE} ...")
    md_text = MD_FILE.read_text(encoding="utf-8")

    print("Converting Markdown → HTML ...")
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "attr_list", "nl2br"]
    )
    body_html = md.convert(md_text)

    # Inline all screenshot images as base64
    body_html = inline_images(body_html)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Mini-ERP Platform — User Guide</title>
</head>
<body>
{body_html}
</body>
</html>"""

    print(f"Rendering PDF → {PDF_FILE} ...")
    css = CSS(string=CSS_STYLES)
    HTML(string=full_html, base_url=str(DOCS_DIR)).write_pdf(
        str(PDF_FILE), stylesheets=[css]
    )
    size_kb = PDF_FILE.stat().st_size // 1024
    print(f"Done. PDF written: {PDF_FILE}  ({size_kb} KB)")


if __name__ == "__main__":
    build_pdf()
