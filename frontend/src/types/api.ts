/** Formato uniforme de los errores de la API. */
export interface ApiErrorBody {
  detail: string
  code: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: number
  name: string
  email: string
  created_at: string
}

export interface VehicleInput {
  plate: string
  brand: string
  model: string
}

export interface Vehicle extends VehicleInput {
  id: number
  created_at: string
}
