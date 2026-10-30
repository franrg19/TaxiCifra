import { useState, type FormEvent } from 'react'
import { errorMessage } from '../api/client'
import { today } from '../format'
import type { OdometerReadingInput } from '../types/api'
import { Button } from './Button'
import { ErrorMessage } from './ErrorMessage'
import { FormField } from './FormField'

interface OdometerFormProps {
  onSubmit: (data: OdometerReadingInput) => Promise<void>
}

/** Formulario para registrar una lectura del cuentakilómetros. */
export function OdometerForm({ onSubmit }: OdometerFormProps) {
  const [date, setDate] = useState(today())
  const [km, setKm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await onSubmit({ date, odometer_km: Number(km) })
      // Se vacían los km para apuntar la siguiente lectura; la fecha se mantiene
      setKm('')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-lg bg-white p-4 shadow"
    >
      <h2 className="text-lg font-semibold">Nueva lectura</h2>
      <ErrorMessage message={error} />
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField
          id="date"
          label="Fecha"
          type="date"
          required
          value={date}
          onChange={(event) => setDate(event.target.value)}
        />
        <FormField
          id="odometer_km"
          label="Kilómetros del cuentakilómetros"
          type="number"
          inputMode="numeric"
          required
          min={0}
          max={9999999}
          step={1}
          value={km}
          onChange={(event) => setKm(event.target.value)}
        />
        <div className="flex items-end">
          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? 'Guardando…' : 'Guardar lectura'}
          </Button>
        </div>
      </div>
    </form>
  )
}
