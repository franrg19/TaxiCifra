import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { errorMessage } from '../api/client'
import {
  createIncome,
  deleteIncome,
  listIncomes,
  updateIncome,
} from '../api/incomes'
import { listVehicles } from '../api/vehicles'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ErrorMessage } from '../components/ErrorMessage'
import { IncomeFilters } from '../components/IncomeFilters'
import { IncomeForm } from '../components/IncomeForm'
import { Pagination } from '../components/Pagination'
import { formatDate, formatEuros } from '../format'
import type { Income, IncomeInput, Page, Vehicle } from '../types/api'

/** Resultado de una consulta, junto con la consulta que lo produjo. */
interface LoadedPage {
  query: string
  incomes: Page<Income> | null
  error: string | null
}

/** Qué formulario está abierto: ninguno, el de alta o el de edición de un ingreso. */
type FormState =
  { mode: 'closed' } | { mode: 'create' } | { mode: 'edit'; income: Income }

export function IncomesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [loaded, setLoaded] = useState<LoadedPage | null>(null)
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [form, setForm] = useState<FormState>({ mode: 'closed' })
  const [pendingDelete, setPendingDelete] = useState<Income | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  // La URL manda: cualquier cambio de filtros o de página produce una consulta nueva
  const query = searchParams.toString()
  const loading = loaded?.query !== query

  useEffect(() => {
    let outdated = false
    listIncomes(query)
      .then((incomes) => {
        if (!outdated) setLoaded({ query, incomes, error: null })
      })
      .catch((err: unknown) => {
        if (!outdated) {
          setLoaded({ query, incomes: null, error: errorMessage(err) })
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

  async function reload() {
    setLoaded({ query, incomes: await listIncomes(query), error: null })
  }

  async function handleSubmit(data: IncomeInput) {
    if (form.mode === 'edit') {
      await updateIncome(form.income.id, data)
    } else {
      await createIncome(data)
    }
    await reload()
    setForm({ mode: 'closed' })
  }

  async function handleDelete(income: Income) {
    setDeleting(true)
    setActionError(null)
    try {
      await deleteIncome(income.id)
      setPendingDelete(null)
      const current = loaded?.incomes
      if (current && current.items.length === 1 && current.page > 1) {
        // Era el último de la página: se pasa a la anterior para no dejarla vacía
        changePage(current.page - 1)
      } else {
        await reload()
      }
    } catch (err) {
      setActionError(errorMessage(err))
      setPendingDelete(null)
    } finally {
      setDeleting(false)
    }
  }

  const plates = new Map(vehicles.map(({ id, plate }) => [id, plate]))
  const incomes = loaded?.incomes ?? null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Ingresos</h1>
        {form.mode === 'closed' && (
          <Button onClick={() => setForm({ mode: 'create' })}>
            Nuevo ingreso
          </Button>
        )}
      </div>

      <ErrorMessage message={actionError} />

      {form.mode !== 'closed' && (
        <IncomeForm
          // Con otra key, React crea el formulario de nuevo con los datos del ingreso elegido
          key={form.mode === 'edit' ? form.income.id : 'new'}
          income={form.mode === 'edit' ? form.income : undefined}
          vehicles={vehicles}
          onSubmit={handleSubmit}
          onCancel={() => setForm({ mode: 'closed' })}
        />
      )}

      <IncomeFilters
        values={searchParams}
        vehicles={vehicles}
        onChange={changeFilter}
        onClear={() => setSearchParams({})}
      />

      <ErrorMessage message={loading ? null : (loaded?.error ?? null)} />

      {loading && incomes === null && (
        <p className="text-slate-600">Cargando…</p>
      )}

      {!loading && incomes?.items.length === 0 && (
        <p className="rounded-lg bg-white p-6 text-slate-600 shadow">
          No hay ingresos con estos filtros.
        </p>
      )}

      {incomes !== null && incomes.items.length > 0 && (
        <>
          <ul
            aria-busy={loading}
            className={`divide-y divide-slate-200 rounded-lg bg-white shadow ${loading ? 'opacity-50' : ''}`}
          >
            {incomes.items.map((income) => (
              <li
                key={income.id}
                className="flex flex-wrap items-center justify-between gap-3 p-4"
              >
                <div>
                  <p className="font-semibold">{formatEuros(income.amount)}</p>
                  <p className="text-sm text-slate-600">
                    {formatDate(income.date)}
                    {income.vehicle_id !== null &&
                      plates.has(income.vehicle_id) &&
                      ` · ${plates.get(income.vehicle_id)}`}
                    {income.description && ` · ${income.description}`}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => setForm({ mode: 'edit', income })}
                  >
                    Editar
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setPendingDelete(income)}
                  >
                    Eliminar
                  </Button>
                </div>
              </li>
            ))}
          </ul>
          <Pagination
            page={incomes.page}
            size={incomes.size}
            total={incomes.total}
            onPageChange={changePage}
          />
        </>
      )}

      {pendingDelete && (
        <ConfirmDialog
          title="Eliminar ingreso"
          message={`¿Seguro que quieres eliminar el ingreso de ${formatEuros(pendingDelete.amount)} del ${formatDate(pendingDelete.date)}?`}
          confirmLabel="Eliminar"
          busy={deleting}
          onConfirm={() => void handleDelete(pendingDelete)}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </div>
  )
}
