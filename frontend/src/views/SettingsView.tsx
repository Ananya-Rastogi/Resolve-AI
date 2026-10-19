import React, { useState } from 'react';
import {
  Sun,
  Moon,
  Laptop,
  Check,
  Bell,
  HelpCircle,
  List,
  User,
  Shield,
  Save,
  CheckCircle,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { ThemeMode } from '../types';

interface SettingsViewProps {
  onNavigate: (view: string) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onNavigate }) => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const { profile, updateProfile, signOut } = useAuth();

  const [soundAlerts, setSoundAlerts] = useState<boolean>(
    profile?.preferences?.notifications ?? true
  );
  const [simpleMode, setSimpleMode] = useState<boolean>(
    profile?.preferences?.simple_mode ?? true
  );
  const [compactView, setCompactView] = useState<boolean>(
    profile?.preferences?.compact_view ?? false
  );

  const [savingPrefs, setSavingPrefs] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const themeOptions: Array<{
    id: ThemeMode;
    label: string;
    description: string;
    icon: React.ElementType;
  }> = [
    {
      id: 'light',
      label: 'Light theme',
      description: 'Clean bright look with high contrast text for daytime work.',
      icon: Sun,
    },
    {
      id: 'dark',
      label: 'Dark theme',
      description: 'Gentle dark colors that reduce eye fatigue in low light.',
      icon: Moon,
    },
    {
      id: 'system',
      label: 'System theme',
      description: 'Matches your computer or operating system settings automatically.',
      icon: Laptop,
    },
  ];

  const handleSelectTheme = async (selected: ThemeMode) => {
    setTheme(selected);
    try {
      await updateProfile({ theme: selected });
    } catch (e) {
      console.warn('Could not sync theme with account profile:', e);
    }
  };

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPrefs(true);
    setSaveStatus(null);

    try {
      const updatedPrefs = {
        notifications: soundAlerts,
        simple_mode: simpleMode,
        compact_view: compactView,
      };

      const { error } = await updateProfile({
        preferences: updatedPrefs,
      });

      if (error) {
        setSaveStatus('error');
      } else {
        setSaveStatus('success');
        setTimeout(() => setSaveStatus(null), 3000);
      }
    } catch (err) {
      setSaveStatus('error');
    } finally {
      setSavingPrefs(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Preferences & Settings
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          Customize your display appearance, helpful explanations, and interface settings
        </p>
      </div>

      {/* 1. Appearance Section */}
      <div className="saas-card p-6 sm:p-8 space-y-5">
        <div className="pb-3 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-2">
            <span>Website Appearance</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Choose how Resolve AI looks to you. Your theme selection stays saved across sessions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {themeOptions.map((opt) => {
            const Icon = opt.icon;
            const isSelected = theme === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => handleSelectTheme(opt.id)}
                className={`relative flex flex-col items-start p-4 rounded-xl border text-left transition-all focus-ring ${
                  isSelected
                    ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/30 ring-2 ring-indigo-500/20 shadow-sm'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-3">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                      isSelected
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  {isSelected && (
                    <span className="flex items-center space-x-1 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-100/70 dark:bg-indigo-900/50 px-2 py-0.5 rounded-full">
                      <Check className="w-3 h-3" />
                      <span>Active</span>
                    </span>
                  )}
                </div>

                <span className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-1">
                  {opt.label}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  {opt.description}
                </span>
              </button>
            );
          })}
        </div>

        <div className="pt-2 text-xs text-slate-500 dark:text-slate-400 flex items-center space-x-2">
          <span>Currently displaying:</span>
          <span className="font-semibold text-slate-700 dark:text-slate-300 capitalize">
            {resolvedTheme} Mode
          </span>
        </div>
      </div>

      {/* 2. Helpful Preferences Section */}
      <div className="saas-card p-6 sm:p-8 space-y-5">
        <div className="pb-3 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Work Preferences
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Turn helpful alerts and simple explanations on or off
          </p>
        </div>

        {saveStatus === 'success' && (
          <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300 text-xs flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
            <span>Your preferences have been saved to your account.</span>
          </div>
        )}

        {saveStatus === 'error' && (
          <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
            <span>Could not save preferences. Please check your connection and try again.</span>
          </div>
        )}

        <form onSubmit={handleSavePreferences} className="space-y-4">
          {/* Toggle 1: High priority alerts */}
          <label className="flex items-start justify-between p-3.5 rounded-lg border border-slate-200 dark:border-slate-800/80 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition cursor-pointer">
            <div className="flex items-start space-x-3 pr-4">
              <Bell className="w-5 h-5 text-indigo-500 mt-0.5 shrink-0" />
              <div>
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 block">
                  Urgent ticket alerts
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 block mt-0.5">
                  Play a friendly sound or show a desktop notification when high priority tickets arrive
                </span>
              </div>
            </div>
            <input
              type="checkbox"
              checked={soundAlerts}
              onChange={(e) => setSoundAlerts(e.target.checked)}
              className="w-4 h-4 mt-1 rounded text-indigo-600 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:ring-indigo-500 focus:ring-offset-0 cursor-pointer"
            />
          </label>

          {/* Toggle 2: Simple English AI Explanations */}
          <label className="flex items-start justify-between p-3.5 rounded-lg border border-slate-200 dark:border-slate-800/80 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition cursor-pointer">
            <div className="flex items-start space-x-3 pr-4">
              <HelpCircle className="w-5 h-5 text-indigo-500 mt-0.5 shrink-0" />
              <div>
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 block">
                  Show simple English explanations
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 block mt-0.5">
                  Include friendly descriptions next to AI confidence scores, model categories, and customer moods
                </span>
              </div>
            </div>
            <input
              type="checkbox"
              checked={simpleMode}
              onChange={(e) => setSimpleMode(e.target.checked)}
              className="w-4 h-4 mt-1 rounded text-indigo-600 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:ring-indigo-500 focus:ring-offset-0 cursor-pointer"
            />
          </label>

          {/* Toggle 3: Compact view */}
          <label className="flex items-start justify-between p-3.5 rounded-lg border border-slate-200 dark:border-slate-800/80 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition cursor-pointer">
            <div className="flex items-start space-x-3 pr-4">
              <List className="w-5 h-5 text-indigo-500 mt-0.5 shrink-0" />
              <div>
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 block">
                  Compact ticket list view
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 block mt-0.5">
                  Display more tickets on screen with smaller row heights in the ticket queue
                </span>
              </div>
            </div>
            <input
              type="checkbox"
              checked={compactView}
              onChange={(e) => setCompactView(e.target.checked)}
              className="w-4 h-4 mt-1 rounded text-indigo-600 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:ring-indigo-500 focus:ring-offset-0 cursor-pointer"
            />
          </label>

          <div className="pt-2">
            <button
              type="submit"
              disabled={savingPrefs}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition focus-ring disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{savingPrefs ? 'Saving preferences...' : 'Save Preferences'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* 3. Account and Security Quick Access */}
      <div className="saas-card p-6 sm:p-8 space-y-4">
        <div className="pb-3 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Account & Security
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Quick shortcuts to your personal account profile and credentials
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => onNavigate('account')}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition focus-ring"
          >
            <User className="w-3.5 h-3.5" />
            <span>Open Account Page</span>
          </button>

          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('resolve-open-tour'))}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-500/10 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 border border-indigo-200 dark:border-indigo-500/30 transition focus-ring"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            <span>Replay Onboarding Tour</span>
          </button>

          <button
            onClick={() => onNavigate('account')}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 border border-indigo-200 dark:border-indigo-800 transition focus-ring"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Change Password</span>
          </button>

          <button
            onClick={async () => {
              await signOut();
              onNavigate('login');
            }}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50 hover:bg-rose-100 dark:hover:bg-rose-900/50 border border-rose-200 dark:border-rose-800 transition focus-ring"
          >
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );
};
