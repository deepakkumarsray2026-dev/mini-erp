import clsx from 'clsx'

type Variant = 'gray' | 'green' | 'red' | 'yellow' | 'blue' | 'purple' | 'orange'

interface Props {
  children: React.ReactNode
  variant?: Variant
  className?: string
}

const variants: Record<Variant, string> = {
  gray:   'bg-gray-100 text-gray-600 ring-1 ring-gray-200',
  green:  'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200/60',
  red:    'bg-red-50 text-red-600 ring-1 ring-red-200/60',
  yellow: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200/60',
  blue:   'bg-blue-50 text-blue-700 ring-1 ring-blue-200/60',
  purple: 'bg-violet-50 text-violet-700 ring-1 ring-violet-200/60',
  orange: 'bg-orange-50 text-orange-700 ring-1 ring-orange-200/60',
}

export function Badge({ children, variant = 'gray', className }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium',
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}

export function statusBadge(status: string): Variant {
  const map: Record<string, Variant> = {
    active: 'green', approved: 'green', paid: 'green', posted: 'green',
    received: 'green', healthy: 'green',
    draft: 'gray', open: 'blue', pending: 'yellow',
    submitted: 'blue', processing: 'blue', sent: 'blue',
    acknowledged: 'blue', partially_received: 'blue',
    rejected: 'red', cancelled: 'red', overdue: 'red', terminated: 'red',
    inactive: 'gray', on_leave: 'yellow', reversed: 'orange',
    converted: 'purple',
  }
  return map[status] ?? 'gray'
}
