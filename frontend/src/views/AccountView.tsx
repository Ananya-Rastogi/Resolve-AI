import React, { useState } from 'react';
import {
  User,
  Mail,
  Shield,
  Calendar,
  Lock,
  Edit2,
  Check,
  X,
  LogOut,
  AlertCircle,
  CheckCircle,
  KeyRound,
  Info,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface AccountViewProps {
  onNavigate: (view: string) => void;
}

export const AccountView: React.FC<AccountViewProps> = ({ onNavigate }) => {
  const { user, profile, updateProfile, updatePassword, signOut } = useAuth();

  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(profile?.full_name || user?.user_metadata?.full_name || '');
  const [profileMessage, setProfileMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  // Password update form state
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [savingPassword, setSavingPassword] = useState(false);

  const userEmail = profile?.email || user?.email || 'agent@resolve-ai.local';
  const displayName = profile?.full_name || user?.user_metadata?.full_name || userEmail.split('@')[0] || 'Support Agent';
  const roleName = profile?.role === 'admin' ? 'Administrator' : profile?.role === 'manager' ? 'Team Lead' : 'Support Specialist';

  // Initials for avatar
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0].toUpperCase())
    .join('') || 'SP';

  const createdAt = user?.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Active since setup';

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMessage(null);
    setSavingProfile(true);

    try {
      const { error } = await updateProfile({ fullName: fullName.trim() });
      if (error) {
        setProfileMessage({ type: 'error', text: "Your changes couldn't be saved. Please try again." });
      } else {
        setProfileMessage({ type: 'success', text: 'Profile updated successfully!' });
        setIsEditing(false);
      }
    } catch (err: any) {
      setProfileMessage({ type: 'error', text: 'Error saving profile details.' });
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);

    if (newPassword.length < 6) {
      setPasswordMessage({ type: 'error', text: 'Password must be at least 6 characters long.' });
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: 'error', text: 'The new passwords do not match. Please re-enter them.' });
      return;
    }

    setSavingPassword(true);
    try {
      const { error } = await updatePassword(newPassword);
      if (error) {
        setPasswordMessage({ type: 'error', text: error.message || "We couldn't update your password." });
      } else {
        setPasswordMessage({ type: 'success', text: 'Password changed successfully!' });
        setNewPassword('');
        setConfirmPassword('');
        setShowPasswordChange(false);
      }
    } catch (err: any) {
      setPasswordMessage({ type: 'error', text: 'Failed to update password.' });
    } finally {
      setSavingPassword(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Account Details
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          Manage your personal profile, credentials, and security settings
        </p>
      </div>

      {/* Main Profile Card */}
      <div className="saas-card p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white text-xl font-bold shadow-md ring-4 ring-indigo-50 dark:ring-indigo-950">
              {initials}
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  {displayName}
                </h2>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  {roleName}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex items-center space-x-1.5">
                <Mail className="w-3.5 h-3.5" />
                <span>{userEmail}</span>
              </p>
            </div>
          </div>

          {!isEditing && (
            <button
              onClick={() => {
                setFullName(displayName);
                setIsEditing(true);
              }}
              className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition focus-ring"
            >
              <Edit2 className="w-3.5 h-3.5" />
              <span>Edit Profile</span>
            </button>
          )}
        </div>

        {/* Profile Alert */}
        {profileMessage && (
          <div
            className={`p-3.5 rounded-lg text-sm flex items-start space-x-2.5 ${
              profileMessage.type === 'success'
                ? 'bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300'
                : 'bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300'
            }`}
          >
            {profileMessage.type === 'success' ? (
              <CheckCircle className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600 dark:text-rose-400" />
            )}
            <span>{profileMessage.text}</span>
          </div>
        )}

        {/* Profile Edit Form / Static Details */}
        {isEditing ? (
          <form onSubmit={handleSaveProfile} className="space-y-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wider">
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="saas-input max-w-md"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wider">
                Email Address
              </label>
              <input
                type="email"
                disabled
                value={userEmail}
                className="saas-input max-w-md bg-slate-100 dark:bg-slate-800/50 cursor-not-allowed opacity-75"
              />
              <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400 flex items-center space-x-1">
                <Info className="w-3.5 h-3.5" />
                <span>To change your work email address, contact your system administrator for security verification.</span>
              </p>
            </div>

            <div className="flex items-center space-x-2.5 pt-2">
              <button
                type="submit"
                disabled={savingProfile}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition focus-ring disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
                <span>{savingProfile ? 'Saving...' : 'Save Changes'}</span>
              </button>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition focus-ring"
              >
                <X className="w-3.5 h-3.5" />
                <span>Cancel</span>
              </button>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800/60">
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Your Role</span>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 mt-1 flex items-center space-x-1.5">
                <Shield className="w-4 h-4 text-indigo-500" />
                <span>{roleName}</span>
              </p>
            </div>
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800/60">
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Member Since</span>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 mt-1 flex items-center space-x-1.5">
                <Calendar className="w-4 h-4 text-indigo-500" />
                <span>{createdAt}</span>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Security & Password Card */}
      <div className="saas-card p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <KeyRound className="w-5 h-5 text-indigo-500" />
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Password & Security
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Update your login password to keep your account safe
              </p>
            </div>
          </div>
          {!showPasswordChange && (
            <button
              onClick={() => setShowPasswordChange(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 border border-indigo-200 dark:border-indigo-800 transition focus-ring"
            >
              Change Password
            </button>
          )}
        </div>

        {passwordMessage && (
          <div
            className={`p-3.5 rounded-lg text-sm flex items-start space-x-2.5 ${
              passwordMessage.type === 'success'
                ? 'bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300'
                : 'bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300'
            }`}
          >
            {passwordMessage.type === 'success' ? (
              <CheckCircle className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600 dark:text-rose-400" />
            )}
            <span>{passwordMessage.text}</span>
          </div>
        )}

        {showPasswordChange && (
          <form onSubmit={handlePasswordChange} className="space-y-4 pt-3 border-t border-slate-200 dark:border-slate-800">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wider">
                New Password (minimum 6 characters)
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                className="saas-input max-w-md"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wider">
                Confirm New Password
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-type new password"
                className="saas-input max-w-md"
              />
            </div>

            <div className="flex items-center space-x-2.5">
              <button
                type="submit"
                disabled={savingPassword}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition focus-ring disabled:opacity-50"
              >
                {savingPassword ? 'Updating Password...' : 'Save New Password'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowPasswordChange(false);
                  setPasswordMessage(null);
                }}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition focus-ring"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Sign Out Card */}
      <div className="saas-card p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-rose-200/50 dark:border-rose-950/50 bg-rose-50/20 dark:bg-rose-950/10">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Sign out of your session
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            You will need to sign back in with your credentials to access tickets and settings.
          </p>
        </div>
        <button
          onClick={async () => {
            await signOut();
            onNavigate('login');
          }}
          className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50 hover:bg-rose-100 dark:hover:bg-rose-900/50 border border-rose-200 dark:border-rose-800/80 transition focus-ring"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
};
