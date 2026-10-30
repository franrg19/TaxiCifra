import { useEffect, useState } from 'react'
import { ApiError, errorMessage } from '../api/client'
import {
  createVehicle,
  deleteVehicle,
  listVehicles,
  updateVehicle,
} from '../api/vehicles'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ErrorMessage } from '../components/ErrorMessage'
import { VehicleForm } from '../components/VehicleForm'
import type { Vehicle, VehicleInput } from '../types/api'

/** Qué formulario está abierto: ninguno, el de alta o el de edición de un vehículo. */
type FormState =
  { mode: 'closed' } | { mode: 'create' } | { mode: 'edit'; vehicle: Vehicle }

/** Borrado pendiente de confirmar. Con relatedData, la API ya avisó de que tiene datos. */
interface PendingDelete {
  vehicle: Vehicle
  relatedData: string | null
}

export function VehiclesPage() {
  const [vehicles, setVehicles] = useState<Vehicle[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>({ mode: 'closed' })
  const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    listVehicles()
      .then(setVehicles)
      .catch((err: unknown) => setError(errorMessage(err)))
  }, [])

  async function handleSubmit(data: VehicleInput) {
    if (form.mode === 'edit') {
      await updateVehicle(form.vehicle.id, data)
    } else {
      await createVehicle(data)
    }
    setVehicles(await listVehicles())
    setForm({ mode: 'closed' })
  }

  async function handleDelete({ vehicle, relatedData }: PendingDelete) {
    setDeleting(true)
    setError(null)
    try {
      // La segunda confirmación, tras el aviso de la API, es la que fuerza el borrado
      await deleteVehicle(vehicle.id, relatedData !== null)
      setPendingDelete(null)
      setVehicles(await listVehicles())
    } catch (err) {
      if (err instanceof ApiError && err.code === 'vehicle_has_related_data') {
        setPendingDelete({ vehicle, relatedData: err.message })
      } else {
        setError(errorMessage(err))
        setPendingDelete(null)
      }
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Vehículos</h1>
        {form.mode === 'closed' && (
          <Button onClick={() => setForm({ mode: 'create' })}>
            Nuevo vehículo
          </Button>
        )}
      </div>

      <ErrorMessage message={error} />

      {form.mode !== 'closed' && (
        <VehicleForm
          // Con otra key, React crea el formulario de nuevo con los datos del vehículo elegido
          key={form.mode === 'edit' ? form.vehicle.id : 'new'}
          vehicle={form.mode === 'edit' ? form.vehicle : undefined}
          onSubmit={handleSubmit}
          onCancel={() => setForm({ mode: 'closed' })}
        />
      )}

      {vehicles === null && !error && (
        <p className="text-slate-600">Cargando…</p>
      )}

      {vehicles?.length === 0 && (
        <p className="rounded-lg bg-white p-6 text-slate-600 shadow">
          Todavía no tienes vehículos. Añade el primero para asociarle tickets,
          ingresos y kilómetros.
        </p>
      )}

      {vehicles !== null && vehicles.length > 0 && (
        <ul className="divide-y divide-slate-200 rounded-lg bg-white shadow">
          {vehicles.map((vehicle) => (
            <li
              key={vehicle.id}
              className="flex flex-wrap items-center justify-between gap-3 p-4"
            >
              <div>
                <p className="font-semibold">{vehicle.plate}</p>
                <p className="text-sm text-slate-600">
                  {vehicle.brand} {vehicle.model}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  onClick={() => setForm({ mode: 'edit', vehicle })}
                >
                  Editar
                </Button>
                <Button
                  variant="secondary"
                  onClick={() =>
                    setPendingDelete({ vehicle, relatedData: null })
                  }
                >
                  Eliminar
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {pendingDelete && (
        <ConfirmDialog
          title={`Eliminar ${pendingDelete.vehicle.plate}`}
          message={
            pendingDelete.relatedData ??
            '¿Seguro que quieres eliminar este vehículo?'
          }
          confirmLabel={
            pendingDelete.relatedData ? 'Eliminar de todos modos' : 'Eliminar'
          }
          busy={deleting}
          onConfirm={() => void handleDelete(pendingDelete)}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </div>
  )
}
