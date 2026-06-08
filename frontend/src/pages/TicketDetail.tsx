import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Ticket } from '../types'
import api from '../services/api'

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

export default function TicketDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAdmin } = useAuth()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [message, setMessage] = useState('')
  const [newStatus, setNewStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadTicket()
  }, [id])

  const loadTicket = async () => {
    try {
      const response = await api.get(`/tickets/${id}`)
      setTicket(response.data)
      setNewStatus(response.data.status)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.post(`/tickets/${id}/updates`, { message })
      setMessage('')
      loadTicket()
    } catch (err) {
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdateStatus = async () => {
    try {
      await api.patch(`/tickets/${id}/status`, { status: newStatus })
      loadTicket()
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) return <div className="p-8 text-gray-500">Carregando...</div>
  if (!ticket) return <div className="p-8 text-gray-500">Chamado não encontrado.</div>

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">🎫 HelpDesk Pro</h1>
          <button onClick={() => navigate('/dashboard')} className="text-sm text-gray-500 hover:underline">
            Voltar
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Detalhes do chamado */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-start justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">{ticket.title}</h2>
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor[ticket.status]}`}>
              {statusLabel[ticket.status]}
            </span>
          </div>
          <p className="text-gray-600 mb-4">{ticket.description}</p>
          <div className="flex gap-4 text-sm text-gray-500">
            <span>Categoria: <strong>{ticket.category}</strong></span>
            <span>Prioridade: <strong>{ticket.priority}</strong></span>
            <span>Aberto em: <strong>{new Date(ticket.created_at).toLocaleDateString('pt-BR')}</strong></span>
          </div>
        </div>

        {/* Atualizar status — admin only */}
        {isAdmin && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="font-semibold text-gray-700 mb-3">Atualizar Status</h3>
            <div className="flex gap-3">
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="open">Aberto</option>
                <option value="in_progress">Em Atendimento</option>
                <option value="waiting">Aguardando</option>
                <option value="resolved">Resolvido</option>
                <option value="cancelled">Cancelado</option>
              </select>
              <button
                onClick={handleUpdateStatus}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm"
              >
                Salvar
              </button>
            </div>
          </div>
        )}

        {/* Histórico de atualizações */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="font-semibold text-gray-700 mb-4">Histórico</h3>
          {ticket.ticket_updates && ticket.ticket_updates.length === 0 ? (
            <p className="text-gray-400 text-sm">Nenhuma atualização ainda.</p>
          ) : (
            <div className="space-y-3">
              {ticket.ticket_updates?.map((update) => (
                <div key={update.id} className="border-l-4 border-blue-200 pl-4 py-1">
                  <p className="text-gray-700">{update.message}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(update.created_at).toLocaleString('pt-BR')}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Adicionar resposta */}
          <form onSubmit={handleAddUpdate} className="mt-6 space-y-3">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Adicionar uma resposta..."
              required
            />
            <button
              type="submit"
              disabled={submitting}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm disabled:opacity-50"
            >
              {submitting ? 'Enviando...' : 'Enviar'}
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}