import clsx from 'clsx'

type Variant = 'gray' | 'green' | 'red' | 'yellow' | 'blue' | 'purple' | 'orange'

interface Props {
  children: React.ReactNode
  variant?: Variant
  className?: string
}

const variantStyles: Record<Variant, React.CSSProperties> = {
  gray:   { backgroundColor: '#F3F4F6', color: '#4B5563', border: '1px solid #E5E7EB' },
  green:  { backgroundColor: '#F0FDF4', color: '#15803D', border: '1px solid #BBF7D0' },
  red:    { backgroundColor: '#FEF2F2', color: '#DC2626', border: '1px solid #FECACA' },
  yellow: { backgroundColor: '#FFFBEB', color: '#92400E', border: '1px solid #FDE68A' },
  blue:   { backgroundColor: '#EFF6FF', color: '#1D4ED8', border: '1px solid #BFDBFE' },
  purple: { backgroundColor: '#F5F3FF', color: '#6D28D9', border: '1px solid #DDD6FE' },
  orange: { backgroundColor: '#FFF7ED', color: '#C2410C', border: '1px solid #FED7AA' },
}

export function Badge({ children, variant = 'gray', className }: Props) {
  return (
    <span
      className={clsx('inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium', className)}
      style={variantStyles[variant]}
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
