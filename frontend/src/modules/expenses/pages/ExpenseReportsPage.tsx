import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, CheckCircle, XCircle } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { expensesService } from '../../../services/expenses.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import type { ExpenseReport } from '../../../types/expenses.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

type CreateData = { title: string; period_start: string; period_end: string }

function CreateReportForm({
  onSubmit,
  loading,
  onCancel,
}: {
  onSubmit: (d: CreateData) => void
  loading: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<CreateData>()
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Report Title" required error={errors.title?.message}>
        <input {...register('title', { required: 'Required' })} className={inputCls} placeholder="e.g. Q1 Travel Expenses" />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Period Start" required error={errors.period_start?.message}>
          <input {...register('period_start', { required: 'Required' })} type="date" className={inputCls} />
        </Field>
        <Field label="Period End" required error={errors.period_end?.message}>
          <input {...register('period_end', { required: 'Required' })} type="date" className={inputCls} />
        </Field>
      </div>
      <FormActions onCancel={onCancel} loading={loading} submitLabel="Create Report" />
    </form>
  )
}

function RejectForm({
  onSubmit,
  loading,
  onCancel,
}: {
  onSubmit: (reason: string) => void
  loading: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<{ reason: string }>()
  return (
    <form onSubmit={handleSubmit((d) => onSubmit(d.reason))} className="space-y-4">
      <Field label="Rejection Reason" required error={errors.reason?.message}>
        <textarea {...register('reason', { required: 'Required' })} className={inputCls} rows={3} placeholder="Please provide a reason…" />
      </Field>
      <FormActions onCancel={onCancel} loading={loading} submitLabel="Reject" />
    </form>
  )
}

const statuses = ['', 'draft', 'submitted', 'approved', 'rejected', 'paid']

export default function ExpenseReportsPage() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [modal, setModal] = useState<{
    open: boolean
    mode: 'create' | 'reject'
    report: ExpenseReport | null
  }>({ open: false, mode: 'create', report: null })
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))

  const { data, isLoading } = useQuery({
    queryKey: ['expense-reports', page, status],
    queryFn: () => expensesService.getReports(page, 20, status || undefined),
  })

  const createMut = useMutation({
    mutationFn: (d: CreateData) => expensesService.createReport(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expense-reports'] }); setModal({ open: false, mode: 'create', report: null }) },
  })

  const approveMut = useMutation({
    mutationFn: (id: string) => expensesService.approveReport(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['expense-reports'] }),
  })

  const rejectMut = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => expensesService.rejectReport(id, reason),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expense-reports'] }); setModal({ open: false, mode: 'create', report: null }) },
  })

  const columns: Column<ExpenseReport>[] = [
    { key: 'report_number', header: 'Report #', className: 'font-mono text-xs' },
    { key: 'title', header: 'Title', render: (r) => <span className="font-medium">{r.title}</span> },
    { key: 'employee_name', header: 'Employee', render: (r) => r.employee_name ?? '—' },
    { key: 'total_amount', header: 'Amount', render: (r) => <span className="font-mono">{fmt(r.total_amount)}</span> },
    {
      key: 'created_at', header: 'Submitted',
      render: (r) => r.created_at ? format(new Date(r.created_at), 'MMM d, yyyy') : '—',
    },
    {
      key: 'status', header: 'Status',
      render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
    },
    ...(isAdmin ? [{
      key: 'id' as keyof ExpenseReport, header: 'Actions',
      render: (r: ExpenseReport) => r.status === 'submitted' ? (
        <div className="flex items-center gap-2">
          <button
            onClick={() => approveMut.mutate(r.id)}
            disabled={approveMut.isPending}
            title="Approve"
            className="text-green-600 hover:text-green-800 disabled:opacity-50 transition-colors"
          >
            <CheckCircle className="h-4 w-4" />
          </button>
          <button
            onClick={() => setModal({ open: true, mode: 'reject', report: r })}
            title="Reject"
            className="text-red-500 hover:text-red-700 transition-colors"
          >
            <XCircle className="h-4 w-4" />
          </button>
        </div>
      ) : null,
      className: 'w-24',
    }] : []),
  ]

  const isSaving = createMut.isPending || rejectMut.isPending

  return (
    <div>
      <PageHeader
        title="Expense Reports"
        description={`${data?.total ?? 0} reports`}
        actions={isAdmin ? (
          <button onClick={() => setModal({ open: true, mode: 'create', report: null })}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add Report
          </button>
        ) : undefined}
      />
      <div className="mb-4">
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1) }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          {statuses.map((s) => <option key={s} value={s}>{s || 'All statuses'}</option>)}
        </select>
      </div>
      <DataTable
        columns={columns}
        data={data?.items ?? []}
        loading={isLoading}
        page={page}
        pages={data?.pages}
        total={data?.total}
        onPage={setPage}
      />
      <Modal
        open={modal.open}
        title={modal.mode === 'create' ? 'Add Expense Report' : 'Reject Report'}
        onClose={() => setModal({ open: false, mode: 'create', report: null })}
      >
        {modal.mode === 'create' ? (
          <CreateReportForm
            onSubmit={(d) => createMut.mutate(d)}
            loading={isSaving}
            onCancel={() => setModal({ open: false, mode: 'create', report: null })}
          />
        ) : (
          <RejectForm
            key={modal.report?.id}
            onSubmit={(reason) => rejectMut.mutate({ id: modal.report!.id, reason })}
            loading={isSaving}
            onCancel={() => setModal({ open: false, mode: 'create', report: null })}
          />
        )}
      </Modal>
    </div>
  )
}
