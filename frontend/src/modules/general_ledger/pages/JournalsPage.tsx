import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'
import { useForm, useFieldArray } from 'react-hook-form'
import { glService } from '../../../services/gl.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import { Modal, Field, inputCls, FormActions } from '../../../components/common/Modal'
import { useStore } from '../../../store'
import type { Journal, Account } from '../../../types/gl.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

type LineData = { account_code: string; debit: number; credit: number; description: string }
type CreateData = {
  journal_date: string
  description: string
  fiscal_period_id: string
  lines: LineData[]
}

function CreateJournalForm({
  accounts,
  fiscalPeriods,
  onSubmit,
  loading,
  onCancel,
}: {
  accounts: Account[]
  fiscalPeriods: { id: string; name: string; fiscal_year: number; period_number: number }[]
  onSubmit: (d: CreateData) => void
  loading: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit, control, watch, formState: { errors } } = useForm<CreateData>({
    defaultValues: {
      lines: [
        { account_code: '', debit: 0, credit: 0, description: '' },
        { account_code: '', debit: 0, credit: 0, description: '' },
      ],
    },
  })
  const { fields, append, remove } = useFieldArray({ control, name: 'lines' })
  const lines = watch('lines')

  const totalDebit = lines.reduce((s, l) => s + (Number(l.debit) || 0), 0)
  const totalCredit = lines.reduce((s, l) => s + (Number(l.credit) || 0), 0)
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Fiscal Period" required error={(errors.fiscal_period_id as { message?: string })?.message}>
        <select {...register('fiscal_period_id', { required: 'Required' })} className={inputCls}>
          <option value="">Select period…</option>
          {fiscalPeriods.map((p) => (
            <option key={p.id} value={p.id}>FY{p.fiscal_year}-P{String(p.period_number).padStart(2, '0')} — {p.name}</option>
          ))}
        </select>
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Journal Date" required>
          <input {...register('journal_date', { required: 'Required' })} type="date" className={inputCls} />
        </Field>
      </div>
      <Field label="Description" required>
        <input {...register('description', { required: 'Required' })} className={inputCls} placeholder="e.g. Monthly accrual" />
      </Field>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-gray-700">Journal Lines</label>
          <button type="button" onClick={() => append({ account_code: '', debit: 0, credit: 0, description: '' })}
            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
            <Plus className="h-3 w-3" /> Add Line
          </button>
        </div>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-3 py-2 text-left">Account</th>
                <th className="px-3 py-2 text-right w-28">Debit</th>
                <th className="px-3 py-2 text-right w-28">Credit</th>
                <th className="px-3 py-2 w-8"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {fields.map((field, i) => (
                <tr key={field.id}>
                  <td className="px-3 py-2">
                    <select {...register(`lines.${i}.account_code`, { required: true })} className={inputCls + ' text-xs'}>
                      <option value="">Select account…</option>
                      {accounts.map((a) => (
                        <option key={a.id} value={a.account_code}>{a.account_code} — {a.account_name}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <input {...register(`lines.${i}.debit`, { valueAsNumber: true })} type="number" step="0.01" min="0"
                      className={inputCls + ' text-right text-xs'} placeholder="0.00" />
                  </td>
                  <td className="px-3 py-2">
                    <input {...register(`lines.${i}.credit`, { valueAsNumber: true })} type="number" step="0.01" min="0"
                      className={inputCls + ' text-right text-xs'} placeholder="0.00" />
                  </td>
                  <td className="px-3 py-2">
                    {fields.length > 2 && (
                      <button type="button" onClick={() => remove(i)} className="text-gray-300 hover:text-red-500">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50 text-xs font-semibold">
              <tr>
                <td className="px-3 py-2 text-gray-500">Totals</td>
                <td className={`px-3 py-2 text-right ${isBalanced ? 'text-green-700' : 'text-red-600'}`}>
                  {fmt(totalDebit)}
                </td>
                <td className={`px-3 py-2 text-right ${isBalanced ? 'text-green-700' : 'text-red-600'}`}>
                  {fmt(totalCredit)}
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
        {!isBalanced && totalDebit > 0 && (
          <p className="mt-1 text-xs text-red-600">Journal is not balanced — debits must equal credits</p>
        )}
      </div>

      <FormActions onCancel={onCancel} loading={loading || !isBalanced} submitLabel="Post Journal" />
    </form>
  )
}

export default function JournalsPage() {
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const queryClient = useQueryClient()
  const user = useStore((s) => s.user)
  const isAdmin = user?.roles?.some((r) => r.includes('admin'))

  const { data, isLoading } = useQuery({
    queryKey: ['journals', page],
    queryFn: () => glService.getJournals(page, 20),
  })

  const { data: accounts = [] } = useQuery({
    queryKey: ['gl-accounts-all'],
    queryFn: () => glService.getAllAccounts(),
    enabled: isAdmin === true,
  })

  const { data: fiscalPeriods = [] } = useQuery({
    queryKey: ['fiscal-periods'],
    queryFn: () => glService.getFiscalPeriods(),
    enabled: isAdmin === true,
  })

  const createMut = useMutation({
    mutationFn: (d: CreateData) => glService.createJournal(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['journals'] }); setModalOpen(false) },
  })

  const columns: Column<Journal>[] = [
    { key: 'journal_number', header: 'Journal #', className: 'font-mono text-xs' },
    { key: 'journal_date', header: 'Date', render: (r) => r.journal_date ? format(new Date(r.journal_date), 'MMM d, yyyy') : '—' },
    { key: 'description', header: 'Description', render: (r) => <span className="font-medium">{r.description}</span> },
    { key: 'source', header: 'Reference', render: (r) => r.source ?? '—' },
    { key: 'total_debit', header: 'Debits', render: (r) => <span className="font-mono">{fmt(r.total_debit)}</span> },
    { key: 'total_credit', header: 'Credits', render: (r) => <span className="font-mono">{fmt(r.total_credit)}</span> },
    {
      key: 'status', header: 'Status',
      render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Journal Entries"
        description={`${data?.total ?? 0} journals`}
        actions={isAdmin ? (
          <button onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" /> Add Journal
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
        open={modalOpen}
        title="Add Journal Entry"
        onClose={() => setModalOpen(false)}
        size="lg"
      >
        <CreateJournalForm
          key={modalOpen ? 'open' : 'closed'}
          accounts={accounts}
          fiscalPeriods={fiscalPeriods}
          onSubmit={(d) => createMut.mutate(d)}
          loading={createMut.isPending}
          onCancel={() => setModalOpen(false)}
        />
      </Modal>
    </div>
  )
}
