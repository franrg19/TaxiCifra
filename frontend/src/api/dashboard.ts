import type {
  CategoryExpense,
  DashboardSummary,
  MonthlyTotals,
} from '../types/api'
import { apiRequest } from './client'

/** Los filtros usan los mismos nombres que la API: date_from, date_to, vehicle_id. */
export function getSummary(query: string): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>(`/dashboard/summary?${query}`)
}

export function getByCategory(query: string): Promise<CategoryExpense[]> {
  return apiRequest<CategoryExpense[]>(`/dashboard/by-category?${query}`)
}

export function getMonthly(query: string): Promise<MonthlyTotals[]> {
  return apiRequest<MonthlyTotals[]>(`/dashboard/monthly?${query}`)
}
