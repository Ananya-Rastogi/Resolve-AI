import {
  AnalyticsResponse,
  HealthResponse,
  Ticket,
  TicketDetail,
  TicketListResponse,
  TicketPriority,
  TicketStatus,
  UserProfile,
  DuplicateCheckResponse,
  HelpChatResponse,
} from './types';
import { supabase } from './lib/supabase';

const DEFAULT_BACKEND_URL = 'https://resolve-ai-backend-p6s7.onrender.com';

const API_BASE = `${(
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? DEFAULT_BACKEND_URL : '')
).replace(/\/$/, '')}/api`;


async function getAuthHeaders(): Promise<HeadersInit> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      if (session.expires_at && Math.floor(Date.now() / 1000) >= session.expires_at) {
        const { data: refreshData } = await supabase.auth.refreshSession();
        if (refreshData?.session?.access_token) {
          headers['Authorization'] = `Bearer ${refreshData.session.access_token}`;
          return headers;
        }
      }
      headers['Authorization'] = `Bearer ${session.access_token}`;
      return headers;
    }
  } catch (e) {
    // Supabase auth not initialized or network offline
  }

  // Local development fallback: send token identifying local authenticated user
  try {
    const localSavedUser = localStorage.getItem('resolve_local_user');
    if (localSavedUser) {
      const parsed = JSON.parse(localSavedUser);
      const userKey = parsed.id || parsed.email || 'local-agent';
      headers['Authorization'] = `Bearer dev-${encodeURIComponent(userKey)}`;
    }
  } catch (e) {
    // Ignore JSON parse errors
  }

  return headers;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAnalytics(): Promise<AnalyticsResponse> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/analytics`, { headers });
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
  user_id?: string;
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
  if (params.user_id) query.set('user_id', params.user_id);
  if (params.page) query.set('page', params.page.toString());
  if (params.limit) query.set('limit', params.limit.toString());

  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/tickets?${query.toString()}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to load tickets: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTicketDetail(ticketId: string): Promise<TicketDetail> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/tickets/${encodeURIComponent(ticketId)}`, { headers });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to load ticket ${ticketId}: ${res.statusText}`);
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
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/tickets`, {
    method: 'POST',
    headers,
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
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/tickets/${encodeURIComponent(ticketId)}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify(updates),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update ticket: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchUserProfile(): Promise<UserProfile> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/user/profile`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to load user profile: ${res.statusText}`);
  }
  return res.json();
}

export async function updateUserProfileApi(updates: Partial<UserProfile>): Promise<UserProfile> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/user/profile`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify(updates),
  });
  if (!res.ok) {
    throw new Error(`Failed to update profile: ${res.statusText}`);
  }
  return res.json();
}

export async function checkDuplicateTickets(
  subject: string,
  excludeTicketId?: string
): Promise<DuplicateCheckResponse> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/tickets/check-duplicates`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      subject,
      exclude_ticket_id: excludeTicketId,
    }),
  });
  if (!res.ok) {
    throw new Error(`Duplicate check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTicketDuplicates(ticketId: string): Promise<DuplicateCheckResponse> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/tickets/${encodeURIComponent(ticketId)}/duplicates`, {
    headers,
  });
  if (!res.ok) {
    throw new Error(`Failed to load duplicates for ticket ${ticketId}: ${res.statusText}`);
  }
  return res.json();
}

export async function sendHelpChatMessage(
  message: string,
  currentPage?: string,
  history?: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>
): Promise<HelpChatResponse> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/help/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      current_page: currentPage,
      history: history || [],
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Help chatbot error (${res.status})`);
  }
  return res.json();
}
