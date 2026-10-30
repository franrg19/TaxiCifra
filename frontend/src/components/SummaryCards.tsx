import { formatEuros, formatKm } from '../format'
import type { DashboardSummary } from '../types/api'

/** Cifras principales del periodo. Lo que no se puede calcular se muestra como "Sin datos". */
export function SummaryCards({ summary }: { summary: DashboardSummary }) {
  const cards = [
    { label: 'Ingresos', value: formatEuros(summary.incomes) },
    { label: 'Gastos confirmados', value: formatEuros(summary.expenses) },
    { label: 'Beneficio estimado', value: formatEuros(summary.profit) },
    { label: 'Tickets confirmados', value: String(summary.ticket_count) },
    {
      label: 'Kilómetros recorridos',
      value:
        summary.km_driven === null ? 'Sin datos' : formatKm(summary.km_driven),
    },
    {
      label: 'Coste por km',
      value: summary.cost_per_km
        ? `${formatEuros(summary.cost_per_km)}/km`
        : 'Sin datos',
    },
  ]

  return (
    <dl className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      {cards.map(({ label, value }) => (
        <div key={label} className="rounded-lg bg-white p-4 shadow">
          <dt className="text-sm text-slate-600">{label}</dt>
          <dd className="mt-1 text-xl font-semibold sm:text-2xl">{value}</dd>
        </div>
      ))}
    </dl>
  )
}
