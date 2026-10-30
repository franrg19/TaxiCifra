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

/** Una página de resultados de un listado de la API. */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export type TicketCategory =
  | 'combustible'
  | 'mantenimiento'
  | 'seguro'
  | 'limpieza'
  | 'reparaciones'
  | 'emisora'
  | 'autonomo'
  | 'datafono'
  | 'otros'

export type TicketStatus = 'pending_review' | 'confirmed'

export interface TicketInput {
  vehicle_id: number | null
  date: string | null
  vendor: string | null
  category: TicketCategory | null
  // Los importes viajan como texto para no perder precisión
  net_amount: string | null
  vat: string | null
  total: string | null
}

export interface Ticket extends TicketInput {
  id: number
  status: TicketStatus
  created_at: string
}

export interface IncomeInput {
  date: string
  amount: string
  description: string | null
  vehicle_id: number
}

export interface Income extends Omit<IncomeInput, 'vehicle_id'> {
  id: number
  // Queda vacío si el vehículo se borró conservando sus ingresos
  vehicle_id: number | null
  created_at: string
}

export interface OdometerReadingInput {
  date: string
  odometer_km: number
}

export interface OdometerReading extends OdometerReadingInput {
  id: number
  vehicle_id: number
  created_at: string
}
