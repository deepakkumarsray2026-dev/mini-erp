import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { procurementService } from '../../../services/procurement.service'
import { apService } from '../../../services/ap.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import type { PurchaseOrder } from '../../../types/procurement.types'
import type { Vendor } from '../../../types/ap.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

type CreateData = {
  vendor_id: string
  issued_date: string
  expected_delivery: string
  total_amount: number
  notes: string
}

function CreatePOForm({
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
      <div className="grid grid-cols-2 gap-4">
        <Field label="Order Date" required error={errors.issued_date?.message}>
          <input {...register('issued_date', { required: 'Required' })} type="date" className={inputCls} />
        </Field>
        <Field label="Expected Delivery">
          <input {...register('expected_delivery')} type="date" className={inputCls} />
        </Field>
      </div>
      <Field label="Total Amount" required error={errors.total_amount?.message}>
        <input {...register('total_amount', { required: 'Required', valueAsNumber: true })} type="number" step="0.01" className={inputCls} placeholder="0.00" />
      </Field>
      <Field label="Notes">
        <textarea {...register('notes')} className={inputCls} rows={2} placeholder="Optional…" />
      </Field>
      <FormActions onCancel={onCancel} loading={loading} submitLabel="Create PO" />
    </form>
  )
}

type UpdateData = { status: string; expected_delivery?: string }

function EditPOForm({
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
  const statuses = ['draft', 'sent', 'acknowledged', 'partially_received', 'received', 'cancelled']
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Status">
        <select {...register('status')} className={inputCls}>
          {statuses.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
      </Field>
      <Field label="Expected Delivery">
        <input {...register('expected_delivery')} type="date" className={inputCls} />
      </Field>
      <FormActions onCancel={onCancel} loading={loading} />
    </form>
  )
}

const statuses = ['', 'draft', 'sent', 'acknowledged', 'partially_received', 'received', 'cancelled']

export default function PurchaseOrdersPage() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [modal, setModal] = useState<{ open: boolean; po: PurchaseOrder | null; mode: 'create' | 'edit' }>({
    open: false, po: null, mode: 'create',
  })
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))

  const { data, isLoading } = useQuery({
    queryKey: ['purchase-orders', page, status],
    queryFn: () => procurementService.getPurchaseOrders(page, 20, status || undefined),
  })

  const { data: vendors = [] } = useQuery({
    queryKey: ['vendors-all'],
    queryFn: () => apService.getAllVendors(),
    enabled: isAdmin === true,
  })

  const createMut = useMutation({
    mutationFn: (d: CreateData) => procurementService.createPurchaseOrder(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['purchase-orders'] }); setModal({ open: false, po: null, mode: 'create' }) },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: UpdateData }) => procurementService.updatePurchaseOrder(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['purchase-orders'] }); setModal({ open: false, po: null, mode: 'create' }) },
  })

  const columns: Column<PurchaseOrder>[] = [
    { key: 'po_number', header: 'PO #', className: 'font-mono text-xs' },
    { key: 'vendor_name', header: 'Vendor', render: (r) => <span className="font-medium">{r.vendor_name ?? '—'}</span> },
    { key: 'issued_date', header: 'Order Date', render: (r) => r.issued_date ? format(new Date(r.issued_date), 'MMM d, yyyy') : '—' },
    {
      key: 'expected_delivery', header: 'Delivery',
      render: (r) => r.expected_delivery ? format(new Date(r.expected_delivery), 'MMM d, yyyy') : '—',
    },
    { key: 'total_amount', header: 'Amount', render: (r) => <span className="font-mono">{fmt(r.total_amount)}</span> },
    {
      key: 'status', header: 'Status',
      render: (r) => <Badge variant={statusBadge(r.status)}>{r.status.replace('_', ' ')}</Badge>,
    },
    ...(isAdmin ? [{
      key: 'id' as keyof PurchaseOrder, header: '',
      render: (r: PurchaseOrder) => (
        <button onClick={() => setModal({ open: true, po: r, mode: 'edit' })}
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
        title="Purchase Orders"
        description={`${data?.total ?? 0} purchase orders`}
        actions={isAdmin ? (
          <button onClick={() => setModal({ open: true, po: null, mode: 'create' })}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add PO
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
        title={modal.mode === 'create' ? 'Add Purchase Order' : 'Edit Purchase Order'}
        onClose={() => setModal({ open: false, po: null, mode: 'create' })}
      >
        {modal.mode === 'create' ? (
          <CreatePOForm
            vendors={vendors}
            onSubmit={(d) => createMut.mutate(d)}
            loading={isSaving}
            onCancel={() => setModal({ open: false, po: null, mode: 'create' })}
          />
        ) : (
          <EditPOForm
            key={modal.po?.id}
            defaultValues={{
              status: modal.po?.status ?? 'draft',
              expected_delivery: modal.po?.expected_delivery ?? '',
            }}
            onSubmit={(d) => updateMut.mutate({ id: modal.po!.id, d })}
            loading={isSaving}
            onCancel={() => setModal({ open: false, po: null, mode: 'create' })}
          />
        )}
      </Modal>
    </div>
  )
}
