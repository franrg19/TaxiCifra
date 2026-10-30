import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router'
import { login as apiLogin, register } from '../api/auth'
import { errorMessage } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { AuthCard } from '../components/AuthCard'
import { Button } from '../components/Button'
import { FormField } from '../components/FormField'

export function RegisterPage() {
  const { isAuthenticated, login } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register({ name, email, password })
      // Tras registrarse, se inicia sesión directamente para no pedir los datos otra vez
      const { access_token } = await apiLogin({ email, password })
      login(access_token)
    } catch (err) {
      setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <AuthCard title="Crear cuenta" error={error}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField
          id="name"
          label="Nombre"
          autoComplete="name"
          required
          maxLength={100}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
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
          label="Contraseña (mínimo 8 caracteres)"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={128}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" disabled={submitting} className="w-full">
          {submitting ? 'Creando cuenta…' : 'Crear cuenta'}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-600">
        ¿Ya tienes cuenta?{' '}
        <Link
          to="/login"
          className="font-medium text-amber-700 hover:underline"
        >
          Inicia sesión
        </Link>
      </p>
    </AuthCard>
  )
}
