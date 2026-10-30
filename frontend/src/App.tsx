import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { AuthProvider } from './auth/AuthProvider'
import { Layout } from './components/Layout'
import { RequireAuth } from './components/RequireAuth'
import { HomePage } from './pages/HomePage'
import { IncomesPage } from './pages/IncomesPage'
import { LoginPage } from './pages/LoginPage'
import { OdometerPage } from './pages/OdometerPage'
import { RegisterPage } from './pages/RegisterPage'
import { TicketReviewPage } from './pages/TicketReviewPage'
import { TicketsPage } from './pages/TicketsPage'
import { VehiclesPage } from './pages/VehiclesPage'

/** Rutas de la aplicación. Cada pantalla nueva se añade aquí. */
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            {/* Todo lo que está aquí dentro exige sesión iniciada */}
            <Route element={<RequireAuth />}>
              <Route index element={<HomePage />} />
              <Route path="/tickets" element={<TicketsPage />} />
              <Route path="/tickets/:ticketId" element={<TicketReviewPage />} />
              <Route path="/incomes" element={<IncomesPage />} />
              <Route path="/odometer" element={<OdometerPage />} />
              <Route path="/vehicles" element={<VehiclesPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
