export type CustomerTier = 'Platinum' | 'Gold' | 'Silver' | 'Bronze';
export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'escalated';
export type TicketPriority = 'High' | 'Medium' | 'Low';
export type TicketTopic = 'billing' | 'shipping' | 'technical' | 'other';
export type AssignedTeam = 'Finance Team' | 'Logistics Team' | 'Tech Support' | 'General Support';

export type ThemeMode = 'light' | 'dark' | 'system';
export type UserRole = 'admin' | 'manager' | 'agent';

export interface UserPreferences {
  notifications?: boolean;
  simple_mode?: boolean;
  compact_view?: boolean;
  [key: string]: any;
}

export interface UserProfile {
  id: string;
  email?: string;
  full_name?: string;
  avatar_url?: string;
  role: UserRole;
  theme: ThemeMode;
  preferences: UserPreferences;
  created_at?: string;
  updated_at?: string;
}

export interface Ticket {
  ticket_id: string;
  user_id?: string;
  customer_name?: string;
  customer_id?: string;
  email?: string;
  tier: CustomerTier;
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  category?: TicketTopic;
  sentiment?: 'POSITIVE' | 'NEGATIVE';
  confidence?: number;
  assigned_team?: AssignedTeam;
  escalation_level: string;
  classification_source?: 'ml' | 'llm' | 'ml_fallback';
  generated_reply?: string;
  created_at: string;
  updated_at: string;
}

export interface TicketAnalysis {
  ml_topic?: string;
  ml_sentiment?: string;
  ml_confidence?: number;
  topic_confidence?: number;
  sentiment_confidence?: number;
  llm_called: boolean;
  llm_succeeded: boolean;
  fallback_occurred: boolean;
  llm_urgency?: string;
  extracted_order_id?: string;
  extracted_product?: string;
  extracted_deadline?: string;
  rag_query?: string;
  rag_used: boolean;
  retrieved_faq_ids: string[];
  used_faq_ids: string[];
  retrieval_count: number;
  retrieval_latency_ms?: number;
  embedding_query_ms?: number;
  vector_search_ms?: number;
  total_retrieval_ms?: number;
  is_cold_retrieval: boolean;
  rag_error?: string;
}

export interface TicketEvent {
  id?: number | string;
  ticket_id: string;
  event_type: string;
  actor: string;
  details: Record<string, any>;
  created_at: string;
}

export interface TicketDetail extends Ticket {
  analysis?: TicketAnalysis;
  events: TicketEvent[];
  citations?: Array<{ faq_id?: string; category?: string; score?: number }>;
  retrieved_sources?: Array<{ faq_id?: string; category?: string; score?: number }>;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface LiveMetrics {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  escalated_tickets: number;
  high_priority_tickets: number;
  category_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
  sentiment_distribution: Record<string, number>;
  team_distribution: Record<string, number>;
  storage_backend: string;
}

export interface AnalyticsResponse {
  timestamp: string;
  live_metrics: LiveMetrics;
  offline_evaluation_benchmark?: {
    summary?: Record<string, any>;
    classification?: Record<string, any>;
    rag?: Record<string, any>;
    end_to_end?: Record<string, any>;
  };
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  storage_backend: string;
  vector_store_status: string;
  database_status: string;
  version: string;
}

export interface DuplicateTicketMatch {
  ticket_id: string;
  subject: string;
  similarity_score: number;
  similarity_reason: string;
  status: TicketStatus;
  priority: TicketPriority;
  category?: TicketTopic;
  created_at?: string;
}

export interface DuplicateCheckResponse {
  matches: DuplicateTicketMatch[];
  total_matches: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface HelpChatResponse {
  reply: string;
  suggested_actions?: Array<{ label: string; view?: string; action?: string; prompt?: string }>;
}

export interface SLAStatusInfo {
  status: 'On Track' | 'Due Soon' | 'Overdue' | 'Needs Review' | 'Resolved';
  timeRemaining: string;
  deadlineText: string;
  isOverdue: boolean;
  colorClass: string;
}
