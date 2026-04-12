export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: string
  username: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  roles: Role[]
  created_at: string
}

export interface Role {
  id: string
  name: string
  description: string
}
