import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Plus, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { workforceService } from '../../../services/workforce.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import { useNotification, getErrorMessage } from '../../../hooks/useNotification'
import type { Employee, Department } from '../../../types/workforce.types'
import { format } from 'date-fns'

type FormData = {
  first_name: string
  last_name: string
  email: string
  department_id: string
  job_id: string
  hire_date: string
  employment_type: string
}

function EmployeeForm({
  defaultValues,
  departments,
  jobs,
  onSubmit,
  loading,
  onCancel,
}: {
  defaultValues?: Partial<FormData>
  departments: Department[]
  jobs: { id: string; title: string; code: string }[]
  onSubmit: (d: FormData) => void
  loading: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ defaultValues })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Field label="First Name" required error={errors.first_name?.message}>
          <input {...register('first_name', { required: 'Required' })} className={inputCls} />
        </Field>
        <Field label="Last Name" required error={errors.last_name?.message}>
          <input {...register('last_name', { required: 'Required' })} className={inputCls} />
        </Field>
      </div>
      <Field label="Email" required error={errors.email?.message}>
        <input {...register('email', { required: 'Required' })} type="email" className={inputCls} placeholder="employee@company.com" />
      </Field>
      <Field label="Department" required error={errors.department_id?.message}>
        <select {...register('department_id', { required: 'Required' })} className={inputCls}>
          <option value="">Select department…</option>
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </Field>
      <Field label="Job" required error={errors.job_id?.message}>
        <select {...register('job_id', { required: 'Required' })} className={inputCls}>
          <option value="">Select job…</option>
          {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
        </select>
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Hire Date" required error={errors.hire_date?.message}>
          <input {...register('hire_date', { required: 'Required' })} type="date" className={inputCls} />
        </Field>
        <Field label="Employment Type" required error={errors.employment_type?.message}>
          <select {...register('employment_type', { required: 'Required' })} className={inputCls}>
            <option value="">Select…</option>
            <option value="full_time">Full Time</option>
            <option value="part_time">Part Time</option>
            <option value="contractor">Contractor</option>
            <option value="intern">Intern</option>
          </select>
        </Field>
      </div>
      <FormActions onCancel={onCancel} loading={loading} />
    </form>
  )
}

type UpdateData = { employment_status: string; department_id?: string; job_id?: string }

function EditEmployeeForm({
  defaultValues,
  departments,
  jobs,
  onSubmit,
  loading,
  onCancel,
}: {
  defaultValues: UpdateData
  departments: Department[]
  jobs: { id: string; title: string; code: string }[]
  onSubmit: (d: UpdateData) => void
  loading: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit } = useForm<UpdateData>({ defaultValues })
  const statuses = ['active', 'inactive', 'on_leave', 'terminated']
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Department">
        <select {...register('department_id')} className={inputCls}>
          <option value="">No change</option>
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </Field>
      <Field label="Job">
        <select {...register('job_id')} className={inputCls}>
          <option value="">No change</option>
          {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
        </select>
      </Field>
      <Field label="Status">
        <select {...register('employment_status')} className={inputCls}>
          {statuses.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
      </Field>
      <FormActions onCancel={onCancel} loading={loading} />
    </form>
  )
}

export default function EmployeesPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [modal, setModal] = useState<{ open: boolean; emp: Employee | null; mode: 'create' | 'edit' }>({
    open: false, emp: null, mode: 'create',
  })
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))
  const notify = useNotification()

  const { data, isLoading } = useQuery({
    queryKey: ['employees', page, debouncedSearch],
    queryFn: () => workforceService.getEmployees(page, 20, debouncedSearch || undefined),
  })

  const { data: departments = [] } = useQuery({
    queryKey: ['departments-all'],
    queryFn: () => workforceService.getAllDepartments(),
    enabled: isAdmin === true,
  })

  const { data: jobs = [] } = useQuery({
    queryKey: ['jobs-all'],
    queryFn: () => workforceService.getAllJobs(),
    enabled: isAdmin === true,
  })

  const createMut = useMutation({
    mutationFn: (d: FormData) => workforceService.createEmployee(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['employees'] }); setModal({ open: false, emp: null, mode: 'create' }) },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: UpdateData }) => workforceService.updateEmployee(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['employees'] }); setModal({ open: false, emp: null, mode: 'create' }) },
  })

  const handleSearch = (v: string) => {
    setSearch(v)
    clearTimeout((window as unknown as { _st?: number })._st)
    ;(window as unknown as { _st?: number })._st = setTimeout(() => {
      setDebouncedSearch(v)
      setPage(1)
    }, 400) as unknown as number
  }

  const columns: Column<Employee>[] = [
    { key: 'employee_number', header: 'ID', className: 'w-28 font-mono text-xs' },
    {
      key: 'full_name', header: 'Name',
      render: (r) => (
        <div>
          <p className="font-medium text-gray-900">{r.full_name}</p>
          <p className="text-xs text-gray-400">{r.email}</p>
        </div>
      ),
    },
    { key: 'department_name', header: 'Department', render: (r) => r.department_name ?? '—' },
    { key: 'job_title', header: 'Job Title', render: (r) => r.job_title ?? '—' },
    {
      key: 'hire_date', header: 'Hire Date',
      render: (r) => r.hire_date ? format(new Date(r.hire_date), 'MMM d, yyyy') : '—',
    },
    {
      key: 'employment_status', header: 'Status',
      render: (r) => (
        <Badge variant={statusBadge(r.employment_status)}>
          {r.employment_status.replace('_', ' ')}
        </Badge>
      ),
    },
    ...(isAdmin ? [{
      key: 'id' as keyof Employee, header: '',
      render: (r: Employee) => (
        <button onClick={() => setModal({ open: true, emp: r, mode: 'edit' })}
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
        title="Employees"
        description={`${data?.total ?? 0} total employees`}
        actions={isAdmin ? (
          <button onClick={() => setModal({ open: true, emp: null, mode: 'create' })}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add Employee
          </button>
        ) : undefined}
      />
      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search by name or email…"
            className="w-full rounded-lg border border-gray-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
        title={modal.mode === 'create' ? 'Add Employee' : 'Edit Employee'}
        onClose={() => setModal({ open: false, emp: null, mode: 'create' })}
        size="lg"
      >
        {modal.mode === 'create' ? (
          <EmployeeForm
            departments={departments}
            jobs={jobs}
            onSubmit={(d) => createMut.mutate(d)}
            loading={isSaving}
            onCancel={() => setModal({ open: false, emp: null, mode: 'create' })}
          />
        ) : (
          <EditEmployeeForm
            key={modal.emp?.id}
            defaultValues={{
              employment_status: modal.emp?.employment_status ?? 'active',
              department_id: modal.emp?.department_id,
              job_id: modal.emp?.job_id,
            }}
            departments={departments}
            jobs={jobs}
            onSubmit={(d) => updateMut.mutate({ id: modal.emp!.id, d })}
            loading={isSaving}
            onCancel={() => setModal({ open: false, emp: null, mode: 'create' })}
          />
        )}
      </Modal>
    </div>
  )
}
