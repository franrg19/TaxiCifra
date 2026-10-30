import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { errorMessage } from '../api/client'
import {
  confirmTicket,
  deleteTicket,
  getTicket,
  updateTicket,
} from '../api/tickets'
import { listVehicles } from '../api/vehicles'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ErrorMessage } from '../components/ErrorMessage'
import { TicketForm } from '../components/TicketForm'
import { TicketImage } from '../components/TicketImage'
import { TicketStatusBadge } from '../components/TicketStatusBadge'
import type { Ticket, TicketInput, Vehicle } from '../types/api'

/** Pantalla donde el usuario revisa los datos de un ticket junto a su foto. */
export function TicketReviewPage() {
  const ticketId = Number(useParams().ticketId)
  const navigate = useNavigate()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [error, setError] = useState<string | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    getTicket(ticketId)
      .then(setTicket)
      .catch((err: unknown) => setError(errorMessage(err)))
    listVehicles()
      .then(setVehicles)
      .catch(() => setVehicles([]))
  }, [ticketId])

  async function handleSave(data: TicketInput) {
    setTicket(await updateTicket(ticketId, data))
  }

  async function handleConfirm(data: TicketInput) {
    // Primero se guardan los cambios y después se valida: si la confirmación
    // falla, las correcciones ya están a salvo y el ticket sigue pendiente
    setTicket(await updateTicket(ticketId, data))
    await confirmTicket(ticketId)
    navigate('/tickets')
  }

  async function handleDelete() {
    setDeleting(true)
    try {
      await deleteTicket(ticketId)
      navigate('/tickets')
    } catch (err) {
      setError(errorMessage(err))
      setDeleting(false)
      setConfirmingDelete(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link
            to="/tickets"
            className="text-sm font-medium text-amber-700 hover:underline"
          >
            ← Volver a tickets
          </Link>
          <h1 className="text-2xl font-semibold">Revisar ticket</h1>
        </div>
        {ticket && (
          <div className="flex items-center gap-3">
            <TicketStatusBadge status={ticket.status} />
            <Button
              variant="secondary"
              onClick={() => setConfirmingDelete(true)}
            >
              Eliminar
            </Button>
          </div>
        )}
      </div>

      <ErrorMessage message={error} />

      {ticket === null && !error && <p className="text-slate-600">Cargando…</p>}

      {ticket && (
        <>
          {ticket.status === 'confirmed' && (
            <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
              Este ticket ya está confirmado. Si lo modificas, volverá a
              pendiente de revisión hasta que lo confirmes de nuevo.
            </p>
          )}
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-lg bg-white p-4 shadow">
              <TicketImage ticketId={ticket.id} />
            </section>
            <section className="rounded-lg bg-white p-4 shadow">
              <p className="mb-4 text-sm text-slate-600">
                Comprueba los datos antes de confirmar. Solo los tickets
                confirmados cuentan como gasto.
              </p>
              <TicketForm
                ticket={ticket}
                vehicles={vehicles}
                onSave={handleSave}
                onConfirm={handleConfirm}
              />
            </section>
          </div>
        </>
      )}

      {confirmingDelete && (
        <ConfirmDialog
          title="Eliminar ticket"
          message="Se eliminarán el ticket y su foto. Esta acción no se puede deshacer."
          confirmLabel="Eliminar"
          busy={deleting}
          onConfirm={() => void handleDelete()}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
    </div>
  )
}
