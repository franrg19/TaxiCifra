import type { Vehicle, VehicleInput } from '../types/api'
import { apiRequest } from './client'

export function listVehicles(): Promise<Vehicle[]> {
  return apiRequest<Vehicle[]>('/vehicles')
}

export function createVehicle(data: VehicleInput): Promise<Vehicle> {
  return apiRequest<Vehicle>('/vehicles', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateVehicle(
  id: number,
  data: VehicleInput,
): Promise<Vehicle> {
  return apiRequest<Vehicle>(`/vehicles/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

/** Con force se borra aunque tenga datos asociados (la API responde 409 si no se indica). */
export function deleteVehicle(id: number, force = false): Promise<void> {
  const query = force ? '?force=true' : ''
  return apiRequest<void>(`/vehicles/${id}${query}`, { method: 'DELETE' })
}
