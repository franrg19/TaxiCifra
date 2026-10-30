import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from '../types/api'
import { apiRequest } from './client'

export function login(data: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function register(data: RegisterRequest): Promise<User> {
  return apiRequest<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
