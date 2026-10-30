import type { Page, Ticket, TicketCategory, TicketStatus } from '../types/api'
import { apiRequest } from './client'

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
