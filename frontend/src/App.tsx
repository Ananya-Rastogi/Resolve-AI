import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardView } from './views/DashboardView';
import { CreateTicketView } from './views/CreateTicketView';
import { TicketQueueView } from './views/TicketQueueView';
import { TicketDetailView } from './views/TicketDetailView';
import { QualityEvalView } from './views/QualityEvalView';
import { fetchHealth } from './api';
import { HealthResponse } from './types';
import { BRAND_CONFIG } from './config/brand';

export const App: React.FC = () => {
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

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0F19] text-slate-100 antialiased selection:bg-indigo-500/30">
      {/* Top Navigation */}
      <Navbar
        currentView={currentView}
        onNavigate={(view) => handleNavigate(view)}
        health={health}
        onRefreshHealth={loadHealth}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'dashboard' && <DashboardView onNavigate={handleNavigate} />}
        {currentView === 'create' && <CreateTicketView onNavigate={handleNavigate} />}
        {currentView === 'queue' && <TicketQueueView onNavigate={handleNavigate} />}
        {currentView === 'detail' && selectedTicketId && (
          <TicketDetailView
            ticketId={selectedTicketId}
            onBack={() => handleNavigate('queue')}
          />
        )}
        {currentView === 'evaluation' && <QualityEvalView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-[#070A10] py-6 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-400">{BRAND_CONFIG.name}</span>
            <span>—</span>
            <span>{BRAND_CONFIG.tagline}</span>
          </div>
          <div className="flex items-center space-x-3 text-slate-400">
            <span>FastAPI 0.142</span>
            <span>•</span>
            <span>LangGraph StateGraph</span>
            <span>•</span>
            <span>ChromaDB RAG</span>
            <span>•</span>
            <span>SQLite / Supabase</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
