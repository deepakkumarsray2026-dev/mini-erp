import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { procurementService } from '../../../services/procurement.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import type { Requisition } from '../../../types/procurement.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

type CreateData = { title: string; justification: string; required_date: string }

function CreateReqForm({
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
      <Field label="Title" required error={errors.title?.message}>
        <input {...register('title', { required: 'Required' })} className={inputCls} placeholder="e.g. Office Supplies Q2" />
      </Field>
      <Field label="Justification">
        <textarea {...register('justification')} className={inputCls} rows={3} placeholder="Business reason for this purchase…" />
      </Field>
      <Field label="Required By">
        <input {...register('required_date')} type="date" className={inputCls} />
      </Field>
      <FormActions onCancel={onCancel} loading={loading} submitLabel="Submit Requisition" />
    </form>
  )
}

type UpdateData = { status: string }

function EditReqForm({
  defaultValues,
  onSubmit,
  loading,
  onCancel,
}: {
  defaultValues: UpdateData
  onSubmit: (d: UpdateData) => void
  loading: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit } = useForm<UpdateData>({ defaultValues })
  const statuses = ['draft', 'submitted', 'approved', 'rejected', 'converted', 'cancelled']
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Status">
        <select {...register('status')} className={inputCls}>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </Field>
      <FormActions onCancel={onCancel} loading={loading} />
    </form>
  )
}

const statuses = ['', 'draft', 'submitted', 'approved', 'rejected', 'converted', 'cancelled']

export default function RequisitionsPage() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [modal, setModal] = useState<{ open: boolean; req: Requisition | null; mode: 'create' | 'edit' }>({
    open: false, req: null, mode: 'create',
  })
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))

  const { data, isLoading } = useQuery({
    queryKey: ['requisitions', page, status],
    queryFn: () => procurementService.getRequisitions(page, 20, status || undefined),
  })

  const createMut = useMutation({
    mutationFn: (d: CreateData) => procurementService.createRequisition(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['requisitions'] }); setModal({ open: false, req: null, mode: 'create' }) },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: UpdateData }) => procurementService.updateRequisition(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['requisitions'] }); setModal({ open: false, req: null, mode: 'create' }) },
  })

  const columns: Column<Requisition>[] = [
    { key: 'pr_number', header: 'Req #', className: 'font-mono text-xs' },
    { key: 'title', header: 'Title', render: (r) => <span className="font-medium">{r.title}</span> },
    { key: 'requester_name', header: 'Requester', render: (r) => r.requester_name ?? '—' },
    { key: 'total_amount', header: 'Amount', render: (r) => <span className="font-mono">{fmt(r.total_amount)}</span> },
    {
      key: 'required_date', header: 'Required By',
      render: (r) => r.required_date ? format(new Date(r.required_date), 'MMM d, yyyy') : '—',
    },
    {
      key: 'status', header: 'Status',
      render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
    },
    ...(isAdmin ? [{
      key: 'id' as keyof Requisition, header: '',
      render: (r: Requisition) => (
        <button onClick={() => setModal({ open: true, req: r, mode: 'edit' })}
          className="text-gray-400 hover:text-blue-600 transition-colors">
          <Pencil className="h-4 w-4" />
        </button>
      ),
      className: 'w-10',
    }] : []),
  ]

  const isSaving = createMut.isPending || updateMut.isPending

  return (
    <div>
      <PageHeader
        title="Purchase Requisitions"
        description={`${data?.total ?? 0} requisitions`}
        actions={isAdmin ? (
          <button onClick={() => setModal({ open: true, req: null, mode: 'create' })}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add Requisition
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
        title={modal.mode === 'create' ? 'Add Requisition' : 'Update Status'}
        onClose={() => setModal({ open: false, req: null, mode: 'create' })}
      >
        {modal.mode === 'create' ? (
          <CreateReqForm
            onSubmit={(d) => createMut.mutate(d)}
            loading={isSaving}
            onCancel={() => setModal({ open: false, req: null, mode: 'create' })}
          />
        ) : (
          <EditReqForm
            key={modal.req?.id}
            defaultValues={{ status: modal.req?.status ?? 'draft' }}
            onSubmit={(d) => updateMut.mutate({ id: modal.req!.id, d })}
            loading={isSaving}
            onCancel={() => setModal({ open: false, req: null, mode: 'create' })}
          />
        )}
      </Modal>
    </div>
  )
}
