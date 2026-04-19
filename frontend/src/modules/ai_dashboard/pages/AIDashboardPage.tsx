import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Brain, TrendingUp, ClipboardList, RefreshCw, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react'
import { aiService } from '../../../services/ai.service'
import { PageHeader } from '../../../components/layout/PageHeader'
import { format } from 'date-fns'

// ── Helpers ───────────────────────────────────────────────────────────────────

function pct(v: number | null | undefined) {
  if (v == null) return '—'
  return `${v.toFixed(1)}%`
}

function RiskBar({ value, threshold = 60 }: { value: number; threshold?: number }) {
  const danger = value >= threshold
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${danger ? 'bg-red-500' : value >= 40 ? 'bg-amber-400' : 'bg-emerald-500'}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className={`text-xs font-semibold font-mono w-12 text-right ${danger ? 'text-red-600' : 'text-gray-600'}`}>
        {pct(value)}
      </span>
    </div>
  )
}

function RiskBadge({ value, threshold = 60 }: { value: number; threshold?: number }) {
  const danger = value >= threshold
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
      danger ? 'bg-red-100 text-red-700' : value >= 40 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
    }`}>
      {danger ? <AlertTriangle className="h-3 w-3" /> : <CheckCircle className="h-3 w-3" />}
      {pct(value)}
    </span>
  )
}

// ── Tabs ──────────────────────────────────────────────────────────────────────

type Tab = 'models' | 'insights' | 'log'

function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'models',   label: 'Model Registry',  icon: <Brain className="h-4 w-4" /> },
    { id: 'insights', label: 'Insights',         icon: <TrendingUp className="h-4 w-4" /> },
    { id: 'log',      label: 'Prediction Log',   icon: <ClipboardList className="h-4 w-4" /> },
  ]
  return (
    <div className="flex border-b border-gray-200 mb-6">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
            active === t.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          {t.icon}{t.label}
        </button>
      ))}
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

  if (isLoading) return <div className="text-sm text-gray-500 py-8 text-center">Loading…</div>
  const models: any[] = data?.items ?? []

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => refetch()} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800">
          <RefreshCw className="h-3 w-3" /> Refresh
        </button>
      </div>
      {MODEL_TYPES.map((mt) => {
        const active = models.find((m) => m.model_type === mt.value && m.is_active)
        return (
          <div key={mt.value} className="border border-gray-200 rounded-xl p-5 bg-white shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-gray-900">{mt.label}</h3>
              {active
                ? <span className="px-2 py-0.5 rounded-full text-xs bg-emerald-100 text-emerald-700 font-medium">active</span>
                : <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-500 font-medium">not trained</span>}
            </div>
            {active && (
              <p className="text-xs text-gray-400 font-mono mb-3">
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
                    <div key={s.label} className="bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 mb-0.5">{s.label}</p>
                      <p className="text-lg font-bold text-gray-900">{s.val}</p>
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
  const attrition = useQuery({ queryKey: ['insight-attrition'], queryFn: () => aiService.getAttritionRisk(10) })
  const expenses  = useQuery({ queryKey: ['insight-expenses'],  queryFn: () => aiService.getExpenseViolations(10) })
  const invoices  = useQuery({ queryKey: ['insight-invoices'],  queryFn: () => aiService.getInvoiceClassifications(10) })

  return (
    <div className="space-y-10">

      {/* Attrition Risk */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-500" />
            <h2 className="text-base font-semibold text-gray-900">Top 10 — Attrition Risk</h2>
          </div>
          <button onClick={() => attrition.refetch()} className="text-xs text-gray-400 hover:text-gray-700 flex items-center gap-1">
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
        </div>
        {attrition.isLoading ? (
          <div className="text-sm text-gray-400 py-6 text-center">Scoring employees…</div>
        ) : attrition.isError ? (
          <div className="text-sm text-red-500 py-4">Model not trained — go to Model Registry and train attrition_predictor.</div>
        ) : (
          <div className="overflow-hidden border border-gray-200 rounded-xl">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Employee</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Department</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide w-48">Attrition Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {(attrition.data ?? []).map((emp: any, i: number) => (
                  <tr key={emp.employee_id} className={emp.risk_pct >= 60 ? 'bg-red-50' : 'hover:bg-gray-50'}>
                    <td className="px-4 py-3 text-gray-400 text-xs font-mono">{i + 1}</td>
                    <td className="px-4 py-3">
                      <p className={`font-medium ${emp.risk_pct >= 60 ? 'text-red-700' : 'text-gray-900'}`}>{emp.full_name}</p>
                      <p className="text-xs text-gray-400">{emp.employee_number}</p>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{emp.department || '—'}</td>
                    <td className="px-4 py-3"><RiskBar value={emp.risk_pct} threshold={60} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Expense Violations */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <h2 className="text-base font-semibold text-gray-900">Top 10 — Expense Violation Risk</h2>
          </div>
          <button onClick={() => expenses.refetch()} className="text-xs text-gray-400 hover:text-gray-700 flex items-center gap-1">
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
        </div>
        {expenses.isLoading ? (
          <div className="text-sm text-gray-400 py-6 text-center">Scoring expense lines…</div>
        ) : expenses.isError ? (
          <div className="text-sm text-red-500 py-4">Model not trained — train expense_violation first.</div>
        ) : (
          <div className="overflow-hidden border border-gray-200 rounded-xl">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Employee</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Category</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide w-40">Violation Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {(expenses.data ?? []).map((line: any, i: number) => (
                  <tr key={line.expense_line_id} className={line.risk_pct >= 60 ? 'bg-red-50' : 'hover:bg-gray-50'}>
                    <td className="px-4 py-3 text-gray-400 text-xs font-mono">{i + 1}</td>
                    <td className={`px-4 py-3 font-medium text-sm ${line.risk_pct >= 60 ? 'text-red-700' : 'text-gray-900'}`}>{line.employee_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{line.category}</td>
                    <td className="px-4 py-3 text-sm font-mono">£{line.amount.toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{line.expense_date}</td>
                    <td className="px-4 py-3"><RiskBar value={line.risk_pct} threshold={60} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Invoice Classifications */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-500" />
            <h2 className="text-base font-semibold text-gray-900">Top 10 — Invoice Classifications</h2>
          </div>
          <button onClick={() => invoices.refetch()} className="text-xs text-gray-400 hover:text-gray-700 flex items-center gap-1">
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
        </div>
        {invoices.isLoading ? (
          <div className="text-sm text-gray-400 py-6 text-center">Classifying invoices…</div>
        ) : invoices.isError ? (
          <div className="text-sm text-red-500 py-4">Model not trained — train invoice_classifier first.</div>
        ) : (
          <div className="overflow-hidden border border-gray-200 rounded-xl">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Invoice</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Vendor</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Actual Category</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Predicted</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {(invoices.data ?? []).map((inv: any, i: number) => (
                  <tr key={inv.invoice_id} className={!inv.is_match ? 'bg-amber-50' : 'hover:bg-gray-50'}>
                    <td className="px-4 py-3 text-gray-400 text-xs font-mono">{i + 1}</td>
                    <td className="px-4 py-3 font-mono text-xs text-blue-600">{inv.invoice_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{inv.vendor_name}</td>
                    <td className="px-4 py-3 text-sm font-mono">£{inv.total_amount.toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs text-gray-600">{inv.actual_category}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        inv.is_match ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {inv.predicted_category}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge value={inv.confidence_pct} threshold={101} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

    </div>
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{data?.total ?? 0} predictions logged</p>
        <button onClick={() => refetch()} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800">
          <RefreshCw className="h-3 w-3" /> Refresh
        </button>
      </div>
      {isLoading ? (
        <div className="text-sm text-gray-500 py-8 text-center">Loading…</div>
      ) : logs.length === 0 ? (
        <div className="text-sm text-gray-400 py-12 text-center border border-dashed border-gray-200 rounded-xl">
          No predictions logged yet.
        </div>
      ) : (
        <div className="overflow-hidden border border-gray-200 rounded-xl">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                {['Model ID', 'Entity', 'Prediction', 'Probability', 'Latency', 'Time'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {logs.map((log) => {
                const isDanger = ['high_risk', 'violation', 'anomalous'].includes(log.prediction)
                return (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{log.model_id.slice(0, 8)}…</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{log.entity_type}/{log.entity_id.slice(0, 8)}…</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        isDanger ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
                      }`}>{log.prediction}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{log.probability != null ? pct(log.probability * 100) : '—'}</td>
                    <td className="px-4 py-3 text-xs text-gray-400 font-mono">{log.latency_ms}ms</td>
                    <td className="px-4 py-3 text-xs text-gray-400">{format(new Date(log.predicted_at), 'dd MMM HH:mm')}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      {data?.pages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
            className="px-3 py-1 text-xs rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50">Prev</button>
          <span className="text-xs text-gray-500">Page {page} of {data.pages}</span>
          <button onClick={() => setPage((p) => Math.min(data.pages, p + 1))} disabled={page === data.pages}
            className="px-3 py-1 text-xs rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50">Next</button>
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
