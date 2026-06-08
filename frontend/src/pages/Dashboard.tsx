import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { Ticket } from '../types'
import api from '../services/api'
import { useNavigate } from 'react-router-dom'

const statusLabel: Record<string, string> = {
  open: 'Aberto',
  in_progress: 'Em Atendimento',
  waiting: 'Aguardando',
  resolved: 'Resolvido',
  cancelled: 'Cancelado',
}

const statusColor: Record<string, string> = {
  open: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-yellow-100 text-yellow-700',
  waiting: 'bg-purple-100 text-purple-700',
  resolved: 'bg-green-100 text-green-700',
  cancelled: 'bg-gray-100 text-gray-700',
}

const priorityLabel: Record<string, string> = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
  critical: 'Crítica',
}

const priorityColor: Record<string, string> = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-orange-100 text-orange-600',
  critical: 'bg-red-100 text-red-600',
}

export default function Dashboard() {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadTickets()
  }, [])

  const loadTickets = async () => {
    try {
      const endpoint = isAdmin ? '/tickets/all' : '/tickets'
      const response = await api.get(endpoint)
      setTickets(response.data.tickets)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">🎫 HelpDesk Pro</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.full_name}
              {isAdmin && (
                <span className="ml-2 bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                  Admin
                </span>
              )}
            </span>
            <button
              onClick={logout}
              className="text-sm text-red-500 hover:underline"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Ações */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-700">
            {isAdmin ? 'Todos os Chamados' : 'Meus Chamados'}
          </h2>
          <button
            onClick={() => navigate('/tickets/new')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm"
          >
            + Novo Chamado
          </button>
        </div>

        {/* Lista de chamados */}
        {loading ? (
          <p className="text-gray-500">Carregando...</p>
        ) : tickets.length === 0 ? (
          <div className="bg-white rounded-lg p-8 text-center text-gray-500 shadow-sm">
            Nenhum chamado encontrado.
          </div>
        ) : (
          <div className="space-y-3">
            {tickets.map((ticket) => (
              <div
                key={ticket.id}
                onClick={() => navigate(`/tickets/${ticket.id}`)}
                className="bg-white rounded-lg shadow-sm p-4 cursor-pointer hover:shadow-md transition"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium text-gray-800">{ticket.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{ticket.category}</p>
                  </div>
                  <div className="flex gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${priorityColor[ticket.priority]}`}>
                      {priorityLabel[ticket.priority]}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor[ticket.status]}`}>
                      {statusLabel[ticket.status]}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {new Date(ticket.created_at).toLocaleDateString('pt-BR')}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}