import type { ReactNode } from 'react'

interface AuthCardProps {
  title: string
  error: string | null
  children: ReactNode
}

/** Marco común de las pantallas de login y registro, con el mensaje de error. */
export function AuthCard({ title, error, children }: AuthCardProps) {
  return (
    <section className="mx-auto mt-8 max-w-sm rounded-lg bg-white p-6 shadow">
      <h1 className="mb-4 text-2xl font-semibold">{title}</h1>
      {error && (
        <p
          role="alert"
          className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {error}
        </p>
      )}
      {children}
    </section>
  )
}
