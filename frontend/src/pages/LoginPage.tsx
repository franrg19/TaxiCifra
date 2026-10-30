import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation } from 'react-router'
import { login as apiLogin } from '../api/auth'
import { errorMessage } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { AuthCard } from '../components/AuthCard'
import { Button } from '../components/Button'
import { FormField } from '../components/FormField'

export function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Con sesión iniciada se vuelve a la pantalla que se quería ver (o al inicio)
  const from = (location.state as { from?: string } | null)?.from ?? '/'
  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const { access_token } = await apiLogin({ email, password })
      login(access_token)
    } catch (err) {
      setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <AuthCard title="Iniciar sesión" error={error}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <FormField
          id="password"
          label="Contraseña"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" disabled={submitting} className="w-full">
          {submitting ? 'Entrando…' : 'Entrar'}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-600">
        ¿No tienes cuenta?{' '}
        <Link
          to="/register"
          className="font-medium text-amber-700 hover:underline"
        >
          Regístrate
        </Link>
      </p>
    </AuthCard>
  )
}
