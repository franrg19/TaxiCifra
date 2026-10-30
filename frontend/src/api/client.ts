import type { ApiErrorBody } from '../types/api'

const API_PREFIX = '/api/v1'
const TOKEN_KEY = 'taxicifra_token'

// Nombre en pantalla de los campos que aparecen en los errores de validación ("campo: motivo")
const FIELD_LABELS: Record<string, string> = {
  name: 'Nombre',
  email: 'Email',
  password: 'Contraseña',
  plate: 'Matrícula',
  brand: 'Marca',
  model: 'Modelo',
  page: 'Página',
  date_from: 'Desde',
  date_to: 'Hasta',
  category: 'Categoría',
  status: 'Estado',
  vehicle_id: 'Vehículo',
  date: 'Fecha',
  vendor: 'Establecimiento',
  net_amount: 'Base imponible',
  vat: 'IVA',
  total: 'Total',
  amount: 'Importe',
  description: 'Descripción',
  odometer_km: 'Kilómetros',
}

/** Error devuelto por la API, con su mensaje en español y su código. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, body: ApiErrorBody) {
    super(translateFields(body.detail))
    this.status = status
    this.code = body.code
  }
}

/** El token JWT se guarda en localStorage: sobrevive a recargas durante sus 24 horas. */
export const tokenStorage = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string): void => localStorage.setItem(TOKEN_KEY, token),
  clear: (): void => localStorage.removeItem(TOKEN_KEY),
}

let onUnauthorized: () => void = () => {}

/** Registra qué hacer cuando la API rechaza el token (caducado o no válido). */
export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler
}

/** Hace una petición a la API y devuelve la respuesta ya convertida desde JSON. */
export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await send(path, init)
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

/** Descarga un fichero protegido. Un <img src> no podría, porque no envía el token. */
export async function apiBlob(path: string): Promise<Blob> {
  const response = await send(path)
  return response.blob()
}

/** Envía la petición con el token y convierte las respuestas de error en ApiError. */
async function send(path: string, init: RequestInit = {}): Promise<Response> {
  const token = tokenStorage.get()
  const headers = new Headers(init.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (typeof init.body === 'string') {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_PREFIX}${path}`, { ...init, headers })

  if (!response.ok) {
    if (response.status === 401 && token) {
      // El token ya no sirve: se cierra la sesión y la app vuelve al login
      tokenStorage.clear()
      onUnauthorized()
    }
    throw new ApiError(response.status, await readErrorBody(response))
  }
  return response
}

async function readErrorBody(response: Response): Promise<ApiErrorBody> {
  try {
    return (await response.json()) as ApiErrorBody
  } catch {
    return {
      detail: 'No se ha podido conectar con el servidor',
      code: 'network_error',
    }
  }
}

/** Cambia "password: debe tener..." por "Contraseña: debe tener...". */
function translateFields(detail: string): string {
  return detail
    .split('; ')
    .map((part) => {
      const [field, ...reason] = part.split(': ')
      const label = FIELD_LABELS[field]
      return label && reason.length > 0
        ? `${label}: ${reason.join(': ')}`
        : part
    })
    .join('; ')
}

/** Mensaje para el usuario a partir de cualquier error de una petición. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  // fetch lanza TypeError si no llega al servidor (sin red o backend apagado)
  return 'No se ha podido conectar con el servidor'
}
