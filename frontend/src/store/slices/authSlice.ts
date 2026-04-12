import type { User } from '../../types/auth.types'

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  setAuthenticated: (val: boolean) => void
  logout: () => void
}

export const createAuthSlice = (set: (fn: (s: AuthState) => Partial<AuthState>) => void): AuthState => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  setUser: (user) => set(() => ({ user })),
  setAuthenticated: (val) => set(() => ({ isAuthenticated: val })),
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set(() => ({ user: null, isAuthenticated: false }))
  },
})
