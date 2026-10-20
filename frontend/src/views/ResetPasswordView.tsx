import React, { useState } from 'react';
import { Mail, Lock, ArrowLeft, ArrowRight, AlertCircle, CheckCircle, KeyRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { BrandLogo } from '../components/BrandLogo';

interface ResetPasswordViewProps {
  onNavigate: (view: string) => void;
  isRecoveryMode?: boolean;
}

export const ResetPasswordView: React.FC<ResetPasswordViewProps> = ({
  onNavigate,
  isRecoveryMode = false,
}) => {
  const { resetPasswordForEmail, updatePassword } = useAuth();
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setErrorMessage('Please enter your email address.');
      return;
    }

    setLoading(true);
    try {
      const { error } = await resetPasswordForEmail(cleanEmail);
      if (error) {
        setErrorMessage(error.message || "We couldn't send the password reset email. Please try again.");
      } else {
        setSuccessMessage(
          'Password reset email sent! Check your inbox for a link to choose a new password.'
        );
      }
    } catch (err: any) {
      setErrorMessage('Something went wrong. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSetNewPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!newPassword || newPassword.length < 6) {
      setErrorMessage('Your new password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('The passwords do not match. Please re-type your new password.');
      return;
    }

    setLoading(true);
    try {
      const { error } = await updatePassword(newPassword);
      if (error) {
        setErrorMessage(error.message || "Couldn't update your password. Please try again.");
      } else {
        setSuccessMessage('Your password has been changed! Redirecting to login...');
        setTimeout(() => {
          onNavigate('login');
        }, 1200);
      }
    } catch (err: any) {
      setErrorMessage('Something went wrong updating your password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <BrandLogo size="lg" showBadge={false} showTagline={false} />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {isRecoveryMode ? 'Set a New Password' : 'Reset Your Password'}
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            {isRecoveryMode
              ? 'Enter your new password below to regain access to your account.'
              : 'Enter your email address and we will send you a link to reset your password.'}
          </p>
        </div>

        <div className="saas-card p-6 sm:p-8 shadow-sm">
          {isRecoveryMode ? (
            <form className="space-y-4" onSubmit={handleSetNewPassword}>
              {errorMessage && (
                <div className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-sm flex items-start space-x-2.5">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600 dark:text-rose-400" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {successMessage && (
                <div className="p-3.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300 text-sm flex items-start space-x-2.5">
                  <CheckCircle className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  <span>{successMessage}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider">
                  New Password
                </label>
                <div className="relative flex items-center">
                  <div
                    className="absolute inset-y-0 left-0 w-12 flex items-center justify-center pointer-events-none text-slate-400 dark:text-slate-500"
                    aria-hidden="true"
                  >
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter at least 6 characters"
                    className="saas-input saas-input-with-icon-left"
                    style={{ paddingLeft: '48px' }}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider">
                  Confirm New Password
                </label>
                <div className="relative flex items-center">
                  <div
                    className="absolute inset-y-0 left-0 w-12 flex items-center justify-center pointer-events-none text-slate-400 dark:text-slate-500"
                    aria-hidden="true"
                  >
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-type your new password"
                    className="saas-input saas-input-with-icon-left"
                    style={{ paddingLeft: '48px' }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 transition-colors focus-ring"
              >
                {loading ? 'Updating Password...' : 'Save New Password'}
              </button>
            </form>
          ) : (
            <form className="space-y-4" onSubmit={handleRequestReset}>
              {errorMessage && (
                <div className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-sm flex items-start space-x-2.5">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600 dark:text-rose-400" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {successMessage && (
                <div className="p-3.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300 text-sm flex items-start space-x-2.5">
                  <CheckCircle className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  <span>{successMessage}</span>
                </div>
              )}

              <div>
                <label
                  htmlFor="reset-email"
                  className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider"
                >
                  Your Email Address
                </label>
                <div className="relative flex items-center">
                  <div
                    className="absolute inset-y-0 left-0 w-12 flex items-center justify-center pointer-events-none text-slate-400 dark:text-slate-500"
                    aria-hidden="true"
                  >
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    id="reset-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="saas-input saas-input-with-icon-left"
                    style={{ paddingLeft: '48px' }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 transition-colors focus-ring"
              >
                {loading ? 'Sending link...' : 'Send Reset Instructions'}
              </button>
            </form>
          )}

          <div className="mt-6 pt-5 border-t border-slate-200 dark:border-slate-800 text-center">
            <button
              onClick={() => onNavigate('login')}
              className="inline-flex items-center space-x-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 hover:underline focus-ring rounded"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
