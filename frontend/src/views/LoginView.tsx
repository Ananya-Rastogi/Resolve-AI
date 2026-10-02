import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, ArrowRight, AlertCircle, CheckCircle, Database } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { BrandLogo } from '../components/BrandLogo';

interface LoginViewProps {
  onNavigate: (view: string) => void;
  onForgotPassword?: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onNavigate, onForgotPassword }) => {
  const handleForgotClick = () => {
    if (onForgotPassword) {
      onForgotPassword();
    } else {
      onNavigate('reset-password');
    }
  };
  const { signIn, isConfigured } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setErrorMessage('Please enter both your email address and password.');
      return;
    }

    setLoading(true);
    try {
      const { error } = await signIn(cleanEmail, password, rememberMe);
      if (error) {
        // User-friendly plain English error messages
        const msg = error.message.toLowerCase();
        if (msg.includes('invalid login credentials') || msg.includes('invalid credentials')) {
          setErrorMessage("We couldn't sign you in. Please check your email and password.");
        } else if (msg.includes('email not confirmed')) {
          setErrorMessage('Please confirm your email address before signing in. Check your inbox for the confirmation link.');
        } else {
          setErrorMessage(error.message || "We couldn't sign you in. Please check your connection and try again.");
        }
        setLoading(false);
        return;
      }

      setSuccessMessage('Signed in successfully! Redirecting to your dashboard...');
      setTimeout(() => {
        onNavigate('dashboard');
      }, 500);
    } catch (err: any) {
      setErrorMessage("Something went wrong during sign in. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Brand Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <BrandLogo size="lg" showBadge={false} showTagline={false} />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Sign in to Resolve AI
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Intelligent customer support ticket triage and multi-agent resolution
          </p>
        </div>

        {/* Missing Supabase configuration banner (Non-misleading) */}
        {!isConfigured && (
          <div className="p-3.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs flex items-start space-x-2.5">
            <Database className="w-4 h-4 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" />
            <div>
              <p className="font-semibold">Local Development Mode Active</p>
              <p className="mt-0.5 text-amber-700 dark:text-amber-300/80">
                Supabase credentials (<code className="font-mono">VITE_SUPABASE_URL</code>) are not configured. You can sign in locally with any email and password for offline testing.
              </p>
            </div>
          </div>
        )}

        {/* Card Form */}
        <div className="saas-card p-6 sm:p-8 shadow-sm">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* Error Banner */}
            {errorMessage && (
              <div
                className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-sm flex items-start space-x-2.5"
                role="alert"
              >
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600 dark:text-rose-400" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success Banner */}
            {successMessage && (
              <div
                className="p-3.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300 text-sm flex items-start space-x-2.5"
                role="alert"
              >
                <CheckCircle className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span>{successMessage}</span>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label
                htmlFor="login-email"
                className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider"
              >
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="login-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="saas-input pl-10"
                />
              </div>
            </div>

            {/* Password Field with Show/Hide */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="login-password"
                  className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider"
                >
                  Password
                </label>
                <button
                  type="button"
                  onClick={handleForgotClick}
                  className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 hover:underline focus-ring rounded"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="saas-input pl-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 focus:outline-none"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded text-indigo-600 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:ring-indigo-500 focus:ring-offset-0 cursor-pointer"
              />
              <label
                htmlFor="remember-me"
                className="ml-2 block text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none"
              >
                Remember me on this device
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors focus-ring"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Footer Link to Sign Up */}
          <div className="mt-6 pt-5 border-t border-slate-200 dark:border-slate-800 text-center">
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Don't have an account yet?{' '}
              <button
                onClick={() => onNavigate('signup')}
                className="font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 hover:underline focus-ring rounded"
              >
                Create a new account
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
