import { Button } from './Button'

interface PaginationProps {
  page: number
  size: number
  total: number
  onPageChange: (page: number) => void
}

/** Botones de anterior y siguiente. Con una sola página no pinta nada. */
export function Pagination({
  page,
  size,
  total,
  onPageChange,
}: PaginationProps) {
  const lastPage = Math.ceil(total / size)
  if (lastPage <= 1) {
    return null
  }
  return (
    <nav aria-label="Paginación" className="flex items-center justify-between">
      <Button
        variant="secondary"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        Anterior
      </Button>
      <span className="text-sm text-slate-600">
        Página {page} de {lastPage}
      </span>
      <Button
        variant="secondary"
        disabled={page >= lastPage}
        onClick={() => onPageChange(page + 1)}
      >
        Siguiente
      </Button>
    </nav>
  )
}
