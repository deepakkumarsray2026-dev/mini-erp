import api from './api'
import type { LoginRequest, TokenResponse, User } from '../types/auth.types'

export const authService = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    const res = await api.post<TokenResponse>('/auth/login', {
      username: data.username,
      password: data.password,
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
