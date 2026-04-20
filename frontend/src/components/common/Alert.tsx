import clsx from 'clsx'

interface Props {
  type?: 'info' | 'success' | 'warning' | 'error'
  message: string
  className?: string
}

const styles: Record<string, React.CSSProperties> = {
  info:    { backgroundColor: '#EFF6FF', border: '1px solid #BFDBFE', color: '#1D4ED8' },
  success: { backgroundColor: '#F0FDF4', border: '1px solid #BBF7D0', color: '#15803D' },
  warning: { backgroundColor: '#FFFBEB', border: '1px solid #FDE68A', color: '#92400E' },
  error:   { backgroundColor: '#FEF2F2', border: '1px solid #FECACA', color: '#DC2626' },
}

export function Alert({ type = 'info', message, className }: Props) {
  return (
    <div className={clsx('rounded-lg px-4 py-3 text-sm', className)} style={styles[type]}>
      {message}
    </div>
  )
}
