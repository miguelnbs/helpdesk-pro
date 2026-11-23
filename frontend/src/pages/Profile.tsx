import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'

export default function Profile() {
  const { user, updateUser, isAdmin, logout } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [sector, setSector] = useState(user?.sector ?? '')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Busca o perfil atualizado (inclui o e-mail) ao abrir a tela
  useEffect(() => {
    api.get('/me')
      .then((response) => {
        updateUser(response.data)
        setFullName(response.data.full_name ?? '')
        setSector(response.data.sector ?? '')
      })
      .catch((err) => console.error(err))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage('')
    setError('')

    if (fullName.trim().length < 2) {
      setError('Informe um nome com pelo menos 2 caracteres.')
      return
    }

    setLoading(true)

    try {
      const response = await api.patch('/me', {
        full_name: fullName.trim(),
        sector: sector.trim(),
      })
      updateUser(response.data)
      setMessage('Perfil atualizado com sucesso.')
    } catch (err) {
      setError('Não foi possível atualizar o perfil. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">🎫 HelpDesk Pro</h1>
          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/dashboard')} className="text-sm text-gray-500 hover:underline">
              Voltar
            </button>
            <button onClick={logout} className="text-sm text-red-500 hover:underline">
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Meus dados</h2>
          <dl className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">E-mail</dt>
              <dd className="text-gray-800 font-medium break-all">{user?.email ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Nível de acesso</dt>
              <dd>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${isAdmin ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>
                  {isAdmin ? 'Administrador' : 'Usuário'}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Membro desde</dt>
              <dd className="text-gray-800 font-medium">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString('pt-BR') : '—'}
              </dd>
            </div>
          </dl>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Editar perfil</h2>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {message && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome completo</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Setor</label>
              <input
                type="text"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ex.: Financeiro, Logística, TI"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm disabled:opacity-50"
            >
              {loading ? 'Salvando...' : 'Salvar alterações'}
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}
