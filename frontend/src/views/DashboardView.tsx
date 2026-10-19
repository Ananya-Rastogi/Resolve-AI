import React, { useEffect, useState } from 'react';
import {
  Inbox,
  Clock,
  CheckCircle2,
  Flame,
  PlusCircle,
  ArrowRight,
  ArrowUpRight,
  Layers,
  ShieldAlert,
  AlertTriangle,
  Users,
  Sparkles,
  BarChart2,
} from 'lucide-react';
import { fetchAnalytics, fetchTickets } from '../api';
import { AnalyticsResponse, Ticket } from '../types';
import { StatusBadge, PriorityBadge, TopicBadge, TierBadge } from '../components/Badges';
import { useAuth } from '../context/AuthContext';

interface DashboardViewProps {
  onNavigate: (view: string, ticketId?: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const { user, profile, welcomeMessage, setWelcomeMessage } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyticsTab, setAnalyticsTab] = useState<'category' | 'priority'>('category');

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
      setError(err.message || 'Failed to load tickets and metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto" />
          <p className="text-slate-500 dark:text-slate-400 text-xs font-mono">Loading dashboard metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-xl saas-card border-rose-300 dark:border-rose-500/30 text-rose-800 dark:text-rose-300 max-w-xl mx-auto my-12 text-center space-y-3">
        <AlertTriangle className="w-7 h-7 mx-auto text-rose-500" />
        <p className="text-sm font-semibold">{error}</p>
        <button
          onClick={loadData}
          className="px-3.5 py-1.5 bg-rose-100 dark:bg-rose-500/20 hover:bg-rose-200 dark:hover:bg-rose-500/30 text-rose-700 dark:text-rose-200 rounded-lg text-xs font-semibold tracking-wide transition focus-ring"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const live = analytics?.live_metrics;
  const totalCount = live?.total_tickets || 0;

  // Personal greeting based on local time
  const hour = new Date().getHours();
  const timeGreeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const displayName = profile?.full_name || user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'there';
  const firstName = displayName.split(' ')[0] || 'there';

  const categoryDefinitions = [
    { id: 'technical', label: 'Technical Support', color: 'bg-indigo-500' },
    { id: 'billing', label: 'Billing & Charges', color: 'bg-emerald-500' },
    { id: 'shipping', label: 'Shipping & Delivery', color: 'bg-sky-500' },
    { id: 'other', label: 'General Questions', color: 'bg-amber-500' },
  ];

  const priorityDefinitions = [
    { id: 'High', label: 'High Priority', color: 'bg-rose-500' },
    { id: 'Medium', label: 'Medium Priority', color: 'bg-amber-500' },
    { id: 'Low', label: 'Low Priority', color: 'bg-slate-400 dark:bg-slate-500' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* 1. Header with greeting and Create Ticket CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-indigo-600 dark:text-indigo-400 font-semibold block mb-0.5">
            {timeGreeting}
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            Welcome back, {firstName} <span className="inline-block">👋</span>
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Here's what needs your attention today.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => onNavigate('create')}
            className="flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all focus-ring hover:shadow-indigo-500/20"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Create New Ticket</span>
          </button>
        </div>
      </div>

      {/* Optional Welcome Message Banner */}
      {welcomeMessage && (
        <div className="p-3.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 flex items-center justify-between text-indigo-900 dark:text-indigo-200 text-xs sm:text-sm">
          <div className="flex items-center space-x-2.5">
            <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
            <span className="font-medium">{welcomeMessage}</span>
          </div>
          <button
            onClick={() => setWelcomeMessage(null)}
            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 2. Four Primary KPI Cards (1 row on desktop, 2 on tablet, 1 on mobile) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Tickets */}
        <div className="p-4 sm:p-5 rounded-xl saas-card flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Total Tickets</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <Inbox className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
              {live?.total_tickets ?? 0}
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 flex items-center space-x-1">
              <span>All tickets recorded</span>
            </div>
          </div>
        </div>

        {/* Open Tickets */}
        <div className="p-4 sm:p-5 rounded-xl saas-card flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Open Tickets</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
              {live?.open_tickets ?? 0}
            </div>
            <div className="text-[11px] text-amber-600 dark:text-amber-400 mt-1 flex items-center space-x-1.5 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" />
              <span>Needs action</span>
            </div>
          </div>
        </div>

        {/* Resolved */}
        <div className="p-4 sm:p-5 rounded-xl saas-card flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Resolved</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
              {live?.resolved_tickets ?? 0}
            </div>
            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1 flex items-center space-x-1.5 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
              <span>Successfully resolved</span>
            </div>
          </div>
        </div>

        {/* High Priority */}
        <div className="p-4 sm:p-5 rounded-xl saas-card flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">High Priority</span>
            <div className="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 flex items-center justify-center">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
              {live?.high_priority_tickets ?? 0}
            </div>
            <div className="text-[11px] text-rose-600 dark:text-rose-400 mt-1 flex items-center space-x-1.5 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 inline-block" />
              <span>Needs urgent reply</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Middle Section: Combined Analytics (Left) & Needs Attention (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column (7 cols): Combined Analytics with Category & Priority tabs */}
        <div className="lg:col-span-7 p-5 sm:p-6 rounded-xl saas-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <BarChart2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                Ticket Distribution
              </h2>
            </div>

            {/* Compact Toggle between Category and Priority */}
            <div className="flex items-center p-0.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-[11px] font-medium">
              <button
                type="button"
                onClick={() => setAnalyticsTab('category')}
                className={`px-2.5 py-1 rounded-md transition ${
                  analyticsTab === 'category'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm font-semibold'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-300'
                }`}
              >
                By Category
              </button>
              <button
                type="button"
                onClick={() => setAnalyticsTab('priority')}
                className={`px-2.5 py-1 rounded-md transition ${
                  analyticsTab === 'priority'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm font-semibold'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-300'
                }`}
              >
                By Priority
              </button>
            </div>
          </div>

          {/* Horizontal Progress Bars */}
          {analyticsTab === 'category' ? (
            <div className="space-y-3.5 pt-1">
              {categoryDefinitions.map(({ id, label, color }) => {
                const count = live?.category_distribution?.[id] || 0;
                const pct = totalCount > 0 ? Math.round((count / totalCount) * 100) : 0;

                return (
                  <div key={id} className="space-y-1.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-medium text-slate-700 dark:text-slate-300">{label}</span>
                      <span className="font-mono text-slate-500 dark:text-slate-400 text-[11px]">
                        {count} ({pct}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800/80 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${color}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="space-y-3.5 pt-1">
              {priorityDefinitions.map(({ id, label, color }) => {
                const count = live?.priority_distribution?.[id] || 0;
                const pct = totalCount > 0 ? Math.round((count / totalCount) * 100) : 0;

                return (
                  <div key={id} className="space-y-1.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-medium text-slate-700 dark:text-slate-300">{label}</span>
                      <span className="font-mono text-slate-500 dark:text-slate-400 text-[11px]">
                        {count} ({pct}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800/80 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${color}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Summary Footer */}
          <div className="pt-2 border-t border-slate-100 dark:border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Live database count: {totalCount} tickets</span>
            <button
              onClick={() => onNavigate('evaluation')}
              className="text-indigo-600 dark:text-indigo-400 hover:underline flex items-center space-x-1"
            >
              <span>View AI Quality & Accuracy</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Right Column (5 cols): Needs Attention Section (Escalations, Urgent, Action needed) */}
        <div className="lg:col-span-5 p-5 sm:p-6 rounded-xl saas-card space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                Needs Attention
              </h2>
              <button
                onClick={() => onNavigate('queue')}
                className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center space-x-1"
              >
                <span>View All</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            {/* Action Alert Rows */}
            <div className="space-y-2.5">
              {/* High Priority Item */}
              <button
                onClick={() => onNavigate('queue')}
                className="w-full text-left p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-900 border border-slate-200 dark:border-slate-800/80 transition flex items-center space-x-3 focus-ring"
              >
                <div className="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
                  <Flame className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {live?.high_priority_tickets ?? 0} high-priority tickets
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                    Require urgent reply within SLA
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              </button>

              {/* Senior Team Review Item (Formerly 5th KPI) */}
              <button
                onClick={() => onNavigate('queue')}
                className="w-full text-left p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-900 border border-slate-200 dark:border-slate-800/80 transition flex items-center space-x-3 focus-ring"
              >
                <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
                  <Users className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {live?.escalated_tickets ?? 0} tickets need senior review
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                    Assigned to senior manager team
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              </button>

              {/* Open Tickets Item */}
              <button
                onClick={() => onNavigate('queue')}
                className="w-full text-left p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-900 border border-slate-200 dark:border-slate-800/80 transition flex items-center space-x-3 focus-ring"
              >
                <div className="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
                  <Clock className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {live?.open_tickets ?? 0} open tickets
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                    Awaiting specialist team action
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              </button>
            </div>
          </div>

          {/* Active Teams Compact Summary */}
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800/60">
            <span className="text-[10px] uppercase font-mono text-slate-500 block mb-2 font-semibold tracking-wider">
              Active Support Teams:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(live?.team_distribution || {}).map(([team, count]) => (
                <button
                  key={team}
                  onClick={() => onNavigate('queue')}
                  className="px-2 py-1 rounded-md bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-[11px] font-medium transition flex items-center space-x-1.5"
                >
                  <span>{team}</span>
                  <span className="font-mono text-indigo-600 dark:text-indigo-400 font-bold">{count}</span>
                </button>
              ))}
              {Object.keys(live?.team_distribution || {}).length === 0 && (
                <span className="text-xs text-slate-500 italic">No assigned teams recorded yet.</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 4. Recent Tickets Table */}
      <div className="rounded-xl saas-card overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Recent Tickets
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Latest incoming tickets awaiting or undergoing resolution.
            </p>
          </div>
          <button
            onClick={() => onNavigate('queue')}
            className="flex items-center space-x-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline transition focus-ring"
          >
            <span>View All Tickets</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentTickets.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Inbox className="w-8 h-8 text-slate-400 mx-auto" />
            <p className="text-slate-500 dark:text-slate-400 text-xs">No tickets in the database yet.</p>
            <button
              onClick={() => onNavigate('create')}
              className="px-3.5 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700 transition focus-ring shadow-sm"
            >
              Create Your First Ticket
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
              <thead className="text-[11px] uppercase bg-slate-50 dark:bg-slate-900/60 text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 font-mono">
                <tr>
                  <th className="px-5 py-3">Ticket ID</th>
                  <th className="px-5 py-3">Customer & Tier</th>
                  <th className="px-5 py-3">Subject</th>
                  <th className="px-5 py-3">Category & Priority</th>
                  <th className="px-5 py-3">Assigned Team</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/60">
                {recentTickets.map((t) => (
                  <tr
                    key={t.ticket_id}
                    onClick={() => onNavigate('detail', t.ticket_id)}
                    className="hover:bg-slate-50 dark:hover:bg-slate-900/50 cursor-pointer transition"
                  >
                    <td className="px-5 py-3.5 font-mono font-semibold text-indigo-600 dark:text-indigo-400 whitespace-nowrap">
                      {t.ticket_id}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="font-semibold text-slate-900 dark:text-slate-200">
                        {t.customer_name || 'Anonymous Customer'}
                      </div>
                      <div className="mt-0.5">
                        <TierBadge tier={t.tier} />
                      </div>
                    </td>
                    <td className="px-5 py-3.5 max-w-xs truncate text-slate-700 dark:text-slate-300">
                      <span title={t.subject}>{t.subject}</span>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="flex items-center space-x-1.5">
                        <TopicBadge topic={t.category} />
                        <PriorityBadge priority={t.priority} />
                      </div>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap text-slate-800 dark:text-slate-300 font-medium">
                      {t.assigned_team || 'General Support'}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap text-right">
                      <span className="text-indigo-600 dark:text-indigo-400 font-medium hover:underline inline-flex items-center space-x-1">
                        <span>Details</span>
                        <ArrowRight className="w-3 h-3" />
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
