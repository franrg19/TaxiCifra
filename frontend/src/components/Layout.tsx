import { Outlet } from 'react-router'

/** Estructura común de todas las pantallas: cabecera y contenido. */
export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-amber-400 shadow">
        <div className="mx-auto max-w-5xl px-4 py-3">
          <span className="text-xl font-bold">Taxicifra</span>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
