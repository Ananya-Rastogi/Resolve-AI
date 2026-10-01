-- Supabase PostgreSQL Schema for Enterprise Multi-Agent Ticket Routing System
-- Version: 1.0.0

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id VARCHAR(64) UNIQUE NOT NULL,
    customer_name VARCHAR(255),
    customer_id VARCHAR(128),
    email VARCHAR(255),
    tier VARCHAR(32) NOT NULL DEFAULT 'Bronze' CHECK (tier IN ('Platinum', 'Gold', 'Silver', 'Bronze')),
    subject TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'escalated')),
    priority VARCHAR(32) NOT NULL DEFAULT 'Medium' CHECK (priority IN ('High', 'Medium', 'Low')),
    category VARCHAR(64) CHECK (category IN ('billing', 'shipping', 'technical', 'other')),
    sentiment VARCHAR(32) CHECK (sentiment IN ('POSITIVE', 'NEGATIVE')),
    confidence NUMERIC(5, 4),
    assigned_team VARCHAR(128) CHECK (assigned_team IN ('Finance Team', 'Logistics Team', 'Tech Support', 'General Support', 'Billing Support', 'Shipping Support', 'Technical Support')),
    escalation_level VARCHAR(64) NOT NULL DEFAULT 'Not Escalated',
    classification_source VARCHAR(32) CHECK (classification_source IN ('ml', 'llm', 'ml_fallback')),
    generated_reply TEXT,
    idempotency_key VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient queue filtering and search
CREATE INDEX IF NOT EXISTS idx_tickets_ticket_id ON tickets(ticket_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_team ON tickets(assigned_team);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_idempotency ON tickets(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- 2. Ticket Analyses Table
CREATE TABLE IF NOT EXISTS ticket_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id VARCHAR(64) NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    ml_topic VARCHAR(64),
    ml_sentiment VARCHAR(32),
    ml_confidence NUMERIC(5, 4),
    topic_confidence NUMERIC(5, 4),
    sentiment_confidence NUMERIC(5, 4),
    llm_called BOOLEAN NOT NULL DEFAULT FALSE,
    llm_succeeded BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_occurred BOOLEAN NOT NULL DEFAULT FALSE,
    llm_urgency VARCHAR(32),
    extracted_order_id VARCHAR(128),
    extracted_product VARCHAR(255),
    extracted_deadline VARCHAR(255),
    rag_query TEXT,
    rag_used BOOLEAN NOT NULL DEFAULT FALSE,
    retrieved_faq_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    used_faq_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    retrieval_count INTEGER NOT NULL DEFAULT 0,
    retrieval_latency_ms NUMERIC(10, 2),
    embedding_query_ms NUMERIC(10, 2),
    vector_search_ms NUMERIC(10, 2),
    total_retrieval_ms NUMERIC(10, 2),
    is_cold_retrieval BOOLEAN NOT NULL DEFAULT FALSE,
    rag_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analyses_ticket_id ON ticket_analyses(ticket_id);

-- 3. Ticket Events / Audit History Table
CREATE TABLE IF NOT EXISTS ticket_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id VARCHAR(64) NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(128) NOT NULL DEFAULT 'system',
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_ticket_id ON ticket_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON ticket_events(created_at DESC);

-- Automatic updated_at timestamp trigger for tickets
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_tickets_updated_at ON tickets;
CREATE TRIGGER trigger_tickets_updated_at
BEFORE UPDATE ON tickets
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
