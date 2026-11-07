import { useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { errorMessage } from '../api/client'
import { PAYMENT_METHOD_LABELS } from '../api/incomes'
import { AMOUNT_PATTERN, amountToInput, inputToAmount, today } from '../format'
import type { Income, IncomeInput, PaymentMethod, Vehicle } from '../types/api'
import { Button } from './Button'
import { ErrorMessage } from './ErrorMessage'
import { FormField } from './FormField'
import { SelectField } from './SelectField'

interface IncomeFormProps {
  /** Ingreso a editar; sin él, el formulario registra uno nuevo. */
  income?: Income
  vehicles: Vehicle[]
  onSubmit: (data: IncomeInput) => Promise<void>
  onCancel: () => void
}

/** Formulario de alta y edición de un ingreso. */
export function IncomeForm({
  income,
  vehicles,
  onSubmit,
  onCancel,
}: IncomeFormProps) {
  // Lo habitual es apuntar la recaudación del día: la fecha viene rellena con hoy
  const [date, setDate] = useState(income?.date ?? today())
  const [amount, setAmount] = useState(amountToInput(income?.amount ?? null))
  // Sin valor inicial: el usuario la elige siempre (los ingresos antiguos no la tienen)
  const [paymentMethod, setPaymentMethod] = useState(
    income?.payment_method ?? '',
  )
  const [description, setDescription] = useState(income?.description ?? '')
  const [chosenVehicle, setChosenVehicle] = useState(
    String(income?.vehicle_id ?? ''),
  )
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Con un solo vehículo no hay nada que elegir: se preselecciona
  const onlyVehicle = vehicles.length === 1 ? String(vehicles[0].id) : ''
  const vehicleId = chosenVehicle || onlyVehicle

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await onSubmit({
        date,
        amount: inputToAmount(amount) ?? '',
        // El desplegable es obligatorio: al enviar ya no puede estar vacío
        payment_method: paymentMethod as PaymentMethod,
        description: description.trim() || null,
        vehicle_id: Number(vehicleId),
      })
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
        {income ? 'Editar ingreso' : 'Nuevo ingreso'}
      </h2>
      <ErrorMessage message={error} />
      {vehicles.length === 0 && (
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Para registrar un ingreso necesitas un vehículo.{' '}
          <Link to="/vehicles" className="font-medium underline">
            Añade el primero
          </Link>
          .
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <FormField
          id="date"
          label="Fecha"
          type="date"
          required
          value={date}
          onChange={(event) => setDate(event.target.value)}
        />
        <FormField
          id="amount"
          label="Importe (€)"
          inputMode="decimal"
          required
          pattern={AMOUNT_PATTERN}
          title="Importe con dos decimales como máximo, por ejemplo 185,50"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
        />
        <SelectField
          id="payment_method"
          label="Forma de pago"
          required
          value={paymentMethod}
          onChange={(event) => setPaymentMethod(event.target.value)}
        >
          <option value="">Elige una forma de pago</option>
          {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </SelectField>
        <SelectField
          id="vehicle"
          label="Vehículo"
          required
          value={vehicleId}
          onChange={(event) => setChosenVehicle(event.target.value)}
        >
          <option value="">Elige un vehículo</option>
          {vehicles.map((vehicle) => (
            <option key={vehicle.id} value={vehicle.id}>
              {vehicle.plate}
            </option>
          ))}
        </SelectField>
      </div>
      <FormField
        id="description"
        label="Descripción (opcional)"
        maxLength={255}
        value={description}
        onChange={(event) => setDescription(event.target.value)}
      />
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
