import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Clock,
} from 'lucide-react';
import { fetchTickets, updateTicket } from '../api';
import { Ticket, TicketStatus } from '../types';
import { StatusBadge, PriorityBadge, TopicBadge, TierBadge, SourceBadge } from '../components/Badges';
import { BRAND_CONFIG } from '../config/brand';
import { calculateTicketSLA } from '../utils/sla';

interface TicketQueueViewProps {
  onNavigate: (view: string, ticketId?: string) => void;
}

export const TicketQueueView: React.FC<TicketQueueViewProps> = ({ onNavigate }) => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [limit] = useState(15);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');

  const loadTickets = async () => {
    try {
      setLoading(true);
      const res = await fetchTickets({
        page,
        limit,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
        priority: priorityFilter || undefined,
        assigned_team: teamFilter || undefined,
      });
      setTickets(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Error fetching ticket queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, [page, statusFilter, categoryFilter, priorityFilter, teamFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadTickets();
  };

  const handleQuickStatusChange = async (ticketId: string, newStatus: TicketStatus) => {
    try {
      setUpdatingId(ticketId);
      await updateTicket(ticketId, { status: newStatus, actor: 'support_agent' });
      await loadTickets();
    } catch (err) {
      console.error('Failed to update ticket status:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleQuickTeamChange = async (ticketId: string, newTeam: string) => {
    try {
      setUpdatingId(ticketId);
      await updateTicket(ticketId, { assigned_team: newTeam, actor: 'support_agent' });
      await loadTickets();
    } catch (err) {
      console.error('Failed to reassign team:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            Support Ticket Queue
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Search, filter, view AI triage results, and update ticket statuses or team assignments.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              setSearch('');
              setStatusFilter('');
              setCategoryFilter('');
              setPriorityFilter('');
              setTeamFilter('');
              setPage(1);
              loadTickets();
            }}
            title="Reset filters and reload"
            className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 text-xs font-medium flex items-center space-x-1.5 transition focus-ring shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh List</span>
          </button>
        </div>
      </div>

      {/* Search and Filters Toolbar */}
      <div className="p-4 rounded-xl saas-panel border border-slate-200 dark:border-slate-800 space-y-3.5">
        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Ticket ID (TKT-...), customer name, or issue details..."
              className="saas-input pl-10 pr-4 py-2"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition focus-ring shadow-sm"
          >
            Search
          </button>
        </form>

        {/* Filter Dropdowns */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1 font-mono text-[11px]">Ticket Status</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="saas-input py-1.5 text-xs"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="escalated">Sent to Senior Team</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1 font-mono text-[11px]">Ticket Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
              className="saas-input py-1.5 text-xs"
            >
              <option value="">All Categories</option>
              <option value="billing">Billing & Charges</option>
              <option value="shipping">Shipping & Delivery</option>
              <option value="technical">Technical Support</option>
              <option value="other">General Inquiries</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1 font-mono text-[11px]">Priority</label>
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setPage(1);
              }}
              className="saas-input py-1.5 text-xs"
            >
              <option value="">All Priorities</option>
              <option value="High">High Priority</option>
              <option value="Medium">Medium Priority</option>
              <option value="Low">Low Priority</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1 font-mono text-[11px]">Support Team</label>
            <select
              value={teamFilter}
              onChange={(e) => {
                setTeamFilter(e.target.value);
                setPage(1);
              }}
              className="saas-input py-1.5 text-xs"
            >
              <option value="">All Teams</option>
              <option value="Finance Team">Finance Team</option>
              <option value="Logistics Team">Logistics Team</option>
              <option value="Tech Support">Tech Support</option>
              <option value="General Support">General Support</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table Container */}
      <div className="rounded-xl saas-card overflow-hidden">
        {loading ? (
          <div className="p-16 text-center space-y-2">
            <div className="w-7 h-7 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto" />
            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Loading ticket queue...</p>
          </div>
        ) : tickets.length === 0 ? (
          <div className="p-16 text-center space-y-2.5">
            <Filter className="w-8 h-8 text-slate-400 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">No matching tickets found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No tickets matched your query. Adjust your filter criteria or create a new ticket in {BRAND_CONFIG.name}.
            </p>
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
                  <th className="px-5 py-3">SLA Status</th>
                  <th className="px-5 py-3">Team & AI Method</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/60">
                {tickets.map((t) => {
                  const sla = calculateTicketSLA(t.priority, t.created_at, t.status);
                  const createdDate = t.created_at && !isNaN(new Date(t.created_at).getTime())
                    ? new Date(t.created_at).toLocaleDateString()
                    : '—';

                  return (
                    <tr key={t.ticket_id} className="hover:bg-slate-50 dark:hover:bg-slate-900/40 transition">
                      <td className="px-5 py-3.5 whitespace-nowrap font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                        <button
                          onClick={() => onNavigate('detail', t.ticket_id)}
                          className="hover:underline text-left block focus-ring"
                        >
                          {t.ticket_id}
                        </button>
                        <span className="text-[10px] text-slate-500 font-sans block mt-0.5">
                          {createdDate}
                        </span>
                      </td>

                      <td className="px-5 py-3.5 whitespace-nowrap">
                        <div className="font-semibold text-slate-900 dark:text-slate-200">{t.customer_name || 'Anonymous Customer'}</div>
                        <div className="mt-1">
                          <TierBadge tier={t.tier} />
                        </div>
                      </td>

                      <td className="px-5 py-3.5 max-w-sm truncate text-slate-700 dark:text-slate-300">
                        <span title={t.subject}>{t.subject}</span>
                      </td>

                      <td className="px-5 py-3.5 whitespace-nowrap">
                        <div className="flex flex-col space-y-1">
                          <div>
                            <TopicBadge topic={t.category} />
                          </div>
                          <div>
                            <PriorityBadge priority={t.priority} />
                          </div>
                        </div>
                      </td>

                      <td className="px-5 py-3.5 whitespace-nowrap">
                        <div className="flex flex-col space-y-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${sla.colorClass} w-fit`}>
                            <Clock className="w-3 h-3 mr-1 shrink-0" />
                            {sla.status}
                          </span>
                          <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono" title={sla.deadlineText}>
                            {sla.timeRemaining}
                          </span>
                        </div>
                      </td>

                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <select
                        value={t.assigned_team || 'General Support'}
                        disabled={updatingId === t.ticket_id}
                        onChange={(e) => handleQuickTeamChange(t.ticket_id, e.target.value)}
                        className="px-2 py-1 rounded bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 focus-ring"
                      >
                        <option value="Finance Team">Finance Team</option>
                        <option value="Logistics Team">Logistics Team</option>
                        <option value="Tech Support">Tech Support</option>
                        <option value="General Support">General Support</option>
                      </select>
                      <div className="mt-1">
                        <SourceBadge source={t.classification_source} />
                      </div>
                    </td>

                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <select
                        value={t.status}
                        disabled={updatingId === t.ticket_id}
                        onChange={(e) => handleQuickStatusChange(t.ticket_id, e.target.value as TicketStatus)}
                        className="px-2 py-1 rounded bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 focus-ring"
                      >
                        <option value="open">Open</option>
                        <option value="in_progress">In Progress</option>
                        <option value="resolved">Resolved</option>
                        <option value="escalated">Sent to Senior Team</option>
                      </select>
                    </td>

                    <td className="px-5 py-3.5 whitespace-nowrap text-right">
                      <button
                        onClick={() => onNavigate('detail', t.ticket_id)}
                        className="px-2.5 py-1 rounded-md bg-indigo-50 dark:bg-indigo-600/10 hover:bg-indigo-100 dark:hover:bg-indigo-600/20 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 transition inline-flex items-center space-x-1 focus-ring"
                      >
                        <span>Open</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-3.5 bg-slate-50 dark:bg-slate-900/60 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-mono">
          <div>
            Showing {tickets.length > 0 ? (page - 1) * limit + 1 : 0} to{' '}
            {Math.min(page * limit, total)} of {total} tickets
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="p-1 rounded bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 dark:text-slate-300 transition focus-ring border border-slate-200 dark:border-slate-700"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="p-1 rounded bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 dark:text-slate-300 transition focus-ring border border-slate-200 dark:border-slate-700"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
