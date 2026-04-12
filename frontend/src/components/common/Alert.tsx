import clsx from 'clsx'

interface Props {
  type?: 'info' | 'success' | 'warning' | 'error'
  message: string
  className?: string
}

const styles = {
  info: 'bg-blue-50 text-blue-800 border-blue-200',
  success: 'bg-green-50 text-green-800 border-green-200',
  warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  error: 'bg-red-50 text-red-800 border-red-200',
}

export function Alert({ type = 'info', message, className }: Props) {
  return (
    <div className={clsx('rounded-lg border px-4 py-3 text-sm', styles[type], className)}>
      {message}
    </div>
  )
}
