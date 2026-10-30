import { useState, type FormEvent } from 'react'
import { errorMessage } from '../api/client'
import { CATEGORY_LABELS } from '../api/tickets'
import { AMOUNT_PATTERN, amountToInput, inputToAmount } from '../format'
import type { Ticket, TicketCategory, TicketInput, Vehicle } from '../types/api'
import { Button } from './Button'
import { ErrorMessage } from './ErrorMessage'
import { FormField } from './FormField'
import { SelectField } from './SelectField'

interface TicketFormProps {
  ticket: Ticket
  vehicles: Vehicle[]
  onSave: (data: TicketInput) => Promise<void>
  onConfirm: (data: TicketInput) => Promise<void>
}

/** Formulario de revisión: el usuario corrige lo que ha leído el OCR y lo confirma. */
export function TicketForm({
  ticket,
  vehicles,
  onSave,
  onConfirm,
}: TicketFormProps) {
  // Los campos se guardan como texto, tal como se escriben; se convierten al enviar
  const [date, setDate] = useState(ticket.date ?? '')
  const [vendor, setVendor] = useState(ticket.vendor ?? '')
  const [category, setCategory] = useState(ticket.category ?? '')
  const [netAmount, setNetAmount] = useState(amountToInput(ticket.net_amount))
  const [vat, setVat] = useState(amountToInput(ticket.vat))
  const [total, setTotal] = useState(amountToInput(ticket.total))
  // null = el usuario aún no ha tocado el desplegable
  const [chosenVehicle, setChosenVehicle] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [saved, setSaved] = useState(false)

  // Con un solo vehículo se propone en los tickets pendientes. Es solo una sugerencia:
  // el vehículo es opcional y elegir "Sin vehículo" se respeta
  const suggested =
    ticket.status === 'pending_review' && vehicles.length === 1
      ? String(vehicles[0].id)
      : ''
  const vehicleId =
    chosenVehicle ?? (String(ticket.vehicle_id ?? '') || suggested)

  function toInput(): TicketInput {
    return {
      date: date || null,
      vendor: vendor.trim() || null,
      category: (category || null) as TicketCategory | null,
      net_amount: inputToAmount(netAmount),
      vat: inputToAmount(vat),
      total: inputToAmount(total),
      vehicle_id: vehicleId ? Number(vehicleId) : null,
    }
  }

  async function submit(action: (data: TicketInput) => Promise<void>) {
    setError(null)
    setSaved(false)
    setSubmitting(true)
    try {
      await action(toInput())
      setSaved(true)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submit(onConfirm)
  }

  function handleSave(event: { currentTarget: HTMLButtonElement }) {
    // Guardar sin confirmar también debe respetar el formato de los importes
    if (event.currentTarget.form?.reportValidity()) {
      void submit(onSave)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorMessage message={error} />
      {saved && (
        <p role="status" className="text-sm text-green-700">
          Cambios guardados.
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          id="date"
          label="Fecha"
          type="date"
          value={date}
          onChange={(event) => setDate(event.target.value)}
        />
        <FormField
          id="vendor"
          label="Establecimiento"
          maxLength={100}
          value={vendor}
          onChange={(event) => setVendor(event.target.value)}
        />
        <SelectField
          id="category"
          label="Categoría"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        >
          <option value="">Sin categoría</option>
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </SelectField>
        <SelectField
          id="vehicle"
          label="Vehículo"
          value={vehicleId}
          onChange={(event) => setChosenVehicle(event.target.value)}
        >
          <option value="">Sin vehículo</option>
          {vehicles.map((vehicle) => (
            <option key={vehicle.id} value={vehicle.id}>
              {vehicle.plate}
            </option>
          ))}
        </SelectField>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField
          id="net_amount"
          label="Base imponible (€)"
          inputMode="decimal"
          pattern={AMOUNT_PATTERN}
          title="Importe con dos decimales como máximo, por ejemplo 41,32"
          value={netAmount}
          onChange={(event) => setNetAmount(event.target.value)}
        />
        <FormField
          id="vat"
          label="IVA (€)"
          inputMode="decimal"
          pattern={AMOUNT_PATTERN}
          title="Importe con dos decimales como máximo, por ejemplo 8,68"
          value={vat}
          onChange={(event) => setVat(event.target.value)}
        />
        <FormField
          id="total"
          label="Total (€)"
          inputMode="decimal"
          pattern={AMOUNT_PATTERN}
          title="Importe con dos decimales como máximo, por ejemplo 50,00"
          value={total}
          onChange={(event) => setTotal(event.target.value)}
        />
      </div>
      <div className="flex flex-wrap justify-end gap-2">
        <Button variant="secondary" disabled={submitting} onClick={handleSave}>
          Guardar sin confirmar
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Guardando…' : 'Guardar y confirmar'}
        </Button>
      </div>
    </form>
  )
}
