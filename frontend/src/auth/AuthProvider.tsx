import { useEffect, useState, type ReactNode } from 'react'
import { setUnauthorizedHandler, tokenStorage } from '../api/client'
import { AuthContext } from './AuthContext'

/** Guarda el estado de la sesión y lo comparte con toda la aplicación. */
export function AuthProvider({ children }: { children: ReactNode }) {
  // Al abrir la app se recupera el token guardado: la sesión sigue abierta tras recargar
  const [token, setToken] = useState<string | null>(tokenStorage.get)

  useEffect(() => {
    // Si la API rechaza el token, el cliente lo borra y aquí se refleja en la pantalla
    setUnauthorizedHandler(() => setToken(null))
  }, [])

  const login = (newToken: string) => {
    tokenStorage.set(newToken)
    setToken(newToken)
  }

  const logout = () => {
    tokenStorage.clear()
    setToken(null)
  }

  return (
    <AuthContext.Provider
      value={{ isAuthenticated: token !== null, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}
