import React, { useEffect, useState } from 'react';
import {
  Inbox,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Flame,
  ArrowUpRight,
  Layers,
  Cpu,
  ArrowRight,
  ShieldCheck,
  Check,
} from 'lucide-react';
import { fetchAnalytics, fetchTickets } from '../api';
import { AnalyticsResponse, Ticket } from '../types';
import { StatusBadge, PriorityBadge, TopicBadge, TierBadge } from '../components/Badges';
import { BRAND_CONFIG } from '../config/brand';
import { WorkflowTracker } from '../components/WorkflowTracker';

interface DashboardViewProps {
  onNavigate: (view: string, ticketId?: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [analyticsData, ticketsData] = await Promise.all([
        fetchAnalytics(),
        fetchTickets({ limit: 6, page: 1 }),
      ]);
      setAnalytics(analyticsData);
      setRecentTickets(ticketsData.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load operational metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-xs font-mono">Loading Resolve AI operational metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-xl saas-card border-rose-500/30 text-rose-300 max-w-xl mx-auto my-12 text-center space-y-3">
        <AlertTriangle className="w-7 h-7 mx-auto text-rose-400" />
        <p className="text-sm font-semibold">{error}</p>
        <button
          onClick={loadData}
          className="px-3.5 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 rounded-lg text-xs font-semibold tracking-wide transition focus-ring"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const live = analytics?.live_metrics;

  const statCards = [
    {
      label: 'Total Ingested',
      value: live?.total_tickets ?? 0,
      icon: Inbox,
      sub: 'All time',
    },
    {
      label: 'Open Queue',
      value: live?.open_tickets ?? 0,
      icon: Clock,
      sub: 'Awaiting action',
    },
    {
      label: 'Resolved',
      value: live?.resolved_tickets ?? 0,
      icon: CheckCircle2,
      sub: 'Completed',
    },
    {
      label: 'High Priority',
      value: live?.high_priority_tickets ?? 0,
      icon: Flame,
      sub: 'SLA sensitive',
    },
    {
      label: 'Escalations',
      value: live?.escalated_tickets ?? 0,
      icon: AlertTriangle,
      sub: 'Human oversight',
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-mono font-medium mb-1">
            <span>{BRAND_CONFIG.category}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            {BRAND_CONFIG.primaryTagline}
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            {BRAND_CONFIG.supportingMessage}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => onNavigate('create')}
            className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-sm transition focus-ring"
          >
            <span>Ingest New Ticket</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Real-time KPI Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="p-4 rounded-xl saas-card saas-card-hover flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium uppercase tracking-wider font-mono">
                  {card.label}
                </span>
                <Icon className="w-4 h-4 opacity-75" />
              </div>
              <div className="mt-3">
                <div className="text-2xl sm:text-3xl font-bold text-white font-mono">
                  {card.value}
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">{card.sub}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Multi-Agent Coordinated Lifecycle Tracker */}
      <WorkflowTracker ticket={recentTickets[0] as any} />

      {/* Breakdown Grid: Category, Priority, Team Routing */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Category Breakdown */}
        <div className="p-5 rounded-xl saas-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center space-x-2">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <span>Category Distribution</span>
            </h2>
            <span className="text-[11px] text-slate-500 font-mono">Live DB</span>
          </div>

          <div className="space-y-3 pt-1">
            {['billing', 'shipping', 'technical', 'other'].map((cat) => {
              const count = live?.category_distribution?.[cat] || 0;
              const total = live?.total_tickets || 1;
              const pct = Math.round((count / total) * 100);
              return (
                <div key={cat} className="space-y-1">
                  <div className="flex justify-between text-xs font-sans">
                    <span className="capitalize font-medium text-slate-300">{cat}</span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        cat === 'billing'
                          ? 'bg-emerald-500'
                          : cat === 'shipping'
                          ? 'bg-cyan-500'
                          : cat === 'technical'
                          ? 'bg-indigo-500'
                          : 'bg-slate-400'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Priority Breakdown */}
        <div className="p-5 rounded-xl saas-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center space-x-2">
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>Priority Levels</span>
            </h2>
            <span className="text-[11px] text-slate-500 font-mono">Live DB</span>
          </div>

          <div className="space-y-3 pt-1">
            {[
              { level: 'High', color: 'bg-rose-500' },
              { level: 'Medium', color: 'bg-amber-500' },
              { level: 'Low', color: 'bg-slate-500' },
            ].map(({ level, color }) => {
              const count = live?.priority_distribution?.[level] || 0;
              const total = live?.total_tickets || 1;
              const pct = Math.round((count / total) * 100);
              return (
                <div key={level} className="space-y-1">
                  <div className="flex justify-between text-xs font-sans">
                    <span className="font-medium text-slate-300">{level} Priority</span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
                    <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Support Team Assignments */}
        <div className="p-5 rounded-xl saas-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center space-x-2">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span>Specialized Agent Routing</span>
            </h2>
            <span className="text-[11px] text-slate-500 font-mono">Live DB</span>
          </div>

          <div className="space-y-2 pt-1">
            {Object.entries(live?.team_distribution || {}).map(([team, count]) => {
              return (
                <div
                  key={team}
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                >
                  <span className="font-medium text-slate-300">{team}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono font-semibold text-[11px]">
                    {count}
                  </span>
                </div>
              );
            })}
            {Object.keys(live?.team_distribution || {}).length === 0 && (
              <p className="text-xs text-slate-500 italic py-4 text-center">No assigned tickets recorded yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Tickets Table */}
      <div className="rounded-xl saas-card overflow-hidden">
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
              Recent Triaged Tickets
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live operational tickets persisted in {live?.storage_backend === 'supabase' ? 'Supabase' : 'SQLite'}.
            </p>
          </div>
          <button
            onClick={() => onNavigate('queue')}
            className="flex items-center space-x-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition focus-ring"
          >
            <span>View Full Queue</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentTickets.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Inbox className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-slate-400 text-xs">No tickets in the database yet.</p>
            <button
              onClick={() => onNavigate('create')}
              className="px-3.5 py-1.5 bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-semibold hover:bg-indigo-600/30 transition focus-ring"
            >
              Ingest First Support Ticket
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="text-[11px] uppercase bg-slate-900/60 text-slate-400 border-b border-slate-800 font-mono">
                <tr>
                  <th className="px-5 py-3">Ticket ID</th>
                  <th className="px-5 py-3">Customer & Tier</th>
                  <th className="px-5 py-3">Subject</th>
                  <th className="px-5 py-3">Topic & Priority</th>
                  <th className="px-5 py-3">Assigned Team</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentTickets.map((t) => (
                  <tr
                    key={t.ticket_id}
                    onClick={() => onNavigate('detail', t.ticket_id)}
                    className="hover:bg-slate-900/50 cursor-pointer transition"
                  >
                    <td className="px-5 py-3.5 font-mono font-medium text-indigo-400 whitespace-nowrap">
                      {t.ticket_id}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="font-medium text-slate-200">{t.customer_name || 'Anonymous'}</div>
                      <div className="mt-0.5">
                        <TierBadge tier={t.tier} />
                      </div>
                    </td>
                    <td className="px-5 py-3.5 max-w-xs truncate text-slate-300">
                      {t.subject}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="flex items-center space-x-1.5">
                        <TopicBadge topic={t.category} />
                        <PriorityBadge priority={t.priority} />
                      </div>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap text-slate-300 font-medium">
                      {t.assigned_team || 'Unassigned'}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap text-right">
                      <span className="text-indigo-400 font-medium hover:underline">
                        Details &rarr;
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
