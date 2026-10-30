import { useState } from 'react'
import { NavLink, Outlet } from 'react-router'
import logo from '../assets/logo-yellow-background.png'
import { useAuth } from '../auth/useAuth'

const NAV_ITEMS = [
  { to: '/', label: 'Resumen' },
  { to: '/tickets', label: 'Tickets' },
  { to: '/incomes', label: 'Ingresos' },
  { to: '/odometer', label: 'Kilometraje' },
  { to: '/vehicles', label: 'Vehículos' },
]

const ITEM_STYLE = 'rounded-md px-3 py-1 text-sm font-medium hover:bg-amber-500'

/** Estructura común de todas las pantallas: cabecera, menú y contenido. */
export function Layout() {
  const { isAuthenticated, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  function handleLogout() {
    setMenuOpen(false)
    logout()
  }

  const navLinks = NAV_ITEMS.map(({ to, label }) => (
    <NavLink
      key={to}
      to={to}
      end
      // En móvil, elegir una pantalla cierra el menú
      onClick={() => setMenuOpen(false)}
      className={({ isActive }) =>
        `${ITEM_STYLE} ${isActive ? 'bg-amber-500' : ''}`
      }
    >
      {label}
    </NavLink>
  ))

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-amber-400 shadow">
        <div className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-1">
          <img src={logo} alt="Taxicifra" className="h-16 w-auto" />
          {isAuthenticated && (
            <>
              {/* Escritorio: menú en línea */}
              <nav className="hidden gap-1 md:flex">{navLinks}</nav>
              <button
                type="button"
                onClick={handleLogout}
                className={`${ITEM_STYLE} ml-auto hidden md:block`}
              >
                Cerrar sesión
              </button>

              {/* Móvil: botón hamburguesa */}
              <button
                type="button"
                aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
                aria-expanded={menuOpen}
                aria-controls="mobile-menu"
                onClick={() => setMenuOpen(!menuOpen)}
                className="ml-auto rounded-md p-2 hover:bg-amber-500 md:hidden"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  aria-hidden="true"
                  className="h-6 w-6"
                >
                  <path
                    d={
                      menuOpen
                        ? 'M6 6l12 12M18 6L6 18'
                        : 'M4 6h16M4 12h16M4 18h16'
                    }
                  />
                </svg>
              </button>
            </>
          )}
        </div>
        {isAuthenticated && menuOpen && (
          <nav
            id="mobile-menu"
            className="flex flex-col gap-1 px-4 pb-3 md:hidden"
          >
            {navLinks}
            <button
              type="button"
              onClick={handleLogout}
              className={`${ITEM_STYLE} text-left`}
            >
              Cerrar sesión
            </button>
          </nav>
        )}
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
