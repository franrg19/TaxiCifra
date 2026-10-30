import { useContext } from 'react'
import { AuthContext, type AuthContextValue } from './AuthContext'

/** Da acceso a la sesión desde cualquier componente dentro de AuthProvider. */
export function useAuth(): AuthContextValue {
  const auth = useContext(AuthContext)
  if (auth === null) {
    throw new Error('useAuth debe usarse dentro de AuthProvider')
  }
  return auth
}
