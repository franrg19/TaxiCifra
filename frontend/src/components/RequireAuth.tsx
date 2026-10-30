import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from '../auth/useAuth'

/** Deja pasar a las rutas protegidas solo con sesión; si no, lleva al login. */
export function RequireAuth() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    // Se recuerda a dónde quería ir para volver allí tras iniciar sesión
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <Outlet />
}
