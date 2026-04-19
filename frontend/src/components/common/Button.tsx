import clsx from 'clsx'
import { Spinner } from './Spinner'

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

const variants = {
  primary:   'text-white',
  secondary: 'font-medium transition-colors',
  danger:    'bg-red-700 text-white hover:bg-red-600 shadow-sm',
  ghost:     'transition-colors',
}

const sizes = {
  sm: 'px-3 py-1.5 text-[13px]',
  md: 'px-4 py-2 text-[13px]',
  lg: 'px-5 py-2.5 text-sm',
}

export function Button({ variant = 'primary', size = 'md', loading, disabled, children, className, style, ...props }: Props) {
  const variantStyle: React.CSSProperties =
    variant === 'primary'
      ? { backgroundColor: '#d97757', boxShadow: '0 1px 3px rgba(0,0,0,.3)' }
      : variant === 'secondary'
      ? { backgroundColor: '#1c1c1e', color: '#c4c0b8', border: '1px solid #2a2a2e' }
      : variant === 'ghost'
      ? { color: '#6b6b6b' }
      : {}

  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center gap-2 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-[#131314] disabled:opacity-50 disabled:cursor-not-allowed',
        variant === 'primary' && 'focus:ring-[#d97757]/40',
        variant === 'secondary' && 'focus:ring-[#2a2a2e]',
        variant === 'ghost' && 'focus:ring-[#2a2a2e]',
        variants[variant],
        sizes[size],
        className,
      )}
      style={{ ...variantStyle, ...style }}
      onMouseEnter={e => {
        if (disabled || loading) return
        if (variant === 'primary') e.currentTarget.style.opacity = '0.88'
        if (variant === 'secondary') e.currentTarget.style.backgroundColor = '#222224'
        if (variant === 'ghost') {
          e.currentTarget.style.backgroundColor = '#222224'
          e.currentTarget.style.color = '#f0ece3'
        }
      }}
      onMouseLeave={e => {
        if (variant === 'primary') e.currentTarget.style.opacity = '1'
        if (variant === 'secondary') e.currentTarget.style.backgroundColor = '#1c1c1e'
        if (variant === 'ghost') {
          e.currentTarget.style.backgroundColor = 'transparent'
          e.currentTarget.style.color = '#6b6b6b'
        }
      }}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  )
}
