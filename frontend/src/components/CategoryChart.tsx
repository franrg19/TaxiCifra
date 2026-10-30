import {
  Bar,
  BarChart,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { CATEGORY_LABELS } from '../api/tickets'
import { euroAxisValue, formatEuros } from '../format'
import type { CategoryExpense } from '../types/api'

const ROW_HEIGHT = 44

/** Gasto por categoría, de mayor a menor. */
export function CategoryChart({ data }: { data: CategoryExpense[] }) {
  if (data.length === 0) {
    return (
      <p className="text-slate-600">
        No hay gastos confirmados en este periodo.
      </p>
    )
  }

  // Recharts necesita números para dibujar; el texto exacto se conserva para mostrarlo
  const rows = data.map(({ category, total }) => ({
    name: CATEGORY_LABELS[category],
    value: Number(total),
    text: formatEuros(total),
  }))

  return (
    <ResponsiveContainer width="100%" height={rows.length * ROW_HEIGHT + 16}>
      <BarChart
        data={rows}
        layout="vertical"
        margin={{ top: 8, right: 88, bottom: 8, left: 8 }}
      >
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="name"
          width={108}
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#475569', fontSize: 13 }}
        />
        <Tooltip
          cursor={{ fill: '#f1f5f9' }}
          formatter={(value) => [euroAxisValue(Number(value)), 'Gasto']}
        />
        <Bar
          dataKey="value"
          isAnimationActive={false}
          name="Gasto"
          fill="#d97706"
          barSize={20}
          radius={[0, 4, 4, 0]}
        >
          <LabelList
            dataKey="text"
            position="right"
            style={{ fill: '#334155', fontSize: 13 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
