import clsx from 'clsx'
import { Spinner } from './Spinner'

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

const variants = {
  primary:   'bg-blue-600 text-white hover:bg-blue-700 shadow-sm focus:ring-blue-500',
  secondary: 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 hover:border-gray-300 focus:ring-gray-300',
  danger:    'bg-red-600 text-white hover:bg-red-700 shadow-sm focus:ring-red-500',
  ghost:     'text-gray-600 hover:bg-gray-100 hover:text-gray-800 focus:ring-gray-300',
}

const sizes = {
  sm: 'px-3 py-1.5 text-[13px]',
  md: 'px-4 py-2 text-[13px]',
  lg: 'px-5 py-2.5 text-sm',
}

export function Button({ variant = 'primary', size = 'md', loading, disabled, children, className, ...props }: Props) {
  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center gap-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  )
}
