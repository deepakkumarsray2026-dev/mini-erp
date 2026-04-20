import { chromium } from '/usr/lib/node_modules/playwright/index.mjs';
import { writeFileSync } from 'fs';

const BASE = 'http://localhost:3000';
const API  = 'http://localhost:8000/api/v1';

// ── Login ──────────────────────────────────────────────────────────────────
async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
  await page.fill('input[autocomplete="username"]', 'platform_admin');
  await page.fill('input[autocomplete="current-password"]', process.env.ADMIN_PASSWORD || '');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard', { timeout: 15000 });
  await page.waitForTimeout(1500);
}

// ── Capture helper ─────────────────────────────────────────────────────────
async function shot(page, route, filename, wait = 2000) {
  console.log(`📸  ${route}`);
  await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(wait);
  const buf = await page.screenshot({ fullPage: true });
  writeFileSync(`/opt/mini-erp/docs/screenshots/${filename}`, buf);
}

// ── Main ───────────────────────────────────────────────────────────────────
const browser = await chromium.launch({
  executablePath: '/home/deepakkumarsray2026/.cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const ctx     = await browser.newContext({ viewport: { width: 1400, height: 900 } });
const page    = await ctx.newPage();

// 1. Login page (before auth)
console.log('📸  /login');
await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
writeFileSync('/opt/mini-erp/docs/screenshots/01_login.png', await page.screenshot({ fullPage: true }));

// 2. Authenticate then capture every page
await login(page);

const pages = [
  ['/dashboard',               '02_dashboard.png'],
  ['/workforce/employees',     '03_employees.png'],
  ['/workforce/departments',   '04_departments.png'],
  ['/payroll/periods',         '05_pay_periods.png'],
  ['/payroll/payslips',        '06_payslips.png'],
  ['/ap/vendors',              '07_vendors.png'],
  ['/ap/invoices',             '08_invoices.png'],
  ['/expenses/reports',        '09_expense_reports.png'],
  ['/procurement/requisitions','10_requisitions.png'],
  ['/procurement/orders',      '11_purchase_orders.png'],
  ['/gl/accounts',             '12_chart_of_accounts.png'],
  ['/gl/journals',             '13_journals.png'],
  ['/gl/trial-balance',        '14_trial_balance.png'],
  ['/ai',                      '15_ai_insights.png'],
  ['/admin/users',             '16_admin_users.png'],
];

for (const [route, file] of pages) {
  await shot(page, route, file, 2500);
}

// Extra: AI Models tab
await page.goto(`${BASE}/ai`, { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
const modelsBtn = page.locator('button', { hasText: 'Model Registry' });
if (await modelsBtn.isVisible()) {
  await modelsBtn.click();
  await page.waitForTimeout(2000);
  writeFileSync('/opt/mini-erp/docs/screenshots/15b_ai_models.png', await page.screenshot({ fullPage: true }));
}

// Extra: AI Prediction Log tab
await page.goto(`${BASE}/ai`, { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
const logBtn = page.locator('button', { hasText: 'Prediction Log' });
if (await logBtn.isVisible()) {
  await logBtn.click();
  await page.waitForTimeout(2000);
  writeFileSync('/opt/mini-erp/docs/screenshots/15c_ai_log.png', await page.screenshot({ fullPage: true }));
}

await browser.close();
console.log('✅  All screenshots saved to /opt/mini-erp/docs/screenshots/');
