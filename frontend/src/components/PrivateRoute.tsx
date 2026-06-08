import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function PrivateRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <div className="p-8 text-gray-500">Carregando...</div>
  if (!isAuthenticated) return <Navigate to="/login" />

  return children
}