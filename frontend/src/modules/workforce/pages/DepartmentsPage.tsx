import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { workforceService } from '../../../services/workforce.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import type { Department } from '../../../types/workforce.types'

type FormData = { code: string; name: string; description: string }

function DeptForm({
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
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ defaultValues })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Code" required error={errors.code?.message}>
        <input {...register('code', { required: 'Required' })} className={inputCls} placeholder="e.g. ENG" />
      </Field>
      <Field label="Name" required error={errors.name?.message}>
        <input {...register('name', { required: 'Required' })} className={inputCls} placeholder="e.g. Engineering" />
      </Field>
      <Field label="Description">
        <textarea {...register('description')} className={inputCls} rows={3} placeholder="Optional description…" />
      </Field>
      <FormActions onCancel={onCancel} loading={loading} />
    </form>
  )
}

export default function DepartmentsPage() {
  const [page, setPage] = useState(1)
  const [modal, setModal] = useState<{ open: boolean; dept: Department | null }>({ open: false, dept: null })
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))

  const { data, isLoading } = useQuery({
    queryKey: ['departments', page],
    queryFn: () => workforceService.getDepartments(page, 20),
  })

  const createMut = useMutation({
    mutationFn: (d: FormData) => workforceService.createDepartment(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['departments'] }); setModal({ open: false, dept: null }) },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: FormData }) => workforceService.updateDepartment(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['departments'] }); setModal({ open: false, dept: null }) },
  })

  const columns: Column<Department>[] = [
    { key: 'code', header: 'Code', className: 'w-24 font-mono text-xs' },
    { key: 'name', header: 'Name', render: (r) => <span className="font-medium">{r.name}</span> },
    { key: 'description', header: 'Description', render: (r) => r.description ?? '—' },
    {
      key: 'is_active', header: 'Status',
      render: (r) => <Badge variant={r.is_active ? 'green' : 'gray'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>,
    },
    ...(isAdmin ? [{
      key: 'id' as keyof Department, header: '',
      render: (r: Department) => (
        <button onClick={() => setModal({ open: true, dept: r })}
          className="text-gray-400 hover:text-blue-600 transition-colors">
          <Pencil className="h-4 w-4" />
        </button>
      ),
      className: 'w-10',
    }] : []),
  ]

  const isEditing = !!modal.dept
  const isSaving = createMut.isPending || updateMut.isPending

  return (
    <div>
      <PageHeader
        title="Departments"
        description={`${data?.total ?? 0} departments`}
        actions={isAdmin ? (
          <button onClick={() => setModal({ open: true, dept: null })}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add Department
          </button>
        ) : undefined}
      />
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
        title={isEditing ? 'Edit Department' : 'Add Department'}
        onClose={() => setModal({ open: false, dept: null })}
      >
        <DeptForm
          key={modal.dept?.id ?? 'new'}
          defaultValues={modal.dept ? { code: modal.dept.code, name: modal.dept.name, description: modal.dept.description ?? '' } : undefined}
          onSubmit={(d) => isEditing ? updateMut.mutate({ id: modal.dept!.id, d }) : createMut.mutate(d)}
          loading={isSaving}
          onCancel={() => setModal({ open: false, dept: null })}
        />
      </Modal>
    </div>
  )
}
