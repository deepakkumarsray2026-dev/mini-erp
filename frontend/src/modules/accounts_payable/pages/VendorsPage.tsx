import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Plus, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { apService } from '../../../services/ap.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import type { Vendor } from '../../../types/ap.types'

type FormData = {
  name: string
  email: string
  phone: string
  payment_terms_days: number
}

function VendorForm({
  defaultValues,
  onSubmit,
  loading,
  onCancel,
}: {
  defaultValues?: Partial<FormData>
  onSubmit: (d: FormData) => void
  loading: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    defaultValues: { payment_terms_days: 30, ...defaultValues },
  })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Vendor Name" required error={errors.name?.message}>
        <input {...register('name', { required: 'Required' })} className={inputCls} placeholder="Company name" />
      </Field>
      <Field label="Payment Terms (days)" required error={errors.payment_terms_days?.message}>
        <input {...register('payment_terms_days', { required: 'Required', valueAsNumber: true })} type="number" className={inputCls} />
      </Field>
      <Field label="Email">
        <input {...register('email')} type="email" className={inputCls} placeholder="billing@vendor.com" />
      </Field>
      <Field label="Phone">
        <input {...register('phone')} className={inputCls} placeholder="+1 (555) 000-0000" />
      </Field>
      <FormActions onCancel={onCancel} loading={loading} />
    </form>
  )
}

export default function VendorsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [modal, setModal] = useState<{ open: boolean; vendor: Vendor | null }>({ open: false, vendor: null })
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))

  const { data, isLoading } = useQuery({
    queryKey: ['vendors', page, debouncedSearch],
    queryFn: () => apService.getVendors(page, 20, debouncedSearch || undefined),
  })

  const createMut = useMutation({
    mutationFn: (d: FormData) => apService.createVendor(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['vendors'] }); setModal({ open: false, vendor: null }) },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: FormData }) => apService.updateVendor(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['vendors'] }); setModal({ open: false, vendor: null }) },
  })

  const handleSearch = (v: string) => {
    setSearch(v)
    clearTimeout((window as unknown as { _vst?: number })._vst)
    ;(window as unknown as { _vst?: number })._vst = setTimeout(() => {
      setDebouncedSearch(v)
      setPage(1)
    }, 400) as unknown as number
  }

  const columns: Column<Vendor>[] = [
    { key: 'vendor_id', header: 'Code', className: 'w-24 font-mono text-xs' },
    { key: 'name', header: 'Name', render: (r) => <span className="font-medium">{r.name}</span> },
    { key: 'email', header: 'Email', render: (r) => r.email ?? '—' },
    { key: 'phone', header: 'Phone', render: (r) => r.phone ?? '—' },
    { key: 'payment_terms_days', header: 'Terms', render: (r) => `Net ${r.payment_terms_days}` },
    {
      key: 'is_active', header: 'Status',
      render: (r) => <Badge variant={r.is_active ? 'green' : 'gray'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>,
    },
    ...(isAdmin ? [{
      key: 'id' as keyof Vendor, header: '',
      render: (r: Vendor) => (
        <button onClick={() => setModal({ open: true, vendor: r })}
          className="text-gray-400 hover:text-blue-600 transition-colors">
          <Pencil className="h-4 w-4" />
        </button>
      ),
      className: 'w-10',
    }] : []),
  ]

  const isEditing = !!modal.vendor
  const isSaving = createMut.isPending || updateMut.isPending

  return (
    <div>
      <PageHeader
        title="Vendors"
        description={`${data?.total ?? 0} vendors`}
        actions={isAdmin ? (
          <button onClick={() => setModal({ open: true, vendor: null })}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add Vendor
          </button>
        ) : undefined}
      />
      <div className="mb-4">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search vendors…"
            className="w-full rounded-lg border border-gray-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
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
        title={isEditing ? 'Edit Vendor' : 'Add Vendor'}
        onClose={() => setModal({ open: false, vendor: null })}
      >
        <VendorForm
          key={modal.vendor?.id ?? 'new'}
          defaultValues={modal.vendor ? {
            name: modal.vendor.name,
            email: modal.vendor.email ?? '',
            phone: modal.vendor.phone ?? '',
            payment_terms_days: modal.vendor.payment_terms_days,
          } : undefined}
          onSubmit={(d) => isEditing ? updateMut.mutate({ id: modal.vendor!.id, d }) : createMut.mutate(d)}
          loading={isSaving}
          onCancel={() => setModal({ open: false, vendor: null })}
        />
      </Modal>
    </div>
  )
}
