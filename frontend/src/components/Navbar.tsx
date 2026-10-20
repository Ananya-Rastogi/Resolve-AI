import React, { useState, useRef, useEffect } from 'react';
import {
  LayoutDashboard,
  PlusCircle,
  ListOrdered,
  BarChart3,
  Database,
  RefreshCw,
  Sun,
  Moon,
  Laptop,
  User as UserIcon,
  Settings as SettingsIcon,
  LogOut,
  ChevronDown,
  Menu,
  X,
  LogIn,
  UserPlus,
} from 'lucide-react';
import { HealthResponse } from '../types';
import { BrandLogo } from './BrandLogo';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

interface NavbarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  health: HealthResponse | null;
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  onNavigate,
  health,
  onRefreshHealth,
}) => {
  const { user, profile, signOut } = useAuth();
  const { theme, resolvedTheme, setTheme } = useTheme();

  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'create', label: 'New Ticket', icon: PlusCircle },
    { id: 'queue', label: 'Ticket Queue', icon: ListOrdered },
    { id: 'evaluation', label: 'AI Quality & Accuracy', icon: BarChart3 },
  ];

  const displayName = profile?.full_name || user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Support Specialist';
  const displayEmail = profile?.email || user?.email || 'agent@resolve-ai.local';
  const roleName = profile?.role === 'admin' ? 'Admin' : profile?.role === 'manager' ? 'Team Lead' : 'Specialist';

  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('') || 'SP';

  const toggleTheme = () => {
    if (resolvedTheme === 'dark') {
      setTheme('light');
    } else {
      setTheme('dark');
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white/90 dark:bg-[#0B0F19]/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Wordmark & Logo */}
          <button
            onClick={() => onNavigate('dashboard')}
            className="flex items-center space-x-3 text-left focus-ring rounded-lg p-1"
            aria-label="Resolve AI Home"
          >
            <BrandLogo size="md" showBadge={true} showTagline={false} />
          </button>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex space-x-1 sm:space-x-1.5" aria-label="Main Navigation">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors focus-ring ${
                    isActive
                      ? 'bg-indigo-50 dark:bg-indigo-600/15 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-900 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 dark:text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Hand Actions: Health, Theme, User Menu */}
          <div className="hidden sm:flex items-center space-x-3">
            {/* Database indicator */}
            <button
              type="button"
              onClick={onRefreshHealth}
              className="flex items-center space-x-2 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-900 hover:bg-slate-200 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-xs transition cursor-pointer focus-ring"
              title={`Database status: ${health?.status || 'checking'}${health?.storage_backend ? ` (${health.storage_backend})` : ''} - Click to refresh`}
              aria-label="Database health status indicator"
            >
              <Database className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
              <span className="text-slate-700 dark:text-slate-300 font-mono text-[11px]">
                {health?.storage_backend === 'supabase'
                  ? 'Supabase Cloud'
                  : health?.storage_backend === 'local_sqlite'
                  ? 'SQLite Local'
                  : health?.storage_backend === 'offline_mode'
                  ? 'Offline'
                  : health?.storage_backend || 'Connecting...'}
              </span>
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === 'healthy'
                    ? 'bg-emerald-500'
                    : health?.status === 'degraded'
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`}
                title={`Database status: ${health?.status || 'checking'}`}
              />
            </button>

            {/* Quick Theme Switcher Button */}
            <button
              onClick={toggleTheme}
              title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              aria-label="Toggle display theme"
              className="p-1.5 rounded-md text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-900 border border-slate-200 dark:border-slate-800 transition focus-ring"
            >
              {resolvedTheme === 'dark' ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4 text-slate-600" />
              )}
            </button>

            {/* User Profile Dropdown or Login Button */}
            {user ? (
              <div className="relative" ref={userMenuRef}>
                <button
                  type="button"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center space-x-2.5 p-1 pl-2 pr-2.5 rounded-full border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition focus-ring"
                  aria-expanded={userMenuOpen}
                  aria-haspopup="true"
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow-sm">
                    {initials}
                  </div>
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 max-w-[120px] truncate">
                    {displayName}
                  </span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-64 rounded-xl saas-card shadow-lg py-2 z-50 border border-slate-200 dark:border-slate-800 animate-in fade-in slide-in-from-top-2 duration-150">
                    <div className="px-4 py-2.5 border-b border-slate-100 dark:border-slate-800">
                      <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
                        {displayName}
                      </p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                        {displayEmail}
                      </p>
                      <span className="inline-block mt-1 px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-50 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 rounded border border-indigo-200 dark:border-indigo-800">
                        {roleName}
                      </span>
                    </div>

                    <div className="py-1">
                      <button
                        onClick={() => {
                          setUserMenuOpen(false);
                          onNavigate('account');
                        }}
                        className="w-full flex items-center space-x-2.5 px-4 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/80 transition"
                      >
                        <UserIcon className="w-4 h-4 text-slate-400" />
                        <span>Account Details</span>
                      </button>

                      <button
                        onClick={() => {
                          setUserMenuOpen(false);
                          onNavigate('settings');
                        }}
                        className="w-full flex items-center space-x-2.5 px-4 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/80 transition"
                      >
                        <SettingsIcon className="w-4 h-4 text-slate-400" />
                        <span>Preferences & Settings</span>
                      </button>
                    </div>

                    <div className="border-t border-slate-100 dark:border-slate-800 pt-1">
                      <button
                        onClick={async () => {
                          setUserMenuOpen(false);
                          await signOut();
                          onNavigate('login');
                        }}
                        className="w-full flex items-center space-x-2.5 px-4 py-2 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onNavigate('login')}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition focus-ring"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Sign In</span>
                </button>
                <button
                  onClick={() => onNavigate('signup')}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition focus-ring shadow-sm"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Sign Up</span>
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center sm:hidden space-x-2">
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="p-1.5 rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              {resolvedTheme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Toggle mobile navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="sm:hidden border-t border-slate-200 dark:border-slate-800 py-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onNavigate(item.id);
                  }}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium ${
                    isActive
                      ? 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}

            {user ? (
              <div className="pt-2 border-t border-slate-200 dark:border-slate-800 space-y-1">
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onNavigate('account');
                  }}
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <UserIcon className="w-4 h-4" />
                  <span>Account Details ({displayName})</span>
                </button>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onNavigate('settings');
                  }}
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <SettingsIcon className="w-4 h-4" />
                  <span>Preferences & Settings</span>
                </button>
                <button
                  onClick={async () => {
                    setMobileMenuOpen(false);
                    await signOut();
                    onNavigate('login');
                  }}
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex gap-2 px-1">
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onNavigate('login');
                  }}
                  className="flex-1 py-2 text-center text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200"
                >
                  Sign In
                </button>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onNavigate('signup');
                  }}
                  className="flex-1 py-2 text-center text-xs font-semibold rounded-lg bg-indigo-600 text-white"
                >
                  Sign Up
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
