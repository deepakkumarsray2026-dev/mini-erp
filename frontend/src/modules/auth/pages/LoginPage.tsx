import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Briefcase } from 'lucide-react'
import { authService } from '../../../services/auth.service'
import { useStore } from '../../../store'
import { Spinner } from '../../../components/common/Spinner'

interface FormData {
  username: string
  password: string
}

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
    <div
      className="flex min-h-screen flex-col items-center justify-center px-4 py-16"
      style={{ backgroundColor: '#131314' }}
    >
      {/* Logo mark */}
      <div className="mb-10 flex flex-col items-center gap-4">
        <div
          className="flex h-11 w-11 items-center justify-center rounded-xl"
          style={{ backgroundColor: '#d97757' }}
        >
          <Briefcase className="h-5 w-5 text-white" />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-semibold tracking-tight" style={{ color: '#f0ece3' }}>
            Mini ERP
          </h1>
          <p className="mt-1 text-sm" style={{ color: '#6b6b6b' }}>
            Sign in to your workspace
          </p>
        </div>
      </div>

      {/* Card */}
      <div
        className="w-full max-w-sm rounded-2xl p-8"
        style={{ backgroundColor: '#1c1c1e', border: '1px solid #2a2a2e' }}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

          {/* Error banner */}
          {error && (
            <div
              className="rounded-lg px-4 py-3 text-sm"
              style={{ backgroundColor: '#2a1a1a', border: '1px solid #4a2020', color: '#df9090' }}
            >
              {error}
            </div>
          )}

          {/* Username */}
          <div>
            <label
              className="block text-sm font-medium mb-1.5"
              style={{ color: '#c4c0b8' }}
            >
              Username
            </label>
            <input
              {...register('username', { required: 'Username is required' })}
              className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
              style={{
                backgroundColor: '#111113',
                border: '1px solid #2e2e32',
                color: '#f0ece3',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = '#d97757')}
              onBlur={e => (e.currentTarget.style.borderColor = '#2e2e32')}
              placeholder="admin"
              autoComplete="username"
            />
            {errors.username && (
              <p className="mt-1.5 text-xs" style={{ color: '#df9090' }}>
                {errors.username.message}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <label
              className="block text-sm font-medium mb-1.5"
              style={{ color: '#c4c0b8' }}
            >
              Password
            </label>
            <input
              {...register('password', { required: 'Password is required' })}
              type="password"
              className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
              style={{
                backgroundColor: '#111113',
                border: '1px solid #2e2e32',
                color: '#f0ece3',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = '#d97757')}
              onBlur={e => (e.currentTarget.style.borderColor = '#2e2e32')}
              placeholder="••••••••"
              autoComplete="current-password"
            />
            {errors.password && (
              <p className="mt-1.5 text-xs" style={{ color: '#df9090' }}>
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="mt-1 w-full rounded-lg py-2.5 text-sm font-medium transition-opacity disabled:opacity-60"
            style={{ backgroundColor: '#d97757', color: '#fff' }}
            onMouseEnter={e => !loading && (e.currentTarget.style.opacity = '0.88')}
            onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <Spinner size="sm" /> Signing in…
              </span>
            ) : (
              'Sign in'
            )}
          </button>
        </form>
      </div>

      <p className="mt-8 text-xs" style={{ color: '#3a3a3e' }}>
        &copy; {new Date().getFullYear()} Mini ERP · Portfolio Project
      </p>
    </div>
  )
}
