import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { errorMessage } from '../api/client'
import {
  CATEGORY_LABELS,
  createDraftTicket,
  listTickets,
  uploadTicket,
} from '../api/tickets'
import { listVehicles } from '../api/vehicles'
import { Button } from '../components/Button'
import { ErrorMessage } from '../components/ErrorMessage'
import { Pagination } from '../components/Pagination'
import { TicketFilters } from '../components/TicketFilters'
import { TicketStatusBadge } from '../components/TicketStatusBadge'
import { compressImage } from '../compressImage'
import { formatDate, formatEuros } from '../format'
import type { Page, Ticket, Vehicle } from '../types/api'

/** Resultado de una consulta, junto con la consulta que lo produjo. */
interface LoadedPage {
  query: string
  tickets: Page<Ticket> | null
  error: string | null
}

export function TicketsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [loaded, setLoaded] = useState<LoadedPage | null>(null)
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [uploading, setUploading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  // La URL manda: cualquier cambio de filtros o de página produce una consulta nueva
  const query = searchParams.toString()
  const loading = loaded?.query !== query

  useEffect(() => {
    let outdated = false
    listTickets(query)
      .then((tickets) => {
        if (!outdated) setLoaded({ query, tickets, error: null })
      })
      .catch((err: unknown) => {
        if (!outdated) {
          setLoaded({ query, tickets: null, error: errorMessage(err) })
        }
      })
    // Si cambian los filtros antes de que responda, se ignora esta respuesta
    return () => {
      outdated = true
    }
  }, [query])

  useEffect(() => {
    listVehicles()
      .then(setVehicles)
      .catch(() => setVehicles([]))
  }, [])

  function changeFilter(name: string, value: string) {
    const next = new URLSearchParams(searchParams)
    if (value) {
      next.set(name, value)
    } else {
      next.delete(name)
    }
    // Con otros filtros cambian los resultados: se vuelve a la primera página
    next.delete('page')
    setSearchParams(next)
  }

  function changePage(page: number) {
    const next = new URLSearchParams(searchParams)
    next.set('page', String(page))
    setSearchParams(next)
  }

  async function handleFileChosen(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }
    setActionError(null)
    setUploading(true)
    try {
      const ticket = await uploadTicket(await compressImage(file))
      navigate(`/tickets/${ticket.id}`)
    } catch (err) {
      setActionError(errorMessage(err))
      setUploading(false)
      // Se vacía para poder elegir de nuevo la misma foto
      event.target.value = ''
    }
  }

  async function handleAddManually() {
    setActionError(null)
    try {
      const ticket = await createDraftTicket()
      navigate(`/tickets/${ticket.id}`)
    } catch (err) {
      setActionError(errorMessage(err))
    }
  }

  const plates = new Map(vehicles.map(({ id, plate }) => [id, plate]))
  const tickets = loaded?.tickets ?? null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Tickets</h1>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            disabled={uploading}
            onClick={() => void handleAddManually()}
          >
            Añadir a mano
          </Button>
          <Button
            disabled={uploading}
            onClick={() => fileInput.current?.click()}
          >
            {uploading ? 'Leyendo ticket…' : 'Subir foto'}
          </Button>
          <input
            ref={fileInput}
            type="file"
            accept="image/jpeg,image/png"
            aria-label="Foto del ticket"
            className="hidden"
            onChange={(event) => void handleFileChosen(event)}
          />
        </div>
      </div>

      <ErrorMessage message={actionError} />

      <TicketFilters
        values={searchParams}
        vehicles={vehicles}
        onChange={changeFilter}
        onClear={() => setSearchParams({})}
      />

      <ErrorMessage message={loading ? null : (loaded?.error ?? null)} />

      {loading && tickets === null && (
        <p className="text-slate-600">Cargando…</p>
      )}

      {!loading && tickets?.items.length === 0 && (
        <p className="rounded-lg bg-white p-6 text-slate-600 shadow">
          No hay tickets con estos filtros.
        </p>
      )}

      {tickets !== null && tickets.items.length > 0 && (
        <>
          <ul
            aria-busy={loading}
            className={`divide-y divide-slate-200 rounded-lg bg-white shadow ${loading ? 'opacity-50' : ''}`}
          >
            {tickets.items.map((ticket) => (
              <li key={ticket.id}>
                <Link
                  to={`/tickets/${ticket.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 p-4 hover:bg-slate-50"
                >
                  <div>
                    <p className="font-semibold">
                      {ticket.vendor ?? 'Sin establecimiento'}
                    </p>
                    <p className="text-sm text-slate-600">
                      {ticket.date ? formatDate(ticket.date) : 'Sin fecha'}
                      {' · '}
                      {ticket.category
                        ? CATEGORY_LABELS[ticket.category]
                        : 'Sin categoría'}
                      {ticket.vehicle_id !== null &&
                        plates.has(ticket.vehicle_id) &&
                        ` · ${plates.get(ticket.vehicle_id)}`}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">
                      {ticket.total ? formatEuros(ticket.total) : '—'}
                    </p>
                    <TicketStatusBadge status={ticket.status} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
          <Pagination
            page={tickets.page}
            size={tickets.size}
            total={tickets.total}
            onPageChange={changePage}
          />
        </>
      )}
    </div>
  )
}
