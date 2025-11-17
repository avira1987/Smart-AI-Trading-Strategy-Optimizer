import client from './client'

export interface TicketMessage {
  id: number
  ticket: number
  user: number
  user_name: string
  message: string
  is_admin: boolean
  created_at: string
}

export interface Ticket {
  id: number
  user: number
  user_name: string
  title: string
  description: string
  category: 'technical' | 'feature' | 'bug' | 'question' | 'other'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  status: 'open' | 'in_progress' | 'resolved' | 'closed'
  created_at: string
  updated_at: string
  resolved_at?: string | null
  admin_response?: string
  admin_user?: number | null
  admin_name?: string | null
  messages_count?: number
  messages?: TicketMessage[]
  redirect_url?: string
}

export interface CreateTicketData {
  title: string
  description: string
  category: 'technical' | 'feature' | 'bug' | 'question' | 'other'
  priority: 'low' | 'medium' | 'high' | 'urgent'
}

// Get all tickets for the logged-in user
export const getTickets = (params?: { status?: string; category?: string }) => 
  client.get<Ticket[]>('/tickets/', { params })

// Get a single ticket by ID
export const getTicket = (id: number) => 
  client.get<Ticket>(`/tickets/${id}/`)

// Create a new ticket
export const createTicket = (data: CreateTicketData) => 
  client.post<Ticket>('/tickets/', data)

// Add a message to a ticket
export const addTicketMessage = (id: number, message: string) => 
  client.post<TicketMessage>(`/tickets/${id}/add_message/`, { message })

// Close a ticket
export const closeTicket = (id: number) => 
  client.post<Ticket>(`/tickets/${id}/close/`)

