import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { errorMessage } from '../api/client'
import { createReading, deleteReading, listReadings } from '../api/odometer'
import { listVehicles } from '../api/vehicles'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ErrorMessage } from '../components/ErrorMessage'
import { OdometerForm } from '../components/OdometerForm'
import { Pagination } from '../components/Pagination'
import { SelectField } from '../components/SelectField'
import { formatDate, formatKm } from '../format'
import type {
  OdometerReading,
  OdometerReadingInput,
  Page,
  Vehicle,
} from '../types/api'

/** Resultado de una consulta, junto con la consulta que lo produjo. */
interface LoadedPage {
  key: string
  readings: Page<OdometerReading> | null
  error: string | null
}

export function OdometerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [vehicles, setVehicles] = useState<Vehicle[] | null>(null)
  const [vehiclesError, setVehiclesError] = useState<string | null>(null)
  const [loaded, setLoaded] = useState<LoadedPage | null>(null)
  const [pendingDelete, setPendingDelete] = useState<OdometerReading | null>(
    null,
  )
  const [deleting, setDeleting] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    listVehicles()
      .then(setVehicles)
      .catch((err: unknown) => setVehiclesError(errorMessage(err)))
  }, [])

  // El vehículo elegido va en la URL; si no hay ninguno válido, se usa el primero
  const fromUrl = Number(searchParams.get('vehicle_id'))
  const vehicle =
    vehicles?.find(({ id }) => id === fromUrl) ?? vehicles?.[0] ?? null
  const vehicleId = vehicle?.id ?? null
  const page = Number(searchParams.get('page')) || 1
  const key = `${vehicleId}:${page}`
  const loading = vehicleId !== null && loaded?.key !== key

  useEffect(() => {
    if (vehicleId === null) {
      return
    }
    let outdated = false
    listReadings(vehicleId, page)
      .then((readings) => {
        if (!outdated) setLoaded({ key, readings, error: null })
      })
      .catch((err: unknown) => {
        if (!outdated) {
          setLoaded({ key, readings: null, error: errorMessage(err) })
        }
      })
    // Si cambia el vehículo antes de que responda, se ignora esta respuesta
    return () => {
      outdated = true
    }
  }, [key, vehicleId, page])

  async function reload(id: number) {
    setLoaded({ key, readings: await listReadings(id, page), error: null })
  }

  async function handleCreate(data: OdometerReadingInput) {
    if (vehicleId !== null) {
      await createReading(vehicleId, data)
      await reload(vehicleId)
    }
  }

  function changePage(next: number) {
    const params = new URLSearchParams(searchParams)
    params.set('page', String(next))
    setSearchParams(params)
  }

  async function handleDelete(reading: OdometerReading) {
    setDeleting(true)
    setActionError(null)
    try {
      await deleteReading(reading.vehicle_id, reading.id)
      setPendingDelete(null)
      const current = loaded?.readings
      if (current && current.items.length === 1 && current.page > 1) {
        // Era la última de la página: se pasa a la anterior para no dejarla vacía
        changePage(current.page - 1)
      } else {
        await reload(reading.vehicle_id)
      }
    } catch (err) {
      setActionError(errorMessage(err))
      setPendingDelete(null)
    } finally {
      setDeleting(false)
    }
  }

  const readings = loaded?.key === key ? loaded.readings : null
  const loadError = loaded?.key === key ? loaded.error : null

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Kilometraje</h1>

      <ErrorMessage message={vehiclesError ?? actionError} />

      {vehicles?.length === 0 && (
        <p className="rounded-lg bg-white p-6 text-slate-600 shadow">
          Para registrar kilómetros necesitas un vehículo.{' '}
          <Link
            to="/vehicles"
            className="font-medium text-amber-700 hover:underline"
          >
            Añade el primero
          </Link>
          .
        </p>
      )}

      {vehicle && vehicles && (
        <>
          <div className="rounded-lg bg-white p-4 shadow sm:max-w-sm">
            <SelectField
              id="vehicle_id"
              label="Vehículo"
              value={vehicle.id}
              onChange={(event) =>
                // Al cambiar de vehículo se vuelve a la primera página
                setSearchParams({ vehicle_id: event.target.value })
              }
            >
              {vehicles.map(({ id, plate }) => (
                <option key={id} value={id}>
                  {plate}
                </option>
              ))}
            </SelectField>
          </div>

          <OdometerForm key={vehicle.id} onSubmit={handleCreate} />

          <ErrorMessage message={loadError} />

          {loading && <p className="text-slate-600">Cargando…</p>}

          {readings?.items.length === 0 && (
            <p className="rounded-lg bg-white p-6 text-slate-600 shadow">
              Este vehículo todavía no tiene lecturas.
            </p>
          )}

          {readings !== null && readings.items.length > 0 && (
            <>
              <ul className="divide-y divide-slate-200 rounded-lg bg-white shadow">
                {readings.items.map((reading) => (
                  <li
                    key={reading.id}
                    className="flex flex-wrap items-center justify-between gap-3 p-4"
                  >
                    <div>
                      <p className="font-semibold">
                        {formatKm(reading.odometer_km)}
                      </p>
                      <p className="text-sm text-slate-600">
                        {formatDate(reading.date)}
                      </p>
                    </div>
                    <Button
                      variant="secondary"
                      onClick={() => setPendingDelete(reading)}
                    >
                      Eliminar
                    </Button>
                  </li>
                ))}
              </ul>
              <Pagination
                page={readings.page}
                size={readings.size}
                total={readings.total}
                onPageChange={changePage}
              />
            </>
          )}
        </>
      )}

      {pendingDelete && (
        <ConfirmDialog
          title="Eliminar lectura"
          message={`¿Seguro que quieres eliminar la lectura de ${formatKm(pendingDelete.odometer_km)} del ${formatDate(pendingDelete.date)}?`}
          confirmLabel="Eliminar"
          busy={deleting}
          onConfirm={() => void handleDelete(pendingDelete)}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </div>
  )
}
