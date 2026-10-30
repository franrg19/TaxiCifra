import { STATUS_LABELS } from '../api/tickets'
import type { TicketStatus } from '../types/api'

const STATUS_STYLES: Record<TicketStatus, string> = {
  pending_review: 'bg-amber-100 text-amber-800',
  confirmed: 'bg-green-100 text-green-800',
}

/** Etiqueta de color con el estado del ticket. */
export function TicketStatusBadge({ status }: { status: TicketStatus }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}
