import React from 'react';
import {
  LayoutDashboard,
  PlusCircle,
  ListOrdered,
  BarChart3,
  Database,
  RefreshCw,
} from 'lucide-react';
import { HealthResponse } from '../types';
import { BrandLogo } from './BrandLogo';

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
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'create', label: 'Ingest Ticket', icon: PlusCircle },
    { id: 'queue', label: 'Ticket Queue', icon: ListOrdered },
    { id: 'evaluation', label: 'Quality & Benchmarks', icon: BarChart3 },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0B0F19]/90 backdrop-blur-md border-b border-slate-800">
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

          {/* Navigation Links */}
          <nav className="flex space-x-1 sm:space-x-1.5" aria-label="Main Navigation">
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
                      ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* System Health & Backend Indicator */}
          <div className="hidden md:flex items-center space-x-2.5">
            <div className="flex items-center space-x-2 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs">
              <Database className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-300 font-mono text-[11px]">
                {health?.storage_backend === 'supabase' ? 'Supabase' : 'SQLite Local'}
              </span>
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === 'healthy' ? 'bg-emerald-400' : 'bg-amber-400'
                }`}
                title={`Database status: ${health?.status || 'checking'}`}
              />
            </div>

            <button
              onClick={onRefreshHealth}
              title="Refresh connection status"
              aria-label="Refresh connection status"
              className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-slate-800 transition focus-ring"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
