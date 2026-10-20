import React, { useState } from 'react';
import { Mail, Lock, User, Eye, EyeOff, ArrowRight, AlertCircle, CheckCircle, Database } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { BrandLogo } from '../components/BrandLogo';

interface SignUpViewProps {
  onNavigate: (view: string) => void;
}

export const SignUpView: React.FC<SignUpViewProps> = ({ onNavigate }) => {
  const { signUp, isConfigured } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const cleanName = fullName.trim();
    const cleanEmail = email.trim();

    if (!cleanName || !cleanEmail || !password || !confirmPassword) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Your password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('The passwords do not match. Please re-type your password.');
      return;
    }

    setLoading(true);
    try {
      const { error, needsEmailConfirmation } = await signUp(cleanEmail, password, cleanName);

      if (error) {
        const msg = error.message.toLowerCase();
        if (msg.includes('user already registered') || msg.includes('already exists')) {
          setErrorMessage('An account with this email address already exists. Try signing in instead.');
        } else {
          setErrorMessage(error.message || "We couldn't create your account. Please try again.");
        }
        setLoading(false);
        return;
      }

      if (needsEmailConfirmation) {
        setSuccessMessage(
          'Account created! We sent a confirmation link to your email. Please click the link in your inbox to verify your account.'
        );
        setLoading(false);
      } else {
        setSuccessMessage('Account created successfully! Taking you to the dashboard...');
        setTimeout(() => {
          onNavigate('dashboard');
        }, 600);
      }
    } catch (err: any) {
      setErrorMessage("Something went wrong while setting up your account. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <BrandLogo size="lg" showBadge={false} showTagline={false} />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Create your account
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Join your customer support team on Resolve AI
          </p>
        </div>

        {/* Local mode indicator */}
        {!isConfigured && (
          <div className="p-3.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs flex items-start space-x-2.5">
            <Database className="w-4 h-4 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" />
            <div>
              <p className="font-semibold">Local Development Mode Active</p>
              <p className="mt-0.5 text-amber-700 dark:text-amber-300/80">
                Accounts created locally are stored for testing without requiring Supabase email verification.
              </p>
            </div>
          </div>
        )}

        {/* Card Form */}
        <div className="saas-card p-6 sm:p-8 shadow-sm">
          <form className="space-y-4" onSubmit={handleSubmit}>
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

            {/* Full Name */}
            <div>
              <label
                htmlFor="signup-name"
                className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider"
              >
                Full Name
              </label>
              <div className="relative flex items-center">
                <div
                  className="absolute inset-y-0 left-0 w-12 flex items-center justify-center pointer-events-none text-slate-400 dark:text-slate-500"
                  aria-hidden="true"
                >
                  <User className="w-4 h-4" />
                </div>
                <input
                  id="signup-name"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Jane Doe"
                  className="saas-input saas-input-with-icon-left"
                  style={{ paddingLeft: '48px' }}
                />
              </div>
            </div>

            {/* Email Address */}
            <div>
              <label
                htmlFor="signup-email"
                className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider"
              >
                Work Email Address
              </label>
              <div className="relative flex items-center">
                <div
                  className="absolute inset-y-0 left-0 w-12 flex items-center justify-center pointer-events-none text-slate-400 dark:text-slate-500"
                  aria-hidden="true"
                >
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="signup-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="saas-input saas-input-with-icon-left"
                  style={{ paddingLeft: '48px' }}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="signup-password"
                className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider"
              >
                Password (min 6 characters)
              </label>
              <div className="relative flex items-center">
                <div
                  className="absolute inset-y-0 left-0 w-12 flex items-center justify-center pointer-events-none text-slate-400 dark:text-slate-500"
                  aria-hidden="true"
                >
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="signup-password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Choose a strong password"
                  className="saas-input saas-input-with-icons"
                  style={{ paddingLeft: '48px', paddingRight: '48px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 focus:outline-none focus:text-indigo-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="signup-confirm-password"
                className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider"
              >
                Confirm Password
              </label>
              <div className="relative flex items-center">
                <div
                  className="absolute inset-y-0 left-0 w-12 flex items-center justify-center pointer-events-none text-slate-400 dark:text-slate-500"
                  aria-hidden="true"
                >
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="signup-confirm-password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-type your password"
                  className="saas-input saas-input-with-icon-left"
                  style={{ paddingLeft: '48px' }}
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors focus-ring"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Creating your account...</span>
                  </>
                ) : (
                  <>
                    <span>Create Account</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Link to Login */}
          <div className="mt-6 pt-5 border-t border-slate-200 dark:border-slate-800 text-center">
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Already have an account?{' '}
              <button
                onClick={() => onNavigate('login')}
                className="font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 hover:underline focus-ring rounded"
              >
                Sign in here
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
