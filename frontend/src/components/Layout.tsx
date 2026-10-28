import { Outlet } from 'react-router'
import { useAuth } from '../auth/useAuth'

/** Estructura común de todas las pantallas: cabecera y contenido. */
export function Layout() {
  const { isAuthenticated, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-amber-400 shadow">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <span className="text-xl font-bold">Taxicifra</span>
          {isAuthenticated && (
            <button
              type="button"
              onClick={logout}
              className="rounded-md px-3 py-1 text-sm font-medium hover:bg-amber-500"
            >
              Cerrar sesión
            </button>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
