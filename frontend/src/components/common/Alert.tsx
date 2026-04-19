import clsx from 'clsx'

interface Props {
  type?: 'info' | 'success' | 'warning' | 'error'
  message: string
  className?: string
}

const styles: Record<string, React.CSSProperties> = {
  info:    { backgroundColor: '#1a1a2a', border: '1px solid #2a2a50', color: '#9090df' },
  success: { backgroundColor: '#1a2a1a', border: '1px solid #2a4a2a', color: '#90cf90' },
  warning: { backgroundColor: '#2a2010', border: '1px solid #504020', color: '#dfba80' },
  error:   { backgroundColor: '#2a1a1a', border: '1px solid #4a2020', color: '#df9090' },
}

export function Alert({ type = 'info', message, className }: Props) {
  return (
    <div
      className={clsx('rounded-lg px-4 py-3 text-sm', className)}
      style={styles[type]}
    >
      {message}
    </div>
  )
}
