import type {
  Page,
  Ticket,
  TicketCategory,
  TicketInput,
  TicketStatus,
} from '../types/api'
import { apiBlob, apiRequest } from './client'

export const CATEGORY_LABELS: Record<TicketCategory, string> = {
  combustible: 'Combustible',
  mantenimiento: 'Mantenimiento',
  seguro: 'Seguro',
  limpieza: 'Limpieza',
  reparaciones: 'Reparaciones',
  emisora: 'Emisora',
  autonomo: 'Autónomo',
  datafono: 'Datáfono',
  otros: 'Otros',
}

export const STATUS_LABELS: Record<TicketStatus, string> = {
  pending_review: 'Pendiente de revisión',
  confirmed: 'Confirmado',
}

/** Lista tickets. Los filtros y la página usan los mismos nombres que la API. */
export function listTickets(query: string): Promise<Page<Ticket>> {
  return apiRequest<Page<Ticket>>(`/tickets?${query}`)
}

export function getTicket(id: number): Promise<Ticket> {
  return apiRequest<Ticket>(`/tickets/${id}`)
}

/** Crea un borrador vacío, que el usuario rellena en la pantalla de revisión. */
export function createDraftTicket(): Promise<Ticket> {
  return apiRequest<Ticket>('/tickets', {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

/** Sube la foto: la API la guarda, la lee con el OCR y devuelve el ticket pendiente. */
export function uploadTicket(image: File): Promise<Ticket> {
  const body = new FormData()
  body.append('image', image)
  return apiRequest<Ticket>('/tickets/upload', { method: 'POST', body })
}

/** Reemplaza los datos del ticket. La API lo deja siempre pendiente de revisión. */
export function updateTicket(id: number, data: TicketInput): Promise<Ticket> {
  return apiRequest<Ticket>(`/tickets/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function confirmTicket(id: number): Promise<Ticket> {
  return apiRequest<Ticket>(`/tickets/${id}/confirm`, { method: 'POST' })
}

export function deleteTicket(id: number): Promise<void> {
  return apiRequest<void>(`/tickets/${id}`, { method: 'DELETE' })
}

export function getTicketImage(id: number): Promise<Blob> {
  return apiBlob(`/tickets/${id}/image`)
}
