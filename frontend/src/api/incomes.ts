import type { Income, IncomeInput, Page } from '../types/api'
import { apiRequest } from './client'

/** Lista ingresos. Los filtros y la página usan los mismos nombres que la API. */
export function listIncomes(query: string): Promise<Page<Income>> {
  return apiRequest<Page<Income>>(`/incomes?${query}`)
}

export function createIncome(data: IncomeInput): Promise<Income> {
  return apiRequest<Income>('/incomes', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateIncome(id: number, data: IncomeInput): Promise<Income> {
  return apiRequest<Income>(`/incomes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteIncome(id: number): Promise<void> {
  return apiRequest<void>(`/incomes/${id}`, { method: 'DELETE' })
}
