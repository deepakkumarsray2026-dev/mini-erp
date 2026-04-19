import clsx from 'clsx'

type Variant = 'gray' | 'green' | 'red' | 'yellow' | 'blue' | 'purple' | 'orange'

interface Props {
  children: React.ReactNode
  variant?: Variant
  className?: string
}

const variantStyles: Record<Variant, React.CSSProperties> = {
  gray:   { backgroundColor: '#222224', color: '#888884', border: '1px solid #2e2e32' },
  green:  { backgroundColor: '#1a2a1a', color: '#7abf7a', border: '1px solid #2a4a2a' },
  red:    { backgroundColor: '#2a1a1a', color: '#df9090', border: '1px solid #4a2020' },
  yellow: { backgroundColor: '#2a2010', color: '#dfba80', border: '1px solid #504020' },
  blue:   { backgroundColor: '#1a1a2a', color: '#8888df', border: '1px solid #2a2a50' },
  purple: { backgroundColor: '#22102a', color: '#bf80df', border: '1px solid #42204a' },
  orange: { backgroundColor: '#2a1a0a', color: '#d97757', border: '1px solid #4a3010' },
}

export function Badge({ children, variant = 'gray', className }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium',
        className,
      )}
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
