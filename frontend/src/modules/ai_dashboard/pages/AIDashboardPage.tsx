import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Brain, TrendingUp, ClipboardList, RefreshCw, AlertTriangle, CheckCircle, ShieldAlert, X, ExternalLink } from 'lucide-react'
import { aiService } from '../../../services/ai.service'
import { PageHeader } from '../../../components/layout/PageHeader'
import { format } from 'date-fns'

// ── Design tokens ─────────────────────────────────────────────────────────────

const T = {
  surface:    '#FFFFFF',
  surfaceAlt: '#F8F9FB',
  border:     '#E2E6EA',
  borderSub:  '#F3F4F6',
  text:       '#111827',
  textSec:    '#374151',
  textMuted:  '#6B7280',
  textFaint:  '#9CA3AF',
  accent:     '#0057AE',
  trackBg:    '#E2E6EA',
  errorBg:    '#FEF2F2',
  errorBrd:   '#FECACA',
  errorTxt:   '#DC2626',
  warnBg:     '#FFFBEB',
  warnBrd:    '#FDE68A',
  warnTxt:    '#92400E',
  successBg:  '#F0FDF4',
  successBrd: '#BBF7D0',
  successTxt: '#15803D',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function pct(v: number | null | undefined) {
  if (v == null) return '—'
  return `${v.toFixed(1)}%`
}

function RiskBar({ value, threshold = 60 }: { value: number; threshold?: number }) {
  const danger = value >= threshold
  const color = danger ? '#EF4444' : value >= 40 ? '#F59E0B' : '#10B981'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: T.trackBg }}>
        <div className="h-full rounded-full" style={{ width: `${Math.min(value, 100)}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-semibold font-mono w-12 text-right" style={{ color: danger ? T.errorTxt : T.textMuted }}>
        {pct(value)}
      </span>
    </div>
  )
}

function RiskBadge({ value, threshold = 60 }: { value: number; threshold?: number }) {
  const danger = value >= threshold
  const style: React.CSSProperties = danger
    ? { backgroundColor: T.errorBg,   color: T.errorTxt,   border: `1px solid ${T.errorBrd}` }
    : value >= 40
    ? { backgroundColor: T.warnBg,    color: T.warnTxt,    border: `1px solid ${T.warnBrd}` }
    : { backgroundColor: T.successBg, color: T.successTxt, border: `1px solid ${T.successBrd}` }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold" style={style}>
      {danger ? <AlertTriangle className="h-3 w-3" /> : <CheckCircle className="h-3 w-3" />}
      {pct(value)}
    </span>
  )
}

// ── Shared table styles ───────────────────────────────────────────────────────

const thCls = 'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide'
const thStyle: React.CSSProperties = { color: T.textMuted, borderBottom: `1px solid ${T.border}`, backgroundColor: T.surfaceAlt }
const tdCls = 'px-4 py-3 text-sm'

// ── Tabs ──────────────────────────────────────────────────────────────────────

type Tab = 'models' | 'insights' | 'log'

function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'models',   label: 'Model Registry', icon: <Brain className="h-4 w-4" /> },
    { id: 'insights', label: 'Insights',        icon: <TrendingUp className="h-4 w-4" /> },
    { id: 'log',      label: 'Prediction Log',  icon: <ClipboardList className="h-4 w-4" /> },
  ]
  return (
    <div className="flex mb-6" style={{ borderBottom: `1px solid ${T.border}` }}>
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className="flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 -mb-px transition-colors"
          style={active === t.id
            ? { borderColor: T.accent, color: T.accent }
            : { borderColor: 'transparent', color: T.textMuted }}
          onMouseEnter={e => { if (active !== t.id) e.currentTarget.style.color = T.textSec }}
          onMouseLeave={e => { if (active !== t.id) e.currentTarget.style.color = T.textMuted }}
        >
          {t.icon}{t.label}
        </button>
      ))}
    </div>
  )
}

// ── View All Modal ────────────────────────────────────────────────────────────

type ModalType = 'attrition' | 'expenses' | 'payroll'

const MODAL_META: Record<ModalType, { title: string; fetchFn: (limit: number) => Promise<any[]> }> = {
  attrition: { title: 'All High Attrition Risk Employees  (> 60%)', fetchFn: (l) => aiService.getAttritionRisk(l) },
  expenses:  { title: 'All High Violation Risk Expense Lines (> 60%)', fetchFn: (l) => aiService.getExpenseViolations(l) },
  payroll:   { title: 'All Anomalous Payslips (> 60%)', fetchFn: (l) => aiService.getPayrollAnomalies(l) },
}

function ViewAllModal({ type, onClose }: { type: ModalType; onClose: () => void }) {
  const meta = MODAL_META[type]
  const { data, isLoading } = useQuery({
    queryKey: ['view-all', type],
    queryFn: () => meta.fetchFn(500),
    staleTime: 60_000,
  })

  const rows: any[] = (data ?? []).filter((r: any) => r.risk_pct > 60)

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 pt-16 px-4 pb-4 overflow-y-auto backdrop-blur-sm">
      <div className="w-full max-w-5xl rounded-2xl shadow-2xl" style={{ backgroundColor: T.surface, border: `1px solid ${T.border}` }}>
        <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: `1px solid ${T.borderSub}` }}>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <h2 className="font-semibold" style={{ color: T.text }}>{meta.title}</h2>
            {!isLoading && (
              <span className="ml-2 px-2 py-0.5 rounded-full text-xs font-semibold"
                style={{ backgroundColor: T.errorBg, color: T.errorTxt, border: `1px solid ${T.errorBrd}` }}>
                {rows.length} record{rows.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <button onClick={onClose} style={{ color: T.textFaint }}><X className="h-5 w-5" /></button>
        </div>
        <div className="p-6">
          {isLoading ? (
            <div className="py-12 text-center text-sm" style={{ color: T.textFaint }}>Loading all records…</div>
          ) : rows.length === 0 ? (
            <div className="py-12 text-center text-sm rounded-xl" style={{ color: T.textFaint, border: `1px dashed ${T.border}` }}>
              No records exceed the 60% threshold.
            </div>
          ) : type === 'attrition' ? (
            <table className="min-w-full text-sm">
              <thead><tr>{['#', 'Employee', 'ID', 'Department', 'Attrition Risk'].map(h => <th key={h} className={thCls} style={thStyle}>{h}</th>)}</tr></thead>
              <tbody>
                {rows.map((r: any, i: number) => (
                  <tr key={r.employee_id} style={{ borderTop: `1px solid ${T.borderSub}`, backgroundColor: T.errorBg }}>
                    <td className={tdCls} style={{ color: T.textFaint, fontFamily: 'monospace' }}>{i + 1}</td>
                    <td className={`${tdCls} font-medium`} style={{ color: T.errorTxt }}>{r.full_name}</td>
                    <td className={tdCls} style={{ color: T.textMuted, fontFamily: 'monospace', fontSize: '0.75rem' }}>{r.employee_number}</td>
                    <td className={tdCls} style={{ color: T.textSec }}>{r.department || '—'}</td>
                    <td className={tdCls}><RiskBar value={r.risk_pct} threshold={60} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : type === 'expenses' ? (
            <table className="min-w-full text-sm">
              <thead><tr>{['#', 'Employee', 'Category', 'Amount', 'Date', 'Violation Risk'].map(h => <th key={h} className={thCls} style={thStyle}>{h}</th>)}</tr></thead>
              <tbody>
                {rows.map((r: any, i: number) => (
                  <tr key={r.expense_line_id} style={{ borderTop: `1px solid ${T.borderSub}`, backgroundColor: T.errorBg }}>
                    <td className={tdCls} style={{ color: T.textFaint, fontFamily: 'monospace' }}>{i + 1}</td>
                    <td className={`${tdCls} font-medium`} style={{ color: T.errorTxt }}>{r.employee_name}</td>
                    <td className={tdCls} style={{ color: T.textSec }}>{r.category}</td>
                    <td className={tdCls} style={{ fontFamily: 'monospace' }}>£{r.amount.toLocaleString()}</td>
                    <td className={tdCls} style={{ color: T.textMuted, fontSize: '0.75rem' }}>{r.expense_date}</td>
                    <td className={tdCls}><RiskBar value={r.risk_pct} threshold={60} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table className="min-w-full text-sm">
              <thead><tr>{['#', 'Employee', 'ID', 'Gross Pay', 'Net Pay', 'Pay Period', 'Anomaly Risk'].map(h => <th key={h} className={thCls} style={thStyle}>{h}</th>)}</tr></thead>
              <tbody>
                {rows.map((r: any, i: number) => (
                  <tr key={r.payslip_id} style={{ borderTop: `1px solid ${T.borderSub}`, backgroundColor: T.errorBg }}>
                    <td className={tdCls} style={{ color: T.textFaint, fontFamily: 'monospace' }}>{i + 1}</td>
                    <td className={`${tdCls} font-medium`} style={{ color: T.errorTxt }}>{r.full_name}</td>
                    <td className={tdCls} style={{ color: T.textMuted, fontFamily: 'monospace', fontSize: '0.75rem' }}>{r.employee_number}</td>
                    <td className={tdCls} style={{ fontFamily: 'monospace' }}>£{r.gross_pay.toLocaleString()}</td>
                    <td className={tdCls} style={{ fontFamily: 'monospace' }}>£{r.net_pay.toLocaleString()}</td>
                    <td className={tdCls} style={{ color: T.textMuted, fontSize: '0.75rem' }}>{r.pay_period_start} → {r.pay_period_end}</td>
                    <td className={tdCls}><RiskBar value={r.risk_pct} threshold={60} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Model Registry Tab ────────────────────────────────────────────────────────

const MODEL_TYPES = [
  { value: 'attrition_predictor', label: 'Attrition Predictor' },
  { value: 'expense_violation',   label: 'Expense Violation' },
  { value: 'payroll_anomaly',     label: 'Payroll Anomaly' },
  { value: 'invoice_classifier',  label: 'Invoice Classifier' },
]

function ModelsTab() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['ml-models'],
    queryFn: () => aiService.getModels({ page: 1, page_size: 20 }),
  })

  if (isLoading) return <div className="py-8 text-center text-sm" style={{ color: T.textFaint }}>Loading…</div>
  const models: any[] = data?.items ?? []

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => refetch()} className="flex items-center gap-1 text-xs transition-colors"
          style={{ color: T.textMuted }}
          onMouseEnter={e => (e.currentTarget.style.color = T.text)}
          onMouseLeave={e => (e.currentTarget.style.color = T.textMuted)}>
          <RefreshCw className="h-3 w-3" /> Refresh
        </button>
      </div>
      {MODEL_TYPES.map((mt) => {
        const active = models.find((m) => m.model_type === mt.value && m.is_active)
        return (
          <div key={mt.value} className="rounded-xl p-5" style={{ border: `1px solid ${T.border}`, backgroundColor: T.surface, boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold" style={{ color: T.text }}>{mt.label}</h3>
              {active
                ? <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ backgroundColor: T.successBg, color: T.successTxt }}>active</span>
                : <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ backgroundColor: '#F3F4F6', color: T.textMuted }}>not trained</span>}
            </div>
            {active && (
              <p className="text-xs font-mono mb-3" style={{ color: T.textFaint }}>
                {active.algorithm} · v{active.version} · {active.train_rows?.toLocaleString()} rows
              </p>
            )}
            {active?.metrics?.length > 0 && (() => {
              const m = active.metrics[0]
              const ex = m.extra ?? {}
              const stats = [
                m.accuracy   != null && { label: 'Accuracy',  val: pct(m.accuracy   * 100) },
                m.roc_auc    != null && { label: 'ROC-AUC',   val: pct(m.roc_auc    * 100) },
                m.f1_score   != null && { label: 'F1',        val: pct(m.f1_score   * 100) },
                ex.cv_auc_mean != null && { label: 'CV-AUC',  val: pct(ex.cv_auc_mean * 100) },
                ex.f1_macro  != null  && { label: 'F1-macro', val: pct(ex.f1_macro  * 100) },
              ].filter(Boolean) as { label: string; val: string }[]
              return (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {stats.map((s) => (
                    <div key={s.label} className="rounded-lg p-3 text-center" style={{ backgroundColor: T.surfaceAlt }}>
                      <p className="text-xs mb-0.5" style={{ color: T.textMuted }}>{s.label}</p>
                      <p className="text-lg font-bold" style={{ color: T.text }}>{s.val}</p>
                    </div>
                  ))}
                </div>
              )
            })()}
          </div>
        )
      })}
    </div>
  )
}

// ── Insights Tab ──────────────────────────────────────────────────────────────

function InsightsTab() {
  const [modal, setModal] = useState<ModalType | null>(null)

  const attrition = useQuery({ queryKey: ['insight-attrition'], queryFn: () => aiService.getAttritionRisk(10) })
  const expenses  = useQuery({ queryKey: ['insight-expenses'],  queryFn: () => aiService.getExpenseViolations(10) })
  const invoices  = useQuery({ queryKey: ['insight-invoices'],  queryFn: () => aiService.getInvoiceClassifications(10) })
  const payroll   = useQuery({ queryKey: ['insight-payroll'],   queryFn: () => aiService.getPayrollAnomalies(10) })

  const tableWrap: React.CSSProperties = {
    border: `1px solid ${T.border}`,
    borderRadius: '0.75rem',
    overflow: 'hidden',
    boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
  }

  const refreshBtn = (fn: () => void) => (
    <button onClick={fn} className="flex items-center gap-1 text-xs transition-colors"
      style={{ color: T.textFaint }}
      onMouseEnter={e => (e.currentTarget.style.color = T.textSec)}
      onMouseLeave={e => (e.currentTarget.style.color = T.textFaint)}>
      <RefreshCw className="h-3 w-3" /> Refresh
    </button>
  )

  const viewAllBtn = (type: ModalType) => (
    <button onClick={() => setModal(type)}
      className="flex items-center gap-1 text-xs font-medium hover:underline"
      style={{ color: T.accent }}>
      <ExternalLink className="h-3 w-3" /> View All &gt; 60%
    </button>
  )

  return (
    <>
    {modal && <ViewAllModal type={modal} onClose={() => setModal(null)} />}
    <div className="space-y-10">

      {/* Attrition Risk */}
      <section>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-500" />
            <h2 className="text-base font-semibold" style={{ color: T.text }}>Top 10 — Attrition Risk</h2>
          </div>
          <div className="flex items-center gap-4">{viewAllBtn('attrition')}{refreshBtn(attrition.refetch)}</div>
        </div>
        <p className="text-xs mb-4" style={{ color: T.textMuted }}>
          Predicts the likelihood of an employee leaving the organisation, based on tenure, performance rating, satisfaction score, salary-to-band ratio, and overtime patterns. Scores above 60% warrant a retention conversation.
        </p>
        {attrition.isLoading ? (
          <div className="py-6 text-center text-sm" style={{ color: T.textFaint }}>Scoring employees…</div>
        ) : attrition.isError ? (
          <div className="py-4 text-sm text-red-500">Model not trained — go to Model Registry and train attrition_predictor.</div>
        ) : (
          <div style={tableWrap}>
            <table className="min-w-full text-sm">
              <thead><tr>{['#', 'Employee', 'Department', 'Attrition Risk'].map(h => <th key={h} className={thCls} style={thStyle}>{h}</th>)}</tr></thead>
              <tbody>
                {(attrition.data ?? []).map((emp: any, i: number) => (
                  <tr key={emp.employee_id}
                    style={{ borderTop: i > 0 ? `1px solid ${T.borderSub}` : undefined, backgroundColor: emp.risk_pct >= 60 ? T.errorBg : undefined }}>
                    <td className={tdCls} style={{ color: T.textFaint, fontFamily: 'monospace', fontSize: '0.75rem' }}>{i + 1}</td>
                    <td className={tdCls}>
                      <p className="font-medium" style={{ color: emp.risk_pct >= 60 ? T.errorTxt : T.text }}>{emp.full_name}</p>
                      <p className="text-xs" style={{ color: T.textFaint }}>{emp.employee_number}</p>
                    </td>
                    <td className={tdCls} style={{ color: T.textSec }}>{emp.department || '—'}</td>
                    <td className={tdCls}><RiskBar value={emp.risk_pct} threshold={60} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Expense Violations */}
      <section>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <h2 className="text-base font-semibold" style={{ color: T.text }}>Top 10 — Expense Violation Risk</h2>
          </div>
          <div className="flex items-center gap-4">{viewAllBtn('expenses')}{refreshBtn(expenses.refetch)}</div>
        </div>
        <p className="text-xs mb-4" style={{ color: T.textMuted }}>
          Flags expense lines that deviate from policy limits and historical spend norms. The model learns from previously marked violations and detects unusual amounts, out-of-policy categories, and patterns linked to high employee violation rates. Scores above 60% should be reviewed before reimbursement.
        </p>
        {expenses.isLoading ? (
          <div className="py-6 text-center text-sm" style={{ color: T.textFaint }}>Scoring expense lines…</div>
        ) : expenses.isError ? (
          <div className="py-4 text-sm text-red-500">Model not trained — train expense_violation first.</div>
        ) : (
          <div style={tableWrap}>
            <table className="min-w-full text-sm">
              <thead><tr>{['#', 'Employee', 'Category', 'Amount', 'Date', 'Violation Risk'].map(h => <th key={h} className={thCls} style={thStyle}>{h}</th>)}</tr></thead>
              <tbody>
                {(expenses.data ?? []).map((line: any, i: number) => (
                  <tr key={line.expense_line_id}
                    style={{ borderTop: i > 0 ? `1px solid ${T.borderSub}` : undefined, backgroundColor: line.risk_pct >= 60 ? T.errorBg : undefined }}>
                    <td className={tdCls} style={{ color: T.textFaint, fontFamily: 'monospace', fontSize: '0.75rem' }}>{i + 1}</td>
                    <td className={`${tdCls} font-medium`} style={{ color: line.risk_pct >= 60 ? T.errorTxt : T.text }}>{line.employee_name}</td>
                    <td className={tdCls} style={{ color: T.textSec }}>{line.category}</td>
                    <td className={tdCls} style={{ fontFamily: 'monospace' }}>£{line.amount.toLocaleString()}</td>
                    <td className={tdCls} style={{ color: T.textMuted, fontSize: '0.75rem' }}>{line.expense_date}</td>
                    <td className={tdCls}><RiskBar value={line.risk_pct} threshold={60} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Invoice Classifications */}
      <section>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-600" />
            <h2 className="text-base font-semibold" style={{ color: T.text }}>Top 10 — Invoice Classifications</h2>
          </div>
          <div className="flex items-center gap-4">{refreshBtn(invoices.refetch)}</div>
        </div>
        <p className="text-xs mb-4" style={{ color: T.textMuted }}>
          Automatically classifies each invoice into a spend category using TF-IDF text features from the invoice description combined with numeric signals. Mismatches between predicted and actual category are highlighted in amber and may indicate miscoding or vendor fraud.
        </p>
        {invoices.isLoading ? (
          <div className="py-6 text-center text-sm" style={{ color: T.textFaint }}>Classifying invoices…</div>
        ) : invoices.isError ? (
          <div className="py-4 text-sm text-red-500">Model not trained — train invoice_classifier first.</div>
        ) : (
          <div style={tableWrap}>
            <table className="min-w-full text-sm">
              <thead><tr>{['#', 'Invoice', 'Vendor', 'Amount', 'Actual Category', 'Predicted', 'Confidence'].map(h => <th key={h} className={thCls} style={thStyle}>{h}</th>)}</tr></thead>
              <tbody>
                {(invoices.data ?? []).map((inv: any, i: number) => (
                  <tr key={inv.invoice_id}
                    style={{ borderTop: i > 0 ? `1px solid ${T.borderSub}` : undefined, backgroundColor: !inv.is_match ? T.warnBg : undefined }}>
                    <td className={tdCls} style={{ color: T.textFaint, fontFamily: 'monospace', fontSize: '0.75rem' }}>{i + 1}</td>
                    <td className={tdCls} style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: T.accent }}>{inv.invoice_number}</td>
                    <td className={tdCls} style={{ color: T.textSec }}>{inv.vendor_name}</td>
                    <td className={tdCls} style={{ fontFamily: 'monospace' }}>£{inv.total_amount.toLocaleString()}</td>
                    <td className={tdCls} style={{ color: T.textSec, fontSize: '0.75rem' }}>{inv.actual_category}</td>
                    <td className={tdCls}>
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full"
                        style={inv.is_match
                          ? { backgroundColor: T.successBg, color: T.successTxt }
                          : { backgroundColor: T.warnBg,    color: T.warnTxt }}>
                        {inv.predicted_category}
                      </span>
                    </td>
                    <td className={tdCls}><RiskBadge value={inv.confidence_pct} threshold={101} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Payroll Anomalies */}
      <section>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-purple-500" />
            <h2 className="text-base font-semibold" style={{ color: T.text }}>Top 10 — Payroll Anomalies</h2>
          </div>
          <div className="flex items-center gap-4">{viewAllBtn('payroll')}{refreshBtn(payroll.refetch)}</div>
        </div>
        <p className="text-xs mb-4" style={{ color: T.textMuted }}>
          Detects payslips where gross pay, net pay, or period-over-period deltas fall outside expected ranges for the employee's role and pay group. Scores above 60% indicate statistically unusual payroll runs that should be reviewed before finalisation.
        </p>
        {payroll.isLoading ? (
          <div className="py-6 text-center text-sm" style={{ color: T.textFaint }}>Scoring payslips…</div>
        ) : payroll.isError ? (
          <div className="py-4 text-sm text-red-500">Model not trained — train payroll_anomaly first.</div>
        ) : (
          <div style={tableWrap}>
            <table className="min-w-full text-sm">
              <thead><tr>{['#', 'Employee', 'Gross Pay', 'Net Pay', 'Pay Period', 'Anomaly Risk'].map(h => <th key={h} className={thCls} style={thStyle}>{h}</th>)}</tr></thead>
              <tbody>
                {(payroll.data ?? []).map((ps: any, i: number) => (
                  <tr key={ps.payslip_id}
                    style={{ borderTop: i > 0 ? `1px solid ${T.borderSub}` : undefined, backgroundColor: ps.risk_pct >= 60 ? T.errorBg : undefined }}>
                    <td className={tdCls} style={{ color: T.textFaint, fontFamily: 'monospace', fontSize: '0.75rem' }}>{i + 1}</td>
                    <td className={tdCls}>
                      <p className="font-medium" style={{ color: ps.risk_pct >= 60 ? T.errorTxt : T.text }}>{ps.full_name}</p>
                      <p className="text-xs" style={{ color: T.textFaint }}>{ps.employee_number}</p>
                    </td>
                    <td className={tdCls} style={{ fontFamily: 'monospace' }}>£{ps.gross_pay.toLocaleString()}</td>
                    <td className={tdCls} style={{ fontFamily: 'monospace' }}>£{ps.net_pay.toLocaleString()}</td>
                    <td className={tdCls} style={{ color: T.textMuted, fontSize: '0.75rem' }}>{ps.pay_period_start} → {ps.pay_period_end}</td>
                    <td className={tdCls}><RiskBar value={ps.risk_pct} threshold={60} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

    </div>
    </>
  )
}

// ── Prediction Log Tab ────────────────────────────────────────────────────────

function LogTab() {
  const [page, setPage] = useState(1)
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['ml-predictions', page],
    queryFn: () => aiService.getPredictions({ page, page_size: 20 }),
  })
  const logs: any[] = data?.items ?? []

  const btnStyle: React.CSSProperties = {
    padding: '4px 12px',
    fontSize: '0.75rem',
    borderRadius: '6px',
    border: `1px solid ${T.border}`,
    backgroundColor: T.surface,
    color: T.textSec,
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm" style={{ color: T.textMuted }}>{data?.total ?? 0} predictions logged</p>
        <button onClick={() => refetch()} className="flex items-center gap-1 text-xs transition-colors"
          style={{ color: T.textFaint }}
          onMouseEnter={e => (e.currentTarget.style.color = T.textSec)}
          onMouseLeave={e => (e.currentTarget.style.color = T.textFaint)}>
          <RefreshCw className="h-3 w-3" /> Refresh
        </button>
      </div>
      {isLoading ? (
        <div className="py-8 text-center text-sm" style={{ color: T.textFaint }}>Loading…</div>
      ) : logs.length === 0 ? (
        <div className="py-12 text-center text-sm rounded-xl" style={{ color: T.textFaint, border: `1px dashed ${T.border}` }}>
          No predictions logged yet.
        </div>
      ) : (
        <div style={{ border: `1px solid ${T.border}`, borderRadius: '0.75rem', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
          <table className="min-w-full text-sm">
            <thead><tr>{['Model ID', 'Entity', 'Prediction', 'Probability', 'Latency', 'Time'].map(h => <th key={h} className={thCls} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {logs.map((log, i) => {
                const isDanger = ['high_risk', 'violation', 'anomalous'].includes(log.prediction)
                return (
                  <tr key={log.id} style={{ borderTop: i > 0 ? `1px solid ${T.borderSub}` : undefined }}>
                    <td className={tdCls} style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: T.textFaint }}>{log.model_id.slice(0, 8)}…</td>
                    <td className={tdCls} style={{ fontSize: '0.75rem', color: T.textMuted }}>{log.entity_type}/{log.entity_id.slice(0, 8)}…</td>
                    <td className={tdCls}>
                      <span className="px-2 py-0.5 rounded-full text-xs font-semibold"
                        style={isDanger
                          ? { backgroundColor: T.errorBg,   color: T.errorTxt }
                          : { backgroundColor: T.successBg, color: T.successTxt }}>
                        {log.prediction}
                      </span>
                    </td>
                    <td className={tdCls} style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: T.textSec }}>{log.probability != null ? pct(log.probability * 100) : '—'}</td>
                    <td className={tdCls} style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: T.textFaint }}>{log.latency_ms}ms</td>
                    <td className={tdCls} style={{ fontSize: '0.75rem', color: T.textMuted }}>{format(new Date(log.predicted_at), 'dd MMM HH:mm')}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      {data?.pages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={{ ...btnStyle, opacity: page === 1 ? 0.4 : 1 }}>Prev</button>
          <span className="text-xs" style={{ color: T.textMuted }}>Page {page} of {data.pages}</span>
          <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page === data.pages} style={{ ...btnStyle, opacity: page === data.pages ? 0.4 : 1 }}>Next</button>
        </div>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AIDashboardPage() {
  const [tab, setTab] = useState<Tab>('insights')
  return (
    <div>
      <PageHeader title="AI / MLOps" description="Phase 2 ML — model registry, top-10 insights, and prediction audit log" />
      <TabBar active={tab} onChange={setTab} />
      {tab === 'models'   && <ModelsTab />}
      {tab === 'insights' && <InsightsTab />}
      {tab === 'log'      && <LogTab />}
    </div>
  )
}
