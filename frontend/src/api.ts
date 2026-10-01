import {
  AnalyticsResponse,
  HealthResponse,
  Ticket,
  TicketDetail,
  TicketListResponse,
  TicketPriority,
  TicketStatus,
  TicketTopic,
} from './types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAnalytics(): Promise<AnalyticsResponse> {
  const res = await fetch(`${API_BASE}/analytics`);
  if (!res.ok) {
    throw new Error(`Failed to load analytics: ${res.statusText}`);
  }
  return res.json();
}

export interface ListTicketsParams {
  status?: string;
  category?: string;
  priority?: string;
  assigned_team?: string;
  search?: string;
  page?: number;
  limit?: number;
}

export async function fetchTickets(params: ListTicketsParams = {}): Promise<TicketListResponse> {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.category) query.set('category', params.category);
  if (params.priority) query.set('priority', params.priority);
  if (params.assigned_team) query.set('assigned_team', params.assigned_team);
  if (params.search) query.set('search', params.search);
  if (params.page) query.set('page', params.page.toString());
  if (params.limit) query.set('limit', params.limit.toString());

  const res = await fetch(`${API_BASE}/tickets?${query.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to load tickets: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTicketDetail(ticketId: string): Promise<TicketDetail> {
  const res = await fetch(`${API_BASE}/tickets/${encodeURIComponent(ticketId)}`);
  if (!res.ok) {
    throw new Error(`Failed to load ticket ${ticketId}: ${res.statusText}`);
  }
  return res.json();
}

export interface CreateTicketPayload {
  subject: string;
  customer_name?: string;
  customer_id?: string;
  email?: string;
  tier: string;
  idempotency_key?: string;
}

export async function createTicket(payload: CreateTicketPayload): Promise<TicketDetail> {
  const res = await fetch(`${API_BASE}/tickets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to create ticket (${res.status})`);
  }
  return res.json();
}

export interface UpdateTicketPayload {
  status?: TicketStatus;
  assigned_team?: string;
  priority?: TicketPriority;
  escalation_level?: string;
  actor?: string;
}

export async function updateTicket(ticketId: string, updates: UpdateTicketPayload): Promise<Ticket> {
  const res = await fetch(`${API_BASE}/tickets/${encodeURIComponent(ticketId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update ticket: ${res.statusText}`);
  }
  return res.json();
}
