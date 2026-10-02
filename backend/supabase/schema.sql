-- ==============================================================================
-- Supabase PostgreSQL Schema for Resolve AI
-- Enterprise Multi-Agent Ticket Resolution Platform
-- Version: 2.2.0 (Hardened Auth, Strict RLS, Search-Path Hardened, Full Permissions)
-- ==============================================================================

-- 1. Ensure UUID Extension Support (Preserves existing installations in public or other schemas)
DO $$
DECLARE
    existing_ext_schema text;
BEGIN
    SELECT n.nspname INTO existing_ext_schema
    FROM pg_extension e
    JOIN pg_namespace n ON e.extnamespace = n.oid
    WHERE e.extname = 'uuid-ossp';

    IF existing_ext_schema IS NULL THEN
        CREATE SCHEMA IF NOT EXISTS extensions;
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;
    ELSE
        RAISE NOTICE 'Extension "uuid-ossp" already installed in schema "%". Preserving location.', existing_ext_schema;
    END IF;
END $$;

-- 2. User Profiles Table (Linked directly to Supabase Auth auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255),
    email VARCHAR(255),
    avatar_url TEXT,
    role VARCHAR(32) NOT NULL DEFAULT 'agent' CHECK (role IN ('admin', 'manager', 'agent')),
    theme VARCHAR(16) NOT NULL DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system')),
    preferences JSONB NOT NULL DEFAULT '{"notifications": true, "simple_mode": true, "compact_view": false}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now()
);

-- Ensure missing columns exist if public.profiles pre-existed from older versions
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'profiles'
    ) THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'email') THEN
            ALTER TABLE public.profiles ADD COLUMN email VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'full_name') THEN
            ALTER TABLE public.profiles ADD COLUMN full_name VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'avatar_url') THEN
            ALTER TABLE public.profiles ADD COLUMN avatar_url TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'role') THEN
            ALTER TABLE public.profiles ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'agent' CHECK (role IN ('admin', 'manager', 'agent'));
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'theme') THEN
            ALTER TABLE public.profiles ADD COLUMN theme VARCHAR(16) NOT NULL DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system'));
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'preferences') THEN
            ALTER TABLE public.profiles ADD COLUMN preferences JSONB NOT NULL DEFAULT '{"notifications": true, "simple_mode": true, "compact_view": false}'::jsonb;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'created_at') THEN
            ALTER TABLE public.profiles ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now();
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'updated_at') THEN
            ALTER TABLE public.profiles ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now();
        END IF;
    END IF;
END $$;

-- Index on profiles email & role (created only after all required columns exist)
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);

-- 3. Tickets Table (with user_id tracking the authenticated agent / creator)
CREATE TABLE IF NOT EXISTS public.tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(64) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now()
);

-- Comprehensive Existing-Schema Compatibility & Diagnostic Block
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'tickets'
    ) THEN
        -- Diagnostic Check 1: Detect non-base table (views, foreign tables)
        IF (SELECT table_type FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'tickets') <> 'BASE TABLE' THEN
            RAISE EXCEPTION 'public.tickets already exists as a non-base table (%). Manual migration required.',
                (SELECT table_type FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'tickets');
        END IF;

        -- Diagnostic Check 2: If ticket_id already exists on an older table, check for duplicate values
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'ticket_id'
        ) THEN
            IF EXISTS (
                SELECT ticket_id FROM public.tickets 
                WHERE ticket_id IS NOT NULL 
                GROUP BY ticket_id HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION 'Legacy public.tickets table contains duplicate ticket_id values. Manual deduplication required before migration.';
            END IF;
        END IF;

        -- Step A: Ensure primary key 'id' exists with safe backfill
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'id') THEN
            ALTER TABLE public.tickets ADD COLUMN id UUID DEFAULT gen_random_uuid();
            UPDATE public.tickets SET id = gen_random_uuid() WHERE id IS NULL;
            ALTER TABLE public.tickets ALTER COLUMN id SET NOT NULL;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_schema = 'public' AND table_name = 'tickets' AND constraint_type = 'PRIMARY KEY') THEN
                ALTER TABLE public.tickets ADD PRIMARY KEY (id);
            END IF;
        END IF;

        -- Step B: Ensure 'ticket_id' exists, is backfilled for legacy rows, is NOT NULL, and has UNIQUE constraint
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'ticket_id') THEN
            ALTER TABLE public.tickets ADD COLUMN ticket_id VARCHAR(64);
            UPDATE public.tickets 
            SET ticket_id = 'TKT-LEGACY-' || COALESCE(id::text, ctid::text)
            WHERE ticket_id IS NULL;
            ALTER TABLE public.tickets ALTER COLUMN ticket_id SET NOT NULL;
        END IF;

        -- Ensure UNIQUE constraint on ticket_id (required by child foreign keys in analyses & events)
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conrelid = 'public.tickets'::regclass AND contype = 'u' 
            AND conname = 'tickets_ticket_id_key'
        ) AND NOT EXISTS (
            SELECT 1 FROM pg_index i 
            JOIN pg_class c ON c.oid = i.indexrelid 
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) 
            WHERE i.indrelid = 'public.tickets'::regclass AND i.indisunique AND a.attname = 'ticket_id'
        ) THEN
            ALTER TABLE public.tickets ADD CONSTRAINT tickets_ticket_id_key UNIQUE (ticket_id);
        END IF;

        -- Step C: Ensure 'subject' exists with safe fallback backfill
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'subject') THEN
            ALTER TABLE public.tickets ADD COLUMN subject TEXT DEFAULT 'Legacy Ticket' NOT NULL;
        END IF;

        -- Step D: Ensure core workflow status & priority exist with defaults
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'status') THEN
            ALTER TABLE public.tickets ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'open';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'priority') THEN
            ALTER TABLE public.tickets ADD COLUMN priority VARCHAR(32) NOT NULL DEFAULT 'Medium';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'tier') THEN
            ALTER TABLE public.tickets ADD COLUMN tier VARCHAR(32) NOT NULL DEFAULT 'Bronze';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'escalation_level') THEN
            ALTER TABLE public.tickets ADD COLUMN escalation_level VARCHAR(64) NOT NULL DEFAULT 'Not Escalated';
        END IF;

        -- Step E: Ensure timestamps exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'created_at') THEN
            ALTER TABLE public.tickets ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now();
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'updated_at') THEN
            ALTER TABLE public.tickets ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now();
        END IF;

        -- Step F: Ensure foreign key on user_id exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'user_id') THEN
            ALTER TABLE public.tickets ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
        END IF;

        -- Step G: Auxiliary nullable columns
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'customer_name') THEN
            ALTER TABLE public.tickets ADD COLUMN customer_name VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'customer_id') THEN
            ALTER TABLE public.tickets ADD COLUMN customer_id VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'email') THEN
            ALTER TABLE public.tickets ADD COLUMN email VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'category') THEN
            ALTER TABLE public.tickets ADD COLUMN category VARCHAR(64);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'sentiment') THEN
            ALTER TABLE public.tickets ADD COLUMN sentiment VARCHAR(32);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'confidence') THEN
            ALTER TABLE public.tickets ADD COLUMN confidence NUMERIC(5, 4);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'assigned_team') THEN
            ALTER TABLE public.tickets ADD COLUMN assigned_team VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'classification_source') THEN
            ALTER TABLE public.tickets ADD COLUMN classification_source VARCHAR(32);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'generated_reply') THEN
            ALTER TABLE public.tickets ADD COLUMN generated_reply TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tickets' AND column_name = 'idempotency_key') THEN
            ALTER TABLE public.tickets ADD COLUMN idempotency_key VARCHAR(128);
        END IF;
    END IF;
END $$;

-- Indexes for efficient queue filtering and search
CREATE INDEX IF NOT EXISTS idx_tickets_ticket_id ON public.tickets(ticket_id);
CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON public.tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON public.tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON public.tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON public.tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_team ON public.tickets(assigned_team);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON public.tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_idempotency ON public.tickets(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- 4. Ticket Analyses Table
CREATE TABLE IF NOT EXISTS public.ticket_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(64) NOT NULL REFERENCES public.tickets(ticket_id) ON DELETE CASCADE,
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now()
);

CREATE INDEX IF NOT EXISTS idx_analyses_ticket_id ON public.ticket_analyses(ticket_id);

-- 5. Ticket Events / Audit History Table
CREATE TABLE IF NOT EXISTS public.ticket_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(64) NOT NULL REFERENCES public.tickets(ticket_id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(128) NOT NULL DEFAULT 'system',
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.now()
);

CREATE INDEX IF NOT EXISTS idx_events_ticket_id ON public.ticket_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON public.ticket_events(created_at DESC);

-- 6. Helper Security Definer Functions (Hardened search_path = '')
CREATE OR REPLACE FUNCTION public.get_auth_user_role()
RETURNS VARCHAR AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid();
$$ LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '';

REVOKE EXECUTE ON FUNCTION public.get_auth_user_role() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_auth_user_role() TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE id = auth.uid() AND role = 'admin'
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '';

REVOKE EXECUTE ON FUNCTION public.is_admin() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_admin() TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.is_admin_or_manager()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE id = auth.uid() AND role IN ('admin', 'manager')
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '';

REVOKE EXECUTE ON FUNCTION public.is_admin_or_manager() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_admin_or_manager() TO authenticated, service_role;

-- 7. Automatic updated_at timestamp triggers
CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = pg_catalog.now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

DROP TRIGGER IF EXISTS trigger_tickets_updated_at ON public.tickets;
CREATE TRIGGER trigger_tickets_updated_at
BEFORE UPDATE ON public.tickets
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

DROP TRIGGER IF EXISTS trigger_profiles_updated_at ON public.profiles;
CREATE TRIGGER trigger_profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

-- 8. Enforce Profile Security on INSERT & UPDATE
-- Note: Intentionally NOT SECURITY DEFINER so that current_user reflects the actual caller
-- (e.g. 'authenticated' for web clients, 'postgres' for dashboard/bootstrap).
CREATE OR REPLACE FUNCTION public.enforce_profile_security()
RETURNS TRIGGER AS $$
BEGIN
    -- On INSERT: ordinary users cannot create elevated roles
    IF TG_OP = 'INSERT' THEN
        IF (NEW.role IS DISTINCT FROM 'agent') THEN
            IF NOT (
                current_user IN ('postgres', 'supabase_admin')
                OR COALESCE(auth.jwt() ->> 'role', '') = 'service_role'
                OR COALESCE(public.is_admin(), false)
            ) THEN
                RAISE EXCEPTION 'New profiles cannot be created with elevated roles.';
            END IF;
        END IF;
        RETURN NEW;
    END IF;

    -- On UPDATE: block changing primary key ID
    IF (NEW.id IS DISTINCT FROM OLD.id) THEN
        RAISE EXCEPTION 'User profile ID cannot be changed.';
    END IF;

    -- Block changing created_at
    IF (NEW.created_at IS DISTINCT FROM OLD.created_at) THEN
        RAISE EXCEPTION 'created_at timestamp cannot be changed.';
    END IF;

    -- Block changing user role unless caller is postgres, service_role, or an existing admin
    IF (NEW.role IS DISTINCT FROM OLD.role) THEN
        IF NOT (
            current_user IN ('postgres', 'supabase_admin')
            OR COALESCE(auth.jwt() ->> 'role', '') = 'service_role'
            OR COALESCE(public.is_admin(), false)
        ) THEN
            RAISE EXCEPTION 'Only administrators can change user roles.';
        END IF;
    END IF;

    -- Block direct email modifications (must be updated via Supabase Auth email change flow)
    IF (NEW.email IS DISTINCT FROM OLD.email) THEN
        IF NOT (
            current_user IN ('postgres', 'supabase_admin')
            OR COALESCE(auth.jwt() ->> 'role', '') = 'service_role'
            OR auth.uid() IS NULL -- Trigger from auth.users system sync
        ) THEN
            RAISE EXCEPTION 'Email address can only be updated through the Supabase Auth verification flow.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

DROP TRIGGER IF EXISTS trigger_enforce_profile_security ON public.profiles;
CREATE TRIGGER trigger_enforce_profile_security
BEFORE INSERT OR UPDATE ON public.profiles
FOR EACH ROW
EXECUTE FUNCTION public.enforce_profile_security();

-- 9. Secure One-Time Bootstrap Procedure for First Administrator
CREATE OR REPLACE FUNCTION public.bootstrap_first_admin(admin_email TEXT)
RETURNS TEXT AS $$
DECLARE
    admin_count INT;
    target_id UUID;
BEGIN
    -- Concurrency safeguard: Serialize concurrent bootstrap calls using a transaction-level advisory lock
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtext('resolve_ai_bootstrap_first_admin_lock'));

    -- Safeguard: Only permit bootstrap if ZERO admins currently exist
    SELECT COUNT(*) INTO admin_count FROM public.profiles WHERE role = 'admin';
    IF admin_count > 0 THEN
        RAISE EXCEPTION 'An administrator already exists. Bootstrap procedure is permanently locked.';
    END IF;

    -- Look up profile by email
    SELECT id INTO target_id FROM public.profiles WHERE email = admin_email;
    IF target_id IS NULL THEN
        RAISE EXCEPTION 'User profile with email "%" does not exist. Please sign up first.', admin_email;
    END IF;

    -- Promote designated user to admin
    UPDATE public.profiles
    SET role = 'admin', updated_at = pg_catalog.now()
    WHERE id = target_id;

    RETURN 'Success: ' || admin_email || ' has been promoted to initial Administrator.';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

REVOKE EXECUTE ON FUNCTION public.bootstrap_first_admin(TEXT) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.bootstrap_first_admin(TEXT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.bootstrap_first_admin(TEXT) TO postgres, service_role;

-- 10. Automatic Profile Creation on Supabase Auth Signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, role, theme, preferences)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', pg_catalog.split_part(NEW.email, '@', 1)),
        NEW.email,
        'agent',
        COALESCE(NEW.raw_user_meta_data->>'theme', 'system'),
        '{"notifications": true, "simple_mode": true, "compact_view": false}'::jsonb
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        full_name = COALESCE(EXCLUDED.full_name, public.profiles.full_name);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 11. Backfill existing users in auth.users
INSERT INTO public.profiles (id, full_name, email, role, theme, preferences)
SELECT 
    id,
    COALESCE(raw_user_meta_data->>'full_name', pg_catalog.split_part(email, '@', 1)),
    email,
    'agent',
    COALESCE(raw_user_meta_data->>'theme', 'system'),
    '{"notifications": true, "simple_mode": true, "compact_view": false}'::jsonb
FROM auth.users
ON CONFLICT (id) DO NOTHING;

-- 11. Row Level Security (RLS) Configuration
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ticket_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ticket_events ENABLE ROW LEVEL SECURITY;

-- 12.1 PROFILES POLICIES
DROP POLICY IF EXISTS "profiles_select_policy" ON public.profiles;
CREATE POLICY "profiles_select_policy"
ON public.profiles FOR SELECT
TO authenticated
USING (
    auth.uid() = id
    OR public.is_admin_or_manager()
);

DROP POLICY IF EXISTS "profiles_update_policy" ON public.profiles;
CREATE POLICY "profiles_update_policy"
ON public.profiles FOR UPDATE
TO authenticated
USING (
    auth.uid() = id
    OR public.is_admin()
)
WITH CHECK (
    auth.uid() = id
    OR public.is_admin()
);

DROP POLICY IF EXISTS "profiles_insert_policy" ON public.profiles;
CREATE POLICY "profiles_insert_policy"
ON public.profiles FOR INSERT
TO authenticated
WITH CHECK (
    auth.uid() = id
    AND role = 'agent'
);

DROP POLICY IF EXISTS "profiles_service_role_policy" ON public.profiles;
CREATE POLICY "profiles_service_role_policy"
ON public.profiles FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 12.2 TICKETS POLICIES
DROP POLICY IF EXISTS "tickets_select_policy" ON public.tickets;
CREATE POLICY "tickets_select_policy"
ON public.tickets FOR SELECT
TO authenticated
USING (
    user_id = auth.uid()
    OR user_id IS NULL
    OR public.is_admin_or_manager()
);

DROP POLICY IF EXISTS "tickets_insert_policy" ON public.tickets;
CREATE POLICY "tickets_insert_policy"
ON public.tickets FOR INSERT
TO authenticated
WITH CHECK (
    user_id = auth.uid()
    OR user_id IS NULL
    OR public.is_admin_or_manager()
);

DROP POLICY IF EXISTS "tickets_update_policy" ON public.tickets;
CREATE POLICY "tickets_update_policy"
ON public.tickets FOR UPDATE
TO authenticated
USING (
    user_id = auth.uid()
    OR (user_id IS NULL AND public.get_auth_user_role() = 'agent')
    OR public.is_admin_or_manager()
)
WITH CHECK (
    user_id = auth.uid()
    OR public.is_admin_or_manager()
);

DROP POLICY IF EXISTS "tickets_service_role_policy" ON public.tickets;
CREATE POLICY "tickets_service_role_policy"
ON public.tickets FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 12.3 TICKET ANALYSES POLICIES
DROP POLICY IF EXISTS "analyses_select_policy" ON public.ticket_analyses;
CREATE POLICY "analyses_select_policy"
ON public.ticket_analyses FOR SELECT
TO authenticated
USING (
    public.is_admin_or_manager()
    OR EXISTS (
        SELECT 1 FROM public.tickets t
        WHERE t.ticket_id = public.ticket_analyses.ticket_id
        AND (t.user_id = auth.uid() OR t.user_id IS NULL)
    )
);

DROP POLICY IF EXISTS "analyses_insert_policy" ON public.ticket_analyses;
CREATE POLICY "analyses_insert_policy"
ON public.ticket_analyses FOR INSERT
TO authenticated
WITH CHECK (
    public.is_admin()
);

DROP POLICY IF EXISTS "analyses_service_role_policy" ON public.ticket_analyses;
CREATE POLICY "analyses_service_role_policy"
ON public.ticket_analyses FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 12.4 TICKET EVENTS POLICIES
DROP POLICY IF EXISTS "events_select_policy" ON public.ticket_events;
CREATE POLICY "events_select_policy"
ON public.ticket_events FOR SELECT
TO authenticated
USING (
    public.is_admin_or_manager()
    OR EXISTS (
        SELECT 1 FROM public.tickets t
        WHERE t.ticket_id = public.ticket_events.ticket_id
        AND (t.user_id = auth.uid() OR t.user_id IS NULL)
    )
);

DROP POLICY IF EXISTS "events_insert_policy" ON public.ticket_events;
CREATE POLICY "events_insert_policy"
ON public.ticket_events FOR INSERT
TO authenticated
WITH CHECK (
    public.is_admin()
);

DROP POLICY IF EXISTS "events_service_role_policy" ON public.ticket_events;
CREATE POLICY "events_service_role_policy"
ON public.ticket_events FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
