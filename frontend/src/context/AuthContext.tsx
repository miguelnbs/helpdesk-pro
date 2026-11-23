import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User } from '../types'
import api from '../services/api'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  updateUser: (user: User) => void
  isAuthenticated: boolean
  isAdmin: boolean
  loading: boolean
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Recupera a sessão salva no localStorage ao carregar
  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }

    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password })
    const { access_token } = response.data

    localStorage.setItem('token', access_token)

    const profileResponse = await api.get('/me')
    const profile = profileResponse.data

    localStorage.setItem('user', JSON.stringify(profile))

    setToken(access_token)
    setUser(profile)
  }

  // Atualiza o usuário em memória e no localStorage (usado após editar o perfil)
  const updateUser = (updated: User) => {
    localStorage.setItem('user', JSON.stringify(updated))
    setUser(updated)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{
      user,
      token,
      login,
      logout,
      updateUser,
      isAuthenticated: !!token,
      isAdmin: user?.role === 'admin',
      loading
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
