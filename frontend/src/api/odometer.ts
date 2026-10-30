import type { OdometerReading, OdometerReadingInput, Page } from '../types/api'
import { apiRequest } from './client'

export function listReadings(
  vehicleId: number,
  page: number,
): Promise<Page<OdometerReading>> {
  return apiRequest<Page<OdometerReading>>(
    `/vehicles/${vehicleId}/odometer?page=${page}`,
  )
}

export function createReading(
  vehicleId: number,
  data: OdometerReadingInput,
): Promise<OdometerReading> {
  return apiRequest<OdometerReading>(`/vehicles/${vehicleId}/odometer`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteReading(
  vehicleId: number,
  readingId: number,
): Promise<void> {
  return apiRequest<void>(`/vehicles/${vehicleId}/odometer/${readingId}`, {
    method: 'DELETE',
  })
}
