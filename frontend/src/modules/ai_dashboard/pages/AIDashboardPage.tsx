import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Brain, Zap, ClipboardList, RefreshCw, CheckCircle, AlertTriangle, XCircle, ChevronRight } from 'lucide-react'
import { aiService, entityService } from '../../../services/ai.service'
import { PageHeader } from '../../../components/layout/PageHeader'
import { format } from 'date-fns'

// ── Helpers ───────────────────────────────────────────────────────────────────

const MODEL_TYPES = [
  { value: 'attrition_predictor', label: 'Attrition Predictor', entity: 'employee' },
  { value: 'expense_violation', label: 'Expense Violation', entity: 'expense_line' },
  { value: 'payroll_anomaly', label: 'Payroll Anomaly', entity: 'payslip' },
  { value: 'invoice_classifier', label: 'Invoice Classifier', entity: 'invoice' },
]

function pct(v: number | undefined | null) {
  if (v == null) return '—'
  return `${(v * 100).toFixed(1)}%`
}

function ProbabilityBar({ value, danger }: { value: number; danger: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${danger ? 'bg-red-500' : 'bg-emerald-500'}`}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="text-xs font-mono w-10 text-right">{pct(value)}</span>
    </div>
  )
}

function ResultBadge({ label, danger }: { label: string; danger: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
      danger ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
    }`}>
      {danger ? <AlertTriangle className="h-3 w-3" /> : <CheckCircle className="h-3 w-3" />}
      {label}
    </span>
  )
}

// ── Tabs ──────────────────────────────────────────────────────────────────────

type Tab = 'models' | 'predict' | 'log'

function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'models', label: 'Model Registry', icon: <Brain className="h-4 w-4" /> },
    { id: 'predict', label: 'Run Prediction', icon: <Zap className="h-4 w-4" /> },
    { id: 'log', label: 'Prediction Log', icon: <ClipboardList className="h-4 w-4" /> },
  ]
  return (
    <div className="flex border-b border-gray-200 mb-6">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors -mb-px ${
            active === t.id
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          {t.icon}
          {t.label}
        </button>
      ))}
    </div>
  )
}

// ── Model Registry Tab ────────────────────────────────────────────────────────

function ModelsTab() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['ml-models'],
    queryFn: () => aiService.getModels({ page: 1, page_size: 20 }),
  })

  const trainMut = useMutation({
    mutationFn: (mt: string) => aiService.trainModel(mt),
    onSuccess: () => refetch(),
  })

  if (isLoading) return <div className="text-sm text-gray-500 py-8 text-center">Loading models…</div>

  const models: any[] = data?.items ?? []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{models.length} model(s) registered</p>
        <button onClick={() => refetch()} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800">
          <RefreshCw className="h-3 w-3" /> Refresh
        </button>
      </div>

      {MODEL_TYPES.map((mt) => {
        const active = models.find((m) => m.model_type === mt.value && m.is_active)
        const isTraining = trainMut.isPending && trainMut.variables === mt.value
        return (
          <div key={mt.value} className="border border-gray-200 rounded-xl p-5 bg-white shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900">{mt.label}</h3>
                  {active ? (
                    <span className="px-2 py-0.5 rounded-full text-xs bg-emerald-100 text-emerald-700 font-medium">active</span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-500 font-medium">not trained</span>
                  )}
                </div>
                {active && (
                  <p className="text-xs text-gray-400 font-mono">
                    {active.algorithm} · v{active.version} · {active.train_rows?.toLocaleString()} rows · trained {format(new Date(active.created_at), 'dd MMM yyyy HH:mm')}
                  </p>
                )}
              </div>
              <button
                onClick={() => trainMut.mutate(mt.value)}
                disabled={isTraining}
                className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 disabled:opacity-50 transition-colors"
              >
                <RefreshCw className={`h-3 w-3 ${isTraining ? 'animate-spin' : ''}`} />
                {isTraining ? 'Training…' : 'Retrain'}
              </button>
            </div>

            {active?.metrics?.length > 0 && (() => {
              const m = active.metrics[0]
              const extra = m.extra ?? {}
              return (
                <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {m.accuracy != null && (
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 mb-0.5">Accuracy</p>
                      <p className="text-lg font-bold text-gray-900">{pct(m.accuracy)}</p>
                    </div>
                  )}
                  {m.roc_auc != null && (
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 mb-0.5">ROC-AUC</p>
                      <p className="text-lg font-bold text-gray-900">{pct(m.roc_auc)}</p>
                    </div>
                  )}
                  {m.f1_score != null && (
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 mb-0.5">F1</p>
                      <p className="text-lg font-bold text-gray-900">{pct(m.f1_score)}</p>
                    </div>
                  )}
                  {extra.cv_auc_mean != null && (
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 mb-0.5">CV-AUC</p>
                      <p className="text-lg font-bold text-gray-900">{pct(extra.cv_auc_mean)}</p>
                    </div>
                  )}
                  {extra.f1_macro != null && (
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 mb-0.5">F1-macro</p>
                      <p className="text-lg font-bold text-gray-900">{pct(extra.f1_macro)}</p>
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        )
      })}
    </div>
  )
}

// ── Run Prediction Tab ────────────────────────────────────────────────────────

function PredictTab() {
  const [modelType, setModelType] = useState('attrition_predictor')
  const [entityId, setEntityId] = useState('')
  const [result, setResult] = useState<any>(null)

  const { data: employees = [] } = useQuery({ queryKey: ['emp-list'], queryFn: entityService.getEmployees })
  const { data: payslips = [] } = useQuery({ queryKey: ['ps-list'], queryFn: entityService.getPayslips })
  const { data: invoices = [] } = useQuery({ queryKey: ['inv-list'], queryFn: entityService.getInvoices })

  const predictMut = useMutation({
    mutationFn: async () => {
      if (!entityId) throw new Error('Pick an entity first')
      if (modelType === 'attrition_predictor') return aiService.predictAttrition(entityId)
      if (modelType === 'expense_violation') return aiService.predictExpenseViolation(entityId)
      if (modelType === 'payroll_anomaly') return aiService.predictPayrollAnomaly(entityId)
      if (modelType === 'invoice_classifier') return aiService.predictInvoice(entityId)
    },
    onSuccess: (data) => setResult(data),
    onError: (e: any) => setResult({ error: e?.response?.data?.detail ?? e?.message }),
  })

  const handleModelChange = (v: string) => {
    setModelType(v)
    setEntityId('')
    setResult(null)
  }

  const renderEntityPicker = () => {
    if (modelType === 'attrition_predictor') {
      return (
        <select value={entityId} onChange={(e) => setEntityId(e.target.value)} className={selectCls}>
          <option value="">Select employee…</option>
          {employees.map((e: any) => (
            <option key={e.id} value={e.id}>{e.full_name ?? `${e.first_name} ${e.last_name}`} ({e.employee_number})</option>
          ))}
        </select>
      )
    }
    if (modelType === 'payroll_anomaly') {
      return (
        <select value={entityId} onChange={(e) => setEntityId(e.target.value)} className={selectCls}>
          <option value="">Select payslip…</option>
          {payslips.map((p: any) => (
            <option key={p.id} value={p.id}>Payslip {p.payslip_number ?? p.id.slice(0, 8)} — £{Number(p.gross_pay).toLocaleString()}</option>
          ))}
        </select>
      )
    }
    if (modelType === 'invoice_classifier') {
      return (
        <select value={entityId} onChange={(e) => setEntityId(e.target.value)} className={selectCls}>
          <option value="">Select invoice…</option>
          {invoices.map((i: any) => (
            <option key={i.id} value={i.id}>{i.invoice_number} — £{Number(i.total_amount).toLocaleString()} ({i.vendor_name ?? 'Vendor'})</option>
          ))}
        </select>
      )
    }
    // expense_violation — needs line ID; show a note
    return (
      <div className="space-y-2">
        <input
          value={entityId}
          onChange={(e) => setEntityId(e.target.value)}
          placeholder="Paste expense line UUID…"
          className={selectCls}
        />
        <p className="text-xs text-gray-400">Find line IDs via the Expenses module or API.</p>
      </div>
    )
  }

  const renderResult = () => {
    if (!result) return null
    if (result.error) {
      return (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start gap-2">
          <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>{result.error}</span>
        </div>
      )
    }

    return (
      <div className="mt-6 border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-700">Prediction Result</span>
          <span className="text-xs text-gray-400 font-mono">{result.latency_ms}ms</span>
        </div>

        <div className="p-5 space-y-5">
          {/* Attrition */}
          {result.risk_score != null && (
            <>
              <div className="flex items-center gap-3">
                <ResultBadge label={result.prediction} danger={result.prediction === 'high_risk'} />
                <span className="text-sm text-gray-500">Risk score</span>
              </div>
              <ProbabilityBar value={result.risk_score} danger={result.risk_score >= 0.5} />
            </>
          )}

          {/* Expense violation */}
          {result.is_violation != null && (
            <>
              <div className="flex items-center gap-3">
                <ResultBadge label={result.prediction} danger={result.is_violation} />
                <span className="text-xs text-gray-400">mode: {result.model_mode}</span>
              </div>
              <ProbabilityBar value={result.probability} danger={result.is_violation} />
            </>
          )}

          {/* Payroll anomaly */}
          {result.is_anomalous != null && (
            <>
              <div className="flex items-center gap-3">
                <ResultBadge label={result.prediction} danger={result.is_anomalous} />
                <span className="text-xs text-gray-400">mode: {result.model_mode}</span>
              </div>
              <ProbabilityBar value={result.probability} danger={result.is_anomalous} />
            </>
          )}

          {/* Invoice classifier */}
          {result.predicted_category != null && (
            <>
              <div className="flex items-center gap-3">
                <span className="inline-flex px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
                  {result.predicted_category}
                </span>
                <span className="text-sm text-gray-500">confidence {pct(result.confidence)}</span>
              </div>
              {result.top_3_predictions && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Top 3</p>
                  {result.top_3_predictions.map((p: any) => (
                    <div key={p.category} className="flex items-center gap-2">
                      <span className="text-sm text-gray-700 w-40 truncate">{p.category}</span>
                      <ProbabilityBar value={p.probability} danger={false} />
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Feature importances */}
          {result.top_features?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Top Features</p>
              <div className="space-y-1.5">
                {result.top_features.map((f: any) => (
                  <div key={f.feature} className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 w-44 truncate font-mono">{f.feature}</span>
                    <ProbabilityBar value={f.importance} danger={false} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-xl">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Model</label>
          <select value={modelType} onChange={(e) => handleModelChange(e.target.value)} className={selectCls}>
            {MODEL_TYPES.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Entity</label>
          {renderEntityPicker()}
        </div>

        <button
          onClick={() => predictMut.mutate()}
          disabled={!entityId || predictMut.isPending}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-40 transition-colors"
        >
          <Zap className="h-4 w-4" />
          {predictMut.isPending ? 'Running…' : 'Run Prediction'}
        </button>
      </div>

      {renderResult()}
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
          No predictions yet — use the Run Prediction tab to score some records.
        </div>
      ) : (
        <div className="overflow-hidden border border-gray-200 rounded-xl">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Model</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Entity</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Prediction</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Probability</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Latency</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {logs.map((log) => {
                const isDanger = ['high_risk', 'violation', 'anomalous'].includes(log.prediction)
                return (
                  <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{log.model_id.slice(0, 8)}…</td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-gray-500">{log.entity_type}/</span>
                      <span className="font-mono text-xs">{log.entity_id.slice(0, 8)}…</span>
                    </td>
                    <td className="px-4 py-3">
                      <ResultBadge label={log.prediction} danger={isDanger} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {log.probability != null ? pct(log.probability) : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 font-mono">{log.latency_ms}ms</td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      {format(new Date(log.predicted_at), 'dd MMM HH:mm')}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {data?.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
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

const selectCls = 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white'

export default function AIDashboardPage() {
  const [tab, setTab] = useState<Tab>('models')

  return (
    <div>
      <PageHeader
        title="AI / MLOps"
        description="Phase 2 ML — model registry, live predictions, and audit log"
      />
      <TabBar active={tab} onChange={setTab} />
      {tab === 'models' && <ModelsTab />}
      {tab === 'predict' && <PredictTab />}
      {tab === 'log' && <LogTab />}
    </div>
  )
}
