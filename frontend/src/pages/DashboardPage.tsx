import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { errorMessage } from '../api/client'
import { getByCategory, getMonthly, getSummary } from '../api/dashboard'
import { listVehicles } from '../api/vehicles'
import { Button } from '../components/Button'
import { CategoryChart } from '../components/CategoryChart'
import { ErrorMessage } from '../components/ErrorMessage'
import { FormField } from '../components/FormField'
import { MonthlyChart } from '../components/MonthlyChart'
import { SelectField } from '../components/SelectField'
import { SummaryCards } from '../components/SummaryCards'
import { firstDayOfMonth, today } from '../format'
import type {
  CategoryExpense,
  DashboardSummary,
  MonthlyTotals,
  Vehicle,
} from '../types/api'

/** Cuántos años se ofrecen en la evolución mensual, contando el actual. */
const YEARS_SHOWN = 5

interface PeriodData {
  key: string
  summary: DashboardSummary | null
  categories: CategoryExpense[]
  error: string | null
}

interface YearData {
  key: string
  months: MonthlyTotals[] | null
}

/** Quita los filtros vacíos: un campo de fecha en blanco significa "sin límite". */
function toQuery(filters: Record<string, string>): string {
  const entries = Object.entries(filters).filter(([, value]) => value)
  return new URLSearchParams(entries).toString()
}

export function DashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [period, setPeriod] = useState<PeriodData | null>(null)
  const [year, setYear] = useState<YearData | null>(null)

  // Sin nada en la URL se muestra el mes en curso
  const dateFrom = searchParams.get('date_from') ?? firstDayOfMonth()
  const dateTo = searchParams.get('date_to') ?? today()
  const vehicleId = searchParams.get('vehicle_id') ?? ''
  const currentYear = Number(today().slice(0, 4))
  const selectedYear = searchParams.get('year') ?? String(currentYear)

  const periodQuery = toQuery({
    date_from: dateFrom,
    date_to: dateTo,
    vehicle_id: vehicleId,
  })
  const yearQuery = toQuery({ year: selectedYear, vehicle_id: vehicleId })

  useEffect(() => {
    let outdated = false
    Promise.all([getSummary(periodQuery), getByCategory(periodQuery)])
      .then(([summary, categories]) => {
        if (!outdated) {
          setPeriod({ key: periodQuery, summary, categories, error: null })
        }
      })
      .catch((err: unknown) => {
        if (!outdated) {
          setPeriod({
            key: periodQuery,
            summary: null,
            categories: [],
            error: errorMessage(err),
          })
        }
      })
    return () => {
      outdated = true
    }
  }, [periodQuery])

  useEffect(() => {
    let outdated = false
    getMonthly(yearQuery)
      .then((months) => {
        if (!outdated) setYear({ key: yearQuery, months })
      })
      .catch(() => {
        if (!outdated) setYear({ key: yearQuery, months: null })
      })
    return () => {
      outdated = true
    }
  }, [yearQuery])

  useEffect(() => {
    listVehicles()
      .then(setVehicles)
      .catch(() => setVehicles([]))
  }, [])

  function changeFilter(name: string, value: string) {
    const next = new URLSearchParams(searchParams)
    next.set(name, value)
    setSearchParams(next)
  }

  const years = Array.from(
    { length: YEARS_SHOWN },
    (_, index) => currentYear - index,
  )

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Resumen</h1>

      <form className="grid gap-4 rounded-lg bg-white p-4 shadow sm:grid-cols-2 lg:grid-cols-4">
        <FormField
          id="date_from"
          label="Desde"
          type="date"
          value={dateFrom}
          onChange={(event) => changeFilter('date_from', event.target.value)}
        />
        <FormField
          id="date_to"
          label="Hasta"
          type="date"
          value={dateTo}
          onChange={(event) => changeFilter('date_to', event.target.value)}
        />
        <SelectField
          id="vehicle_id"
          label="Vehículo"
          value={vehicleId}
          onChange={(event) => changeFilter('vehicle_id', event.target.value)}
        >
          <option value="">Todos</option>
          {vehicles.map(({ id, plate }) => (
            <option key={id} value={id}>
              {plate}
            </option>
          ))}
        </SelectField>
        <div className="flex items-end">
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => setSearchParams({})}
          >
            Este mes
          </Button>
        </div>
      </form>

      <ErrorMessage message={period?.error ?? null} />

      {period?.summary ? (
        <SummaryCards summary={period.summary} />
      ) : (
        !period && <p className="text-slate-600">Cargando…</p>
      )}

      <p className="text-sm text-slate-600">
        Solo cuentan como gasto los tickets confirmados.
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="min-w-0 rounded-lg bg-white p-4 shadow">
          <h2 className="mb-4 text-lg font-semibold">Gasto por categoría</h2>
          {period?.summary && <CategoryChart data={period.categories} />}
        </section>

        <section className="min-w-0 rounded-lg bg-white p-4 shadow">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Evolución mensual</h2>
            <select
              aria-label="Año"
              value={selectedYear}
              onChange={(event) => changeFilter('year', event.target.value)}
              className="rounded-md border border-slate-300 bg-white px-2 py-1"
            >
              {years.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>
          {year?.months ? (
            <MonthlyChart data={year.months} />
          ) : (
            year && (
              <p className="text-slate-600">
                No se ha podido cargar la evolución mensual.
              </p>
            )
          )}
        </section>
      </div>
    </div>
  )
}
