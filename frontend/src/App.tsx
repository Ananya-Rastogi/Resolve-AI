import React, { useEffect, useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { DashboardView } from './views/DashboardView';
import { CreateTicketView } from './views/CreateTicketView';
import { TicketQueueView } from './views/TicketQueueView';
import { TicketDetailView } from './views/TicketDetailView';
import { QualityEvalView } from './views/QualityEvalView';
import { AccountView } from './views/AccountView';
import { SettingsView } from './views/SettingsView';
import { LoginView } from './views/LoginView';
import { SignUpView } from './views/SignUpView';
import { ResetPasswordView } from './views/ResetPasswordView';
import { fetchHealth } from './api';
import { HealthResponse } from './types';
import { BRAND_CONFIG } from './config/brand';

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentView, setCurrentView] = useState<string>('dashboard');
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const loadHealth = async () => {
    try {
      const h = await fetchHealth();
      setHealth(h);
    } catch (err) {
      console.warn('Backend health check error:', err);
      setHealth({
        status: 'degraded',
        timestamp: new Date().toISOString(),
        storage_backend: 'offline_mode',
        vector_store_status: 'unknown',
        database_status: 'unreachable',
        version: '1.0.0',
      });
    }
  };

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleNavigate = (view: string, ticketId?: string) => {
    if (ticketId) {
      setSelectedTicketId(ticketId);
      setCurrentView('detail');
    } else {
      setCurrentView(view);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Initial loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-600 rounded-full animate-spin mx-auto" />
          <h2 className="text-lg font-bold tracking-tight text-slate-800 dark:text-slate-200">
            Loading {BRAND_CONFIG.name}...
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Checking your secure session</p>
        </div>
      </div>
    );
  }

  // Unauthenticated flow: protect all routes
  if (!user) {
    if (currentView === 'signup') {
      return <SignUpView onNavigate={handleNavigate} />;
    }
    if (currentView === 'reset-password') {
      return <ResetPasswordView onNavigate={handleNavigate} />;
    }
    return <LoginView onNavigate={handleNavigate} />;
  }

  // If user is logged in but view is an auth view, direct to dashboard
  const activeView = (currentView === 'login' || currentView === 'signup' || currentView === 'reset-password')
    ? 'dashboard'
    : currentView;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100 antialiased selection:bg-indigo-500/30 transition-colors duration-200">
      {/* Top Navigation */}
      <Navbar
        currentView={activeView}
        onNavigate={(view) => handleNavigate(view)}
        health={health}
        onRefreshHealth={loadHealth}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeView === 'dashboard' && <DashboardView onNavigate={handleNavigate} />}
        {activeView === 'create' && <CreateTicketView onNavigate={handleNavigate} />}
        {activeView === 'queue' && <TicketQueueView onNavigate={handleNavigate} />}
        {activeView === 'detail' && selectedTicketId && (
          <TicketDetailView
            ticketId={selectedTicketId}
            onBack={() => handleNavigate('queue')}
          />
        )}
        {activeView === 'evaluation' && <QualityEvalView />}
        {activeView === 'account' && <AccountView onNavigate={handleNavigate} />}
        {activeView === 'settings' && <SettingsView onNavigate={handleNavigate} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-900 bg-white dark:bg-[#070A10] py-6 text-center text-xs text-slate-500 font-mono transition-colors">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-700 dark:text-slate-400">{BRAND_CONFIG.name}</span>
            <span>—</span>
            <span className="text-slate-500 dark:text-slate-500">{BRAND_CONFIG.tagline}</span>
          </div>
          <div className="flex items-center space-x-3 text-slate-500 dark:text-slate-400">
            <span>FastAPI Backend</span>
            <span>•</span>
            <span>LangGraph Multi-Agent</span>
            <span>•</span>
            <span>ChromaDB Knowledge Base</span>
            <span>•</span>
            <span>Supabase / SQLite</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
