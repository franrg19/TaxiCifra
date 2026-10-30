import type { ReactNode } from 'react'
import { ErrorMessage } from './ErrorMessage'

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
      <div className="mb-4 empty:hidden">
        <ErrorMessage message={error} />
      </div>
      {children}
    </section>
  )
}
