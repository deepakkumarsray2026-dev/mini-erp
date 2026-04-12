import clsx from 'clsx'

type Variant = 'gray' | 'green' | 'red' | 'yellow' | 'blue' | 'purple' | 'orange'

interface Props {
  children: React.ReactNode
  variant?: Variant
  className?: string
}

const variants: Record<Variant, string> = {
  gray: 'bg-gray-100 text-gray-700',
  green: 'bg-green-100 text-green-700',
  red: 'bg-red-100 text-red-700',
  yellow: 'bg-yellow-100 text-yellow-700',
  blue: 'bg-blue-100 text-blue-700',
  purple: 'bg-purple-100 text-purple-700',
  orange: 'bg-orange-100 text-orange-700',
}

export function Badge({ children, variant = 'gray', className }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
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
