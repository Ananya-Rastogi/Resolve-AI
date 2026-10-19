import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../lib/supabase';
import { UserProfile, ThemeMode } from '../types';
import { useTheme } from './ThemeContext';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: UserProfile | null;
  loading: boolean;
  isConfigured: boolean;
  welcomeMessage: string | null;
  setWelcomeMessage: (msg: string | null) => void;
  signIn: (email: string, password: string, rememberMe?: boolean) => Promise<{ error: Error | null }>;
  signUp: (email: string, password: string, fullName: string) => Promise<{ error: Error | null; needsEmailConfirmation?: boolean }>;
  signOut: () => Promise<void>;
  resetPasswordForEmail: (email: string) => Promise<{ error: Error | null }>;
  updatePassword: (newPassword: string) => Promise<{ error: Error | null }>;
  updateProfile: (updates: { fullName?: string; avatarUrl?: string; theme?: ThemeMode; preferences?: any }) => Promise<{ error: Error | null }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [welcomeMessage, setWelcomeMessage] = useState<string | null>(null);
  const { setTheme } = useTheme();

  // Load user profile from Supabase profiles table
  const fetchProfile = async (currentUser: User) => {
    if (!isSupabaseConfigured) {
      const mockProfile: UserProfile = {
        id: currentUser.id,
        email: currentUser.email || 'agent@resolve-ai.local',
        full_name: (currentUser.user_metadata?.full_name as string) || 'Support Specialist',
        role: 'agent',
        theme: 'system',
        preferences: { notifications: true, simple_mode: true, compact_view: false },
      };
      setProfile(mockProfile);
      return;
    }

    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', currentUser.id)
        .single();

      if (error && error.code !== 'PGRST116') {
        console.warn('Error fetching user profile from Supabase:', error.message);
      }

      if (data) {
        setProfile(data as UserProfile);
        if (data.theme && ['light', 'dark', 'system'].includes(data.theme)) {
          setTheme(data.theme as ThemeMode);
        }
      } else {
        // Automatically create fallback profile if not found
        const newProfile: Partial<UserProfile> = {
          id: currentUser.id,
          email: currentUser.email || '',
          full_name: (currentUser.user_metadata?.full_name as string) || currentUser.email?.split('@')[0] || 'Support Specialist',
          role: 'agent',
          theme: 'system',
          preferences: { notifications: true, simple_mode: true, compact_view: false },
        };
        await supabase.from('profiles').upsert(newProfile);
        setProfile(newProfile as UserProfile);
      }
    } catch (err) {
      console.warn('Exception fetching profile:', err);
    }
  };

  useEffect(() => {
    let mounted = true;

    async function initAuth() {
      try {
        if (!isSupabaseConfigured) {
          // If Supabase is not configured, check for local dev session or finish loading
          const localSavedUser = localStorage.getItem('resolve_local_user');
          if (localSavedUser) {
            try {
              const parsed = JSON.parse(localSavedUser);
              if (mounted) {
                setUser(parsed);
                fetchProfile(parsed);
              }
            } catch (e) {
              localStorage.removeItem('resolve_local_user');
            }
          }
          if (mounted) setLoading(false);
          return;
        }

        const { data: { session: initialSession } } = await supabase.auth.getSession();
        if (mounted) {
          setSession(initialSession);
          setUser(initialSession?.user ?? null);
          if (initialSession?.user) {
            localStorage.setItem('resolve_local_user', JSON.stringify({
              id: initialSession.user.id,
              email: initialSession.user.email,
              user_metadata: initialSession.user.user_metadata,
            }));
            await fetchProfile(initialSession.user);
          }
          setLoading(false);
        }
      } catch (err) {
        console.error('Error during initial auth check:', err);
        if (mounted) setLoading(false);
      }
    }

    initAuth();

    // Listen for auth state transitions
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        if (!mounted) return;
        setSession(newSession);
        setUser(newSession?.user ?? null);

        if (event === 'SIGNED_IN' && newSession?.user) {
          localStorage.setItem('resolve_local_user', JSON.stringify({
            id: newSession.user.id,
            email: newSession.user.email,
            user_metadata: newSession.user.user_metadata,
          }));
          await fetchProfile(newSession.user);
          const userName =
            (newSession.user.user_metadata?.full_name as string) ||
            newSession.user.email?.split('@')[0] ||
            'Team Member';
          setWelcomeMessage(`Welcome back, ${userName}! Ready to resolve tickets.`);
        } else if (event === 'SIGNED_OUT') {
          localStorage.removeItem('resolve_local_user');
          setProfile(null);
          setWelcomeMessage(null);
        } else if (event === 'TOKEN_REFRESHED' && newSession?.user) {
          localStorage.setItem('resolve_local_user', JSON.stringify({
            id: newSession.user.id,
            email: newSession.user.email,
            user_metadata: newSession.user.user_metadata,
          }));
          await fetchProfile(newSession.user);
        }
      }
    );

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string, rememberMe = true) => {
    if (!isSupabaseConfigured) {
      // Local dev mode fallback if Supabase credentials are missing
      const mockUser = {
        id: 'local-dev-user-001',
        email,
        user_metadata: { full_name: email.split('@')[0] || 'Local Specialist' },
      } as unknown as User;
      setUser(mockUser);
      localStorage.setItem('resolve_local_user', JSON.stringify(mockUser));
      await fetchProfile(mockUser);
      setWelcomeMessage(`Welcome back! You are in local development mode.`);
      return { error: null };
    }

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) {
        return { error };
      }
      if (data.user) {
        await fetchProfile(data.user);
      }
      return { error: null };
    } catch (err: any) {
      return { error: err };
    }
  };

  const signUp = async (email: string, password: string, fullName: string) => {
    if (!isSupabaseConfigured) {
      const mockUser = {
        id: 'local-dev-user-001',
        email,
        user_metadata: { full_name: fullName },
      } as unknown as User;
      setUser(mockUser);
      localStorage.setItem('resolve_local_user', JSON.stringify(mockUser));
      await fetchProfile(mockUser);
      setWelcomeMessage(`Welcome to Resolve AI, ${fullName}! Your account has been created.`);
      return { error: null, needsEmailConfirmation: false };
    }

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      });

      if (error) {
        return { error };
      }

      // Check if email confirmation is required
      const needsEmailConfirmation = Boolean(data.user && !data.session);
      if (data.user && data.session) {
        try {
          await supabase.from('profiles').upsert({
            id: data.user.id,
            email: data.user.email || email,
            full_name: fullName,
            role: 'agent',
            theme: 'system',
            preferences: { notifications: true, simple_mode: true, compact_view: false },
          });
        } catch (e) {
          // Ignore if trigger handled it
        }
        await fetchProfile(data.user);
      }

      return { error: null, needsEmailConfirmation };
    } catch (err: any) {
      return { error: err };
    }
  };

  const signOut = async () => {
    localStorage.removeItem('resolve_local_user');
    if (!isSupabaseConfigured) {
      setUser(null);
      setSession(null);
      setProfile(null);
      return;
    }
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
    setProfile(null);
  };

  const resetPasswordForEmail = async (email: string) => {
    if (!isSupabaseConfigured) {
      return { error: null };
    }
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/#reset-password`,
      });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const updatePassword = async (newPassword: string) => {
    if (!isSupabaseConfigured) {
      return { error: null };
    }
    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const updateProfile = async (updates: {
    fullName?: string;
    avatarUrl?: string;
    theme?: ThemeMode;
    preferences?: any;
  }) => {
    if (!user) {
      return { error: new Error('User not logged in') };
    }

    try {
      const payload: Record<string, any> = {
        updated_at: new Date().toISOString(),
      };
      if (updates.fullName !== undefined) payload.full_name = updates.fullName;
      if (updates.avatarUrl !== undefined) payload.avatar_url = updates.avatarUrl;
      if (updates.theme !== undefined) {
        payload.theme = updates.theme;
        setTheme(updates.theme);
      }
      if (updates.preferences !== undefined) payload.preferences = updates.preferences;

      if (isSupabaseConfigured) {
        const { error } = await supabase
          .from('profiles')
          .update(payload)
          .eq('id', user.id);

        if (error) {
          return { error };
        }
      }

      // Also update auth user metadata if full name changed
      if (updates.fullName && isSupabaseConfigured) {
        await supabase.auth.updateUser({
          data: { full_name: updates.fullName },
        });
      }

      setProfile((prev) => (prev ? { ...prev, ...payload } : null));
      return { error: null };
    } catch (err: any) {
      return { error: err };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        loading,
        isConfigured: isSupabaseConfigured,
        welcomeMessage,
        setWelcomeMessage,
        signIn,
        signUp,
        signOut,
        resetPasswordForEmail,
        updatePassword,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
