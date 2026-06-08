export interface User {
  id: string
  full_name: string
  role: 'user' | 'admin'
  sector: string | null
  created_at: string
}

export interface Ticket {
  id: string
  title: string
  description: string
  category: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  status: 'open' | 'in_progress' | 'waiting' | 'resolved' | 'cancelled'
  created_by: string
  assigned_to: string | null
  created_at: string
  updated_at: string
  resolved_at: string | null
  ticket_updates?: TicketUpdate[]
}

export interface TicketUpdate {
  id: string
  ticket_id: string
  author_id: string
  message: string
  created_at: string
}