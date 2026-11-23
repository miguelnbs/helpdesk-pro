import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import PrivateRoute from './components/PrivateRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Dashboard from './pages/Dashboard'
import NewTicket from './pages/NewTicket'
import TicketDetail from './pages/TicketDetail'
import Profile from './pages/Profile'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/dashboard" element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          } />
          <Route path="/profile" element={
            <PrivateRoute>
              <Profile />
            </PrivateRoute>
          } />
          <Route path="/tickets/new" element={
            <PrivateRoute>
              <NewTicket />
            </PrivateRoute>
          } />
          <Route path="/tickets/:id" element={
            <PrivateRoute>
              <TicketDetail />
            </PrivateRoute>
          } />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
