import { CATEGORY_LABELS, STATUS_LABELS } from '../api/tickets'
import type { Vehicle } from '../types/api'
import { Button } from './Button'
import { FormField } from './FormField'
import { SelectField } from './SelectField'

interface TicketFiltersProps {
  values: URLSearchParams
  vehicles: Vehicle[]
  onChange: (name: string, value: string) => void
  onClear: () => void
}

/** Filtros del listado de tickets. Sus valores viven en la URL de la página. */
export function TicketFilters({
  values,
  vehicles,
  onChange,
  onClear,
}: TicketFiltersProps) {
  return (
    <form className="grid gap-4 rounded-lg bg-white p-4 shadow sm:grid-cols-2 lg:grid-cols-3">
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
        id="category"
        label="Categoría"
        value={values.get('category') ?? ''}
        onChange={(event) => onChange('category', event.target.value)}
      >
        <option value="">Todas</option>
        {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </SelectField>
      <SelectField
        id="status"
        label="Estado"
        value={values.get('status') ?? ''}
        onChange={(event) => onChange('status', event.target.value)}
      >
        <option value="">Todos</option>
        {Object.entries(STATUS_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </SelectField>
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
