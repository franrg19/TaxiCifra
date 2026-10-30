import { useState, type FormEvent } from 'react'
import { errorMessage } from '../api/client'
import type { Vehicle, VehicleInput } from '../types/api'
import { Button } from './Button'
import { ErrorMessage } from './ErrorMessage'
import { FormField } from './FormField'

interface VehicleFormProps {
  /** Vehículo a editar; sin él, el formulario da de alta uno nuevo. */
  vehicle?: Vehicle
  onSubmit: (data: VehicleInput) => Promise<void>
  onCancel: () => void
}

/** Formulario de alta y edición de un vehículo. */
export function VehicleForm({ vehicle, onSubmit, onCancel }: VehicleFormProps) {
  const [plate, setPlate] = useState(vehicle?.plate ?? '')
  const [brand, setBrand] = useState(vehicle?.brand ?? '')
  const [model, setModel] = useState(vehicle?.model ?? '')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await onSubmit({ plate, brand, model })
    } catch (err) {
      setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-lg bg-white p-6 shadow"
    >
      <h2 className="text-lg font-semibold">
        {vehicle ? 'Editar vehículo' : 'Nuevo vehículo'}
      </h2>
      <ErrorMessage message={error} />
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField
          id="plate"
          label="Matrícula"
          required
          maxLength={15}
          value={plate}
          onChange={(event) => setPlate(event.target.value)}
        />
        <FormField
          id="brand"
          label="Marca"
          required
          maxLength={50}
          value={brand}
          onChange={(event) => setBrand(event.target.value)}
        />
        <FormField
          id="model"
          label="Modelo"
          required
          maxLength={50}
          value={model}
          onChange={(event) => setModel(event.target.value)}
        />
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="secondary" disabled={submitting} onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Guardando…' : 'Guardar'}
        </Button>
      </div>
    </form>
  )
}
