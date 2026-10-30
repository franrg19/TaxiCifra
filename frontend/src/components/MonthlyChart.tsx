import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { euroAxisValue } from '../format'
import type { MonthlyTotals } from '../types/api'

const MONTHS = [
  'Ene',
  'Feb',
  'Mar',
  'Abr',
  'May',
  'Jun',
  'Jul',
  'Ago',
  'Sep',
  'Oct',
  'Nov',
  'Dic',
]

/** Ingresos y gastos de cada mes del año. */
export function MonthlyChart({ data }: { data: MonthlyTotals[] }) {
  // Recharts necesita números: solo se usan para dibujar, no para hacer cuentas
  const rows = data.map(({ month, incomes, expenses }) => ({
    name: MONTHS[month - 1],
    incomes: Number(incomes),
    expenses: Number(expenses),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} stroke="#e2e8f0" />
        <XAxis
          dataKey="name"
          axisLine={false}
          tickLine={false}
          interval={0}
          tick={{ fill: '#475569', fontSize: 11 }}
        />
        <YAxis
          width={56}
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#475569', fontSize: 12 }}
          tickFormatter={(value: number) => value.toLocaleString('es-ES')}
        />
        <Tooltip
          cursor={{ fill: '#f1f5f9' }}
          formatter={(value) => euroAxisValue(Number(value))}
        />
        <Legend wrapperStyle={{ fontSize: 13 }} />
        <Bar
          dataKey="incomes"
          isAnimationActive={false}
          name="Ingresos"
          fill="#1d4ed8"
          radius={[4, 4, 0, 0]}
        />
        <Bar
          dataKey="expenses"
          isAnimationActive={false}
          name="Gastos"
          fill="#d97706"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
