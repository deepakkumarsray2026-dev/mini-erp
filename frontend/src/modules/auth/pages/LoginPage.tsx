import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Briefcase, Users, BarChart3, ShieldCheck, Zap } from 'lucide-react'
import { authService } from '../../../services/auth.service'
import { useStore } from '../../../store'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'

interface FormData {
  username: string
  password: string
}

const features = [
  { icon: <Users className="h-4 w-4" />, text: 'Workforce & payroll management' },
  { icon: <BarChart3 className="h-4 w-4" />, text: 'Real-time financial insights' },
  { icon: <Zap className="h-4 w-4" />, text: 'AI-powered anomaly detection' },
  { icon: <ShieldCheck className="h-4 w-4" />, text: 'Role-based access control' },
]

export default function LoginPage() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { setAuthenticated, setUser } = useStore()
  const navigate = useNavigate()

  const onSubmit = async (data: FormData) => {
    setError('')
    setLoading(true)
    try {
      const tokens = await authService.login(data)
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      setAuthenticated(true)
      const user = await authService.me()
      setUser(user)
      navigate('/dashboard')
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      let msg: string
      if (Array.isArray(detail)) {
        msg = detail.map((d: { msg?: string }) => d.msg ?? String(d)).join('; ')
      } else if (typeof detail === 'string') {
        msg = detail
      } else {
        msg = 'Invalid username or password.'
      }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left panel — brand */}
      <div
        className="hidden lg:flex lg:w-5/12 flex-col justify-between p-12 text-white"
        style={{ background: 'linear-gradient(160deg, #0057AE 0%, #1C2B4A 100%)' }}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20">
            <Briefcase className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight">Mini ERP</span>
        </div>

        <div>
          <h2 className="text-4xl font-bold leading-tight">
            Your enterprise.<br />Unified.
          </h2>
          <p className="mt-4 text-blue-100 text-base leading-relaxed max-w-xs">
            One platform for HR, finance, procurement, and AI-powered insights across your entire organisation.
          </p>
          <ul className="mt-8 space-y-3">
            {features.map((f, i) => (
              <li key={i} className="flex items-center gap-3 text-sm text-blue-100">
                <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-white/15">
                  {f.icon}
                </span>
                {f.text}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-blue-300">
          &copy; {new Date().getFullYear()} Mini ERP · Portfolio Project
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-1 items-center justify-center bg-[#F0F2F5] px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="mb-8 flex flex-col items-center lg:hidden">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl mb-3" style={{ backgroundColor: '#0057AE' }}>
              <Briefcase className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl font-bold" style={{ color: '#111827' }}>Mini ERP</h1>
          </div>

          <div className="mb-8">
            <h3 className="text-2xl font-bold" style={{ color: '#111827' }}>Sign in</h3>
            <p className="mt-1 text-sm" style={{ color: '#6B7280' }}>Enter your credentials to access your account</p>
          </div>

          <div
            className="rounded-2xl p-8"
            style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E6EA', boxShadow: '0 4px 16px rgba(0,0,0,0.08)' }}
          >
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {error && <Alert type="error" message={error} />}

              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: '#374151' }}>
                  Username
                </label>
                <input
                  {...register('username', { required: 'Username is required' })}
                  className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all"
                  style={{ borderColor: '#D1D5DB', color: '#111827' }}
                  onFocus={e => (e.currentTarget.style.borderColor = '#0057AE')}
                  onBlur={e => (e.currentTarget.style.borderColor = '#D1D5DB')}
                  placeholder="admin"
                  autoComplete="username"
                />
                {errors.username && <p className="mt-1.5 text-xs text-red-500">{errors.username.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: '#374151' }}>
                  Password
                </label>
                <input
                  {...register('password', { required: 'Password is required' })}
                  type="password"
                  className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all"
                  style={{ borderColor: '#D1D5DB', color: '#111827' }}
                  onFocus={e => (e.currentTarget.style.borderColor = '#0057AE')}
                  onBlur={e => (e.currentTarget.style.borderColor = '#D1D5DB')}
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                {errors.password && <p className="mt-1.5 text-xs text-red-500">{errors.password.message}</p>}
              </div>

              <Button type="submit" loading={loading} size="lg" className="w-full justify-center mt-1">
                Sign in
              </Button>
            </form>
          </div>

          <p className="mt-6 text-center text-xs" style={{ color: '#9CA3AF' }}>
            Mini ERP · Portfolio Project
          </p>
        </div>
      </div>
    </div>
  )
}
