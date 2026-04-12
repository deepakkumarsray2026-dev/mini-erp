import api from './api'
import type { LoginRequest, TokenResponse, User } from '../types/auth.types'

export const authService = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    const form = new URLSearchParams()
    form.append('username', data.username)
    form.append('password', data.password)
    const res = await api.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return res.data
  },

  async me(): Promise<User> {
    const res = await api.get<User>('/auth/me')
    return res.data
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },
}
