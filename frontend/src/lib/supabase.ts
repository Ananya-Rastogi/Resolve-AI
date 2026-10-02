import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Retrieve Supabase environment variables from Vite
// Support VITE_SUPABASE_PUBLISHABLE_KEY or fallback to VITE_SUPABASE_ANON_KEY
const rawUrl = (import.meta.env.VITE_SUPABASE_URL || '').trim();
// Ensure no trailing /rest/v1 or trailing slash
const supabaseUrl = rawUrl.replace(/\/rest\/v1\/?$/, '').replace(/\/+$/, '');
const supabaseKey = (
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  ''
).trim();

export const isSupabaseConfigured = Boolean(
  supabaseUrl &&
  supabaseKey &&
  !supabaseUrl.includes('placeholder') &&
  !supabaseKey.includes('placeholder') &&
  !supabaseUrl.includes('your-project-ref') &&
  !supabaseKey.includes('your-supabase')
);

if (!isSupabaseConfigured) {
  console.warn(
    '[Resolve AI] Supabase configuration missing or incomplete. ' +
    'Please set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in frontend/.env.local'
  );
}

// Create client with browser localStorage session persistence
export const supabase: SupabaseClient = createClient(
  supabaseUrl || 'https://placeholder-project.supabase.co',
  supabaseKey || 'placeholder-anon-key',
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storage: window.localStorage,
    },
  }
);
