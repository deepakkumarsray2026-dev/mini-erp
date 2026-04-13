import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { glService } from '../../../services/gl.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import type { Account } from '../../../types/gl.types'

type FormData = {
  account_code: string
  account_name: string
  account_type: string
  normal_balance: string
}

const typeColors: Record<string, 'blue' | 'red' | 'green' | 'purple' | 'orange'> = {
  asset: 'blue', liability: 'red', equity: 'purple', revenue: 'green', expense: 'orange',
}

function AccountForm({
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
      <Field label="Account Code" required error={errors.account_code?.message}>
        <input {...register('account_code', { required: 'Required' })} className={inputCls} placeholder="e.g. 1000" />
      </Field>
      <Field label="Account Name" required error={errors.account_name?.message}>
        <input {...register('account_name', { required: 'Required' })} className={inputCls} placeholder="e.g. Cash and Cash Equivalents" />
      </Field>
      <Field label="Account Type" required error={errors.account_type?.message}>
        <select {...register('account_type', { required: 'Required' })} className={inputCls}>
          <option value="">Select type…</option>
          {['asset', 'liability', 'equity', 'revenue', 'expense'].map((t) => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
      </Field>
      <Field label="Normal Balance" required error={errors.normal_balance?.message}>
        <select {...register('normal_balance', { required: 'Required' })} className={inputCls}>
          <option value="">Select…</option>
          <option value="debit">Debit</option>
          <option value="credit">Credit</option>
        </select>
      </Field>
      <FormActions onCancel={onCancel} loading={loading} />
    </form>
  )
}

export default function AccountsPage() {
  const [page, setPage] = useState(1)
  const [modal, setModal] = useState<{ open: boolean; account: Account | null }>({ open: false, account: null })
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))

  const { data, isLoading } = useQuery({
    queryKey: ['gl-accounts', page],
    queryFn: () => glService.getAccounts(page, 50),
  })

  const createMut = useMutation({
    mutationFn: (d: FormData) => glService.createAccount(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['gl-accounts'] }); setModal({ open: false, account: null }) },
  })

  const updateMut = useMutation({
    mutationFn: ({ code, d }: { code: string; d: FormData }) => glService.updateAccount(code, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['gl-accounts'] }); setModal({ open: false, account: null }) },
  })

  const columns: Column<Account>[] = [
    { key: 'account_code', header: 'Number', className: 'w-28 font-mono text-xs' },
    { key: 'account_name', header: 'Name', render: (r) => <span className="font-medium">{r.account_name}</span> },
    {
      key: 'account_type', header: 'Type',
      render: (r) => <Badge variant={typeColors[r.account_type] ?? 'gray'}>{r.account_type}</Badge>,
    },
    { key: 'normal_balance', header: 'Normal Balance' },
    {
      key: 'is_active', header: 'Status',
      render: (r) => <Badge variant={r.is_active ? 'green' : 'gray'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>,
    },
    ...(isAdmin ? [{
      key: 'id' as keyof Account, header: '',
      render: (r: Account) => (
        <button onClick={() => setModal({ open: true, account: r })}
          className="text-gray-400 hover:text-blue-600 transition-colors">
          <Pencil className="h-4 w-4" />
        </button>
      ),
      className: 'w-10',
    }] : []),
  ]

  const isEditing = !!modal.account
  const isSaving = createMut.isPending || updateMut.isPending

  return (
    <div>
      <PageHeader
        title="Chart of Accounts"
        description={`${data?.total ?? 0} accounts`}
        actions={isAdmin ? (
          <button onClick={() => setModal({ open: true, account: null })}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add Account
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
        title={isEditing ? 'Edit Account' : 'Add Account'}
        onClose={() => setModal({ open: false, account: null })}
      >
        <AccountForm
          key={modal.account?.id ?? 'new'}
          defaultValues={modal.account ? {
            account_code: modal.account.account_code,
            account_name: modal.account.account_name,
            account_type: modal.account.account_type,
            normal_balance: modal.account.normal_balance,
          } : undefined}
          onSubmit={(d) => isEditing ? updateMut.mutate({ code: modal.account!.account_code, d }) : createMut.mutate(d)}
          loading={isSaving}
          onCancel={() => setModal({ open: false, account: null })}
        />
      </Modal>
    </div>
  )
}
