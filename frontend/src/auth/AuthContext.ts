import { createContext } from 'react'

export interface AuthContextValue {
  isAuthenticated: boolean
  /** Guarda el token recibido al iniciar sesión. */
  login: (token: string) => void
  /** Borra el token y cierra la sesión. */
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
