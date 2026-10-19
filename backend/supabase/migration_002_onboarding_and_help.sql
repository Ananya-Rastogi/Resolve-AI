-- ==============================================================================
-- Resolve AI: Migration 002 - User Onboarding Status & Preferences Hardening
-- Run this migration in the Supabase SQL Editor if a dedicated column is preferred.
--
-- Note: Resolve AI user profile preferences (JSONB) seamlessly persist onboarding
-- state ({ "onboarding_completed": true, "onboarding_skipped": false }) out-of-the-box.
-- This migration provides optional dedicated columns and performance indexes.
--
-- Security Controls:
--  1. Retains all existing profiles and RLS security policies.
--  2. Safe & Idempotent: Can be run multiple times without data loss or downtime.
-- ==============================================================================

-- 1. Ensure onboarding column exists on public.profiles (optional fast-path)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'profiles'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'onboarding_completed'
        ) THEN
            ALTER TABLE public.profiles ADD COLUMN onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;
        END IF;
    END IF;
END $$;

-- 2. Add GIN index on preferences JSONB for efficient key queries
CREATE INDEX IF NOT EXISTS idx_profiles_preferences_gin ON public.profiles USING GIN (preferences);
