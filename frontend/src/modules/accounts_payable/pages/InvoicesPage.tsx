import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { apService } from '../../../services/ap.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import type { Invoice, Vendor } from '../../../types/ap.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

type CreateData = {
  vendor_id: string
  invoice_number: string
  invoice_date: string
  due_date: string
  subtotal: number
  total_amount: number
  description: string
}

type UpdateData = { status: string }

function CreateInvoiceForm({
  vendors,
  onSubmit,
  loading,
  onCancel,
}: {
  vendors: Vendor[]
  onSubmit: (d: CreateData) => void
  loading: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<CreateData>()
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Vendor" required error={errors.vendor_id?.message}>
        <select {...register('vendor_id', { required: 'Required' })} className={inputCls}>
          <option value="">Select vendor…</option>
          {vendors.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
        </select>
      </Field>
      <Field label="Invoice Number" required error={errors.invoice_number?.message}>
        <input {...register('invoice_number', { required: 'Required' })} className={inputCls} placeholder="e.g. INV-2024-001" />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Invoice Date" required error={errors.invoice_date?.message}>
          <input {...register('invoice_date', { required: 'Required' })} type="date" className={inputCls} />
        </Field>
        <Field label="Due Date" required error={errors.due_date?.message}>
          <input {...register('due_date', { required: 'Required' })} type="date" className={inputCls} />
        </Field>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Subtotal" required error={errors.subtotal?.message}>
          <input {...register('subtotal', { required: 'Required', valueAsNumber: true })} type="number" step="0.01" className={inputCls} placeholder="0.00" />
        </Field>
        <Field label="Total Amount" required error={errors.total_amount?.message}>
          <input {...register('total_amount', { required: 'Required', valueAsNumber: true })} type="number" step="0.01" className={inputCls} placeholder="0.00" />
        </Field>
      </div>
      <Field label="Description">
        <textarea {...register('description')} className={inputCls} rows={2} placeholder="Optional…" />
      </Field>
      <FormActions onCancel={onCancel} loading={loading} submitLabel="Create Invoice" />
    </form>
  )
}

function EditInvoiceForm({
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
  const statuses = ['draft', 'submitted', 'approved', 'paid', 'overdue', 'cancelled']
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

const statuses = ['', 'draft', 'submitted', 'approved', 'paid', 'overdue', 'cancelled']

export default function InvoicesPage() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [modal, setModal] = useState<{ open: boolean; invoice: Invoice | null; mode: 'create' | 'edit' }>({
    open: false, invoice: null, mode: 'create',
  })
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', page, status],
    queryFn: () => apService.getInvoices(page, 20, status || undefined),
  })

  const { data: vendors = [] } = useQuery({
    queryKey: ['vendors-all'],
    queryFn: () => apService.getAllVendors(),
    enabled: isAdmin === true,
  })

  const createMut = useMutation({
    mutationFn: (d: CreateData) => apService.createInvoice(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['invoices'] }); setModal({ open: false, invoice: null, mode: 'create' }) },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: UpdateData }) => apService.updateInvoice(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['invoices'] }); setModal({ open: false, invoice: null, mode: 'create' }) },
  })

  const columns: Column<Invoice>[] = [
    { key: 'invoice_number', header: 'Invoice #', className: 'font-mono text-xs' },
    { key: 'vendor_name', header: 'Vendor', render: (r) => <span className="font-medium">{r.vendor_name ?? '—'}</span> },
    { key: 'invoice_date', header: 'Date', render: (r) => r.invoice_date ? format(new Date(r.invoice_date), 'MMM d, yyyy') : '—' },
    { key: 'due_date', header: 'Due', render: (r) => r.due_date ? format(new Date(r.due_date), 'MMM d, yyyy') : '—' },
    { key: 'total_amount', header: 'Amount', render: (r) => <span className="font-mono">{fmt(r.total_amount)}</span> },
    { key: 'paid_amount', header: 'Paid', render: (r) => <span className="font-mono text-green-700">{fmt(r.paid_amount)}</span> },
    {
      key: 'status', header: 'Status',
      render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
    },
    ...(isAdmin ? [{
      key: 'id' as keyof Invoice, header: '',
      render: (r: Invoice) => (
        <button onClick={() => setModal({ open: true, invoice: r, mode: 'edit' })}
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
        title="Invoices"
        description={`${data?.total ?? 0} invoices`}
        actions={isAdmin ? (
          <button onClick={() => setModal({ open: true, invoice: null, mode: 'create' })}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add Invoice
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
        title={modal.mode === 'create' ? 'Add Invoice' : 'Edit Invoice'}
        onClose={() => setModal({ open: false, invoice: null, mode: 'create' })}
      >
        {modal.mode === 'create' ? (
          <CreateInvoiceForm
            vendors={vendors}
            onSubmit={(d) => createMut.mutate(d)}
            loading={isSaving}
            onCancel={() => setModal({ open: false, invoice: null, mode: 'create' })}
          />
        ) : (
          <EditInvoiceForm
            key={modal.invoice?.id}
            defaultValues={{ status: modal.invoice?.status ?? 'draft' }}
            onSubmit={(d) => updateMut.mutate({ id: modal.invoice!.id, d })}
            loading={isSaving}
            onCancel={() => setModal({ open: false, invoice: null, mode: 'create' })}
          />
        )}
      </Modal>
    </div>
  )
}
