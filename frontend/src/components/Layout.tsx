import { NavLink, Outlet } from 'react-router'
import { useAuth } from '../auth/useAuth'

const NAV_ITEMS = [
  { to: '/', label: 'Inicio' },
  { to: '/tickets', label: 'Tickets' },
  { to: '/vehicles', label: 'Vehículos' },
]

/** Estructura común de todas las pantallas: cabecera, menú y contenido. */
export function Layout() {
  const { isAuthenticated, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-amber-400 shadow">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <span className="text-xl font-bold">Taxicifra</span>
          {isAuthenticated && (
            <>
              <nav className="flex gap-1">
                {NAV_ITEMS.map(({ to, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end
                    className={({ isActive }) =>
                      `rounded-md px-3 py-1 text-sm font-medium hover:bg-amber-500 ${isActive ? 'bg-amber-500' : ''}`
                    }
                  >
                    {label}
                  </NavLink>
                ))}
              </nav>
              <button
                type="button"
                onClick={logout}
                className="ml-auto rounded-md px-3 py-1 text-sm font-medium hover:bg-amber-500"
              >
                Cerrar sesión
              </button>
            </>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
