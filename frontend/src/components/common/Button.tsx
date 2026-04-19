import clsx from 'clsx'
import { Spinner } from './Spinner'

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

const sizes = {
  sm: 'px-3 py-1.5 text-[13px]',
  md: 'px-4 py-2 text-[13px]',
  lg: 'px-5 py-2.5 text-sm',
}

const variantStyle: Record<string, React.CSSProperties> = {
  primary:   { backgroundColor: '#0057AE', color: '#FFFFFF', boxShadow: '0 1px 2px rgba(0,0,0,0.08)' },
  secondary: { backgroundColor: '#FFFFFF', color: '#374151', border: '1px solid #D1D5DB' },
  danger:    { backgroundColor: '#DC2626', color: '#FFFFFF', boxShadow: '0 1px 2px rgba(0,0,0,0.08)' },
  ghost:     { color: '#6B7280', backgroundColor: 'transparent' },
}

const hoverStyle: Record<string, Partial<React.CSSProperties>> = {
  primary:   { backgroundColor: '#004A9E' },
  secondary: { backgroundColor: '#F9FAFB', borderColor: '#9CA3AF' },
  danger:    { backgroundColor: '#B91C1C' },
  ghost:     { backgroundColor: '#F3F4F6', color: '#111827' },
}

export function Button({ variant = 'primary', size = 'md', loading, disabled, children, className, style, ...props }: Props) {
  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center gap-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-[#0057AE]/40 disabled:opacity-50 disabled:cursor-not-allowed',
        sizes[size],
        className,
      )}
      style={{ ...variantStyle[variant], ...style }}
      onMouseEnter={e => {
        if (disabled || loading) return
        Object.assign(e.currentTarget.style, hoverStyle[variant])
      }}
      onMouseLeave={e => {
        Object.assign(e.currentTarget.style, variantStyle[variant])
      }}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  )
}
