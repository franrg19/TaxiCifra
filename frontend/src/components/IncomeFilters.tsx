import type { Vehicle } from '../types/api'
import { Button } from './Button'
import { FormField } from './FormField'
import { SelectField } from './SelectField'

interface IncomeFiltersProps {
  values: URLSearchParams
  vehicles: Vehicle[]
  onChange: (name: string, value: string) => void
  onClear: () => void
}

/** Filtros del listado de ingresos. Sus valores viven en la URL de la página. */
export function IncomeFilters({
  values,
  vehicles,
  onChange,
  onClear,
}: IncomeFiltersProps) {
  return (
    <form className="grid gap-4 rounded-lg bg-white p-4 shadow sm:grid-cols-2 lg:grid-cols-4">
      <FormField
        id="date_from"
        label="Desde"
        type="date"
        value={values.get('date_from') ?? ''}
        onChange={(event) => onChange('date_from', event.target.value)}
      />
      <FormField
        id="date_to"
        label="Hasta"
        type="date"
        value={values.get('date_to') ?? ''}
        onChange={(event) => onChange('date_to', event.target.value)}
      />
      <SelectField
        id="vehicle_id"
        label="Vehículo"
        value={values.get('vehicle_id') ?? ''}
        onChange={(event) => onChange('vehicle_id', event.target.value)}
      >
        <option value="">Todos</option>
        {vehicles.map((vehicle) => (
          <option key={vehicle.id} value={vehicle.id}>
            {vehicle.plate}
          </option>
        ))}
      </SelectField>
      <div className="flex items-end">
        <Button variant="secondary" className="w-full" onClick={onClear}>
          Quitar filtros
        </Button>
      </div>
    </form>
  )
}
