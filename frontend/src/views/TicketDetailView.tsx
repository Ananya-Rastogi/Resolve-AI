import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Bot,
  Cpu,
  Clock,
  ShieldCheck,
  AlertTriangle,
  History,
  BookOpen,
  CheckCircle2,
  FileCheck,
  ShieldAlert,
  Send,
  Zap,
} from 'lucide-react';
import { fetchTicketDetail, updateTicket } from '../api';
import { TicketDetail, TicketStatus, AssignedTeam, TicketPriority } from '../types';
import { StatusBadge, PriorityBadge, TopicBadge, TierBadge, SourceBadge } from '../components/Badges';
import { WorkflowTracker } from '../components/WorkflowTracker';
import { BRAND_CONFIG } from '../config/brand';

interface TicketDetailViewProps {
  ticketId: string;
  onBack: () => void;
}

export const TicketDetailView: React.FC<TicketDetailViewProps> = ({ ticketId, onBack }) => {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  const [editStatus, setEditStatus] = useState<TicketStatus>('open');
  const [editTeam, setEditTeam] = useState<string>('General Support');
  const [editPriority, setEditPriority] = useState<TicketPriority>('Medium');

  const loadDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchTicketDetail(ticketId);
      setTicket(data);
      setEditStatus(data.status);
      setEditTeam(data.assigned_team || 'General Support');
      setEditPriority(data.priority);
    } catch (err: any) {
      setError(err.message || 'Failed to load ticket details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [ticketId]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setUpdating(true);
      await updateTicket(ticketId, {
        status: editStatus,
        assigned_team: editTeam,
        priority: editPriority,
        actor: 'triage_lead',
      });
      await loadDetail();
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-9 h-9 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-xs font-mono">Loading {BRAND_CONFIG.name} triage diagnostics...</p>
        </div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="p-8 max-w-lg mx-auto text-center space-y-4 saas-card">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Ticket Record Unavailable</h2>
        <p className="text-sm text-slate-400">{error || 'Could not retrieve ticket records from storage.'}</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition focus-ring"
        >
          &larr; Back to Queue
        </button>
      </div>
    );
  }

  const analysis = ticket.analysis;

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Top Bar with Back Button */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white transition focus-ring rounded-md px-2 py-1"
        >
          <ArrowLeft className="w-4 h-4 text-indigo-400" />
          <span>Back to Resolution Queue</span>
        </button>

        <div className="flex items-center space-x-2 font-mono text-xs text-slate-500">
          <span>Created: {new Date(ticket.created_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Main Ticket Banner */}
      <div className="p-6 sm:p-7 rounded-2xl saas-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-3">
              <span className="text-xl sm:text-2xl font-bold font-mono text-indigo-400">
                {ticket.ticket_id}
              </span>
              <TierBadge tier={ticket.tier} />
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
            </div>
            <div className="text-xs text-slate-400 flex flex-wrap gap-x-4 gap-y-1 pt-1">
              <span>Customer: <strong className="text-slate-200">{ticket.customer_name || 'Anonymous'}</strong></span>
              {ticket.email && <span>Email: <strong className="text-slate-200">{ticket.email}</strong></span>}
              {ticket.customer_id && <span>Account: <strong className="font-mono text-slate-200">{ticket.customer_id}</strong></span>}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <SourceBadge source={ticket.classification_source} />
          </div>
        </div>

        {/* Customer Stated Issue */}
        <div className="pt-2">
          <span className="text-[11px] uppercase font-mono tracking-wider text-slate-400 block mb-1">
            Customer Stated Issue:
          </span>
          <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 text-sm text-slate-200 leading-relaxed font-sans">
            {ticket.subject}
          </div>
        </div>
      </div>

      {/* Dynamic Workflow Tracker */}
      <WorkflowTracker ticket={ticket} />

      {/* Two-Column Layout: AI Triage Diagnostics & Grounded Response */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: AI Pipeline Diagnostics (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Classification & Confidence Analysis */}
          <div className="p-6 rounded-2xl saas-card space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span>Multi-Agent Triage Diagnostics</span>
              </h2>
              <span className="text-xs text-slate-400 font-mono">
                Source: <strong className="text-indigo-300">{ticket.classification_source || 'ml'}</strong>
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[11px] text-slate-500 block uppercase font-mono">Predicted Topic</span>
                <div className="mt-1">
                  <TopicBadge topic={ticket.category} />
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[11px] text-slate-500 block uppercase font-mono">Sentiment</span>
                <span
                  className={`text-xs font-bold uppercase mt-1 block ${
                    ticket.sentiment === 'POSITIVE' ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {ticket.sentiment || 'UNKNOWN'}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[11px] text-slate-500 block uppercase font-mono">Confidence Score</span>
                <span className="text-xs font-mono font-bold text-indigo-400 mt-1 block">
                  {ticket.confidence !== undefined ? (ticket.confidence * 100).toFixed(1) + '%' : 'N/A'}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[11px] text-slate-500 block uppercase font-mono">Assigned Team</span>
                <span className="text-xs font-semibold text-slate-200 mt-1 block">
                  {ticket.assigned_team || 'General Support'}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[11px] text-slate-500 block uppercase font-mono">Calculated Priority</span>
                <span className="text-xs font-semibold text-slate-200 mt-1 block">
                  {ticket.priority}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[11px] text-slate-500 block uppercase font-mono">Escalation Decision</span>
                <span
                  className={`text-xs font-bold mt-1 block ${
                    ticket.escalation_level !== 'Not Escalated' ? 'text-rose-400' : 'text-slate-300'
                  }`}
                >
                  {ticket.escalation_level}
                </span>
              </div>
            </div>

            {/* Explainable Decision Note */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 space-y-1.5">
              <span className="font-semibold text-slate-200 flex items-center space-x-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Explainable Agent Routing:</span>
              </span>
              <p className="text-slate-400 leading-normal">
                {ticket.classification_source === 'ml'
                  ? `High initial ML confidence (${((analysis?.ml_confidence ?? 0) * 100).toFixed(1)}% >= 50% threshold) routed directly to priority assessment, preserving LLM compute.`
                  : ticket.classification_source === 'llm'
                  ? `ML classifier confidence (${((analysis?.ml_confidence ?? 0) * 100).toFixed(1)}% < 50% threshold) triggered LangGraph structured LLM fallback for safe disambiguation.`
                  : `Deterministic ML fallback utilized after LLM retry threshold was reached.`}
              </p>
              <p className="text-slate-400 leading-normal">
                Priority <strong>{ticket.priority}</strong> dispatched to <strong>{ticket.assigned_team}</strong>.
                {ticket.tier === 'Platinum' || ticket.tier === 'Gold'
                  ? ticket.priority === 'High'
                    ? ` Account tier (${ticket.tier}) triggered High-Priority Autonomous Escalation for immediate SLA dispatch.`
                    : ` Account tier (${ticket.tier}) is premium, but priority is ${ticket.priority} (standard queue).`
                  : ` Standard tier account (${ticket.tier}) queued without escalation.`}
              </p>
            </div>
          </div>

          {/* Chroma RAG Knowledge Retrieval */}
          <div className="p-6 rounded-2xl saas-card space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-emerald-400" />
                <span>Knowledge Retrieval & Grounding</span>
              </h2>
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
                <Clock className="w-3 h-3 text-slate-500" />
                <span>Total: {analysis?.total_retrieval_ms?.toFixed(1) ?? '—'} ms</span>
                {analysis?.is_cold_retrieval && (
                  <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px]">Cold</span>
                )}
              </div>
            </div>

            {/* Retrieval Timing Metrics Bar */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                <span className="text-[10px] text-slate-500 font-mono block">Query Embedding</span>
                <span className="font-mono text-slate-300 font-semibold">
                  {analysis?.embedding_query_ms?.toFixed(1) ?? '—'} ms
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                <span className="text-[10px] text-slate-500 font-mono block">Vector Search</span>
                <span className="font-mono text-slate-300 font-semibold">
                  {analysis?.vector_search_ms?.toFixed(1) ?? '—'} ms
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                <span className="text-[10px] text-slate-500 font-mono block">Documents Retrieved</span>
                <span className="font-mono text-slate-300 font-semibold">
                  {analysis?.retrieval_count ?? 0} FAQs
                </span>
              </div>
            </div>

            {/* Retrieved Sources & Validated Citations */}
            <div className="space-y-3 pt-2">
              <div className="text-xs font-medium text-slate-300">Retrieved FAQ Document IDs:</div>
              <div className="flex flex-wrap gap-2">
                {analysis?.retrieved_faq_ids && analysis.retrieved_faq_ids.length > 0 ? (
                  analysis.retrieved_faq_ids.map((id, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-700 text-slate-300 font-mono text-xs flex items-center space-x-1"
                    >
                      <BookOpen className="w-3 h-3 text-slate-500" />
                      <span>{id}</span>
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500 italic">No retrieved FAQs recorded.</span>
                )}
              </div>

              <div className="text-xs font-medium text-slate-300 pt-1">Validated Cited FAQs in Response:</div>
              <div className="flex flex-wrap gap-2">
                {analysis?.used_faq_ids && analysis.used_faq_ids.length > 0 ? (
                  analysis.used_faq_ids.map((id, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-mono text-xs flex items-center space-x-1"
                    >
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>{id} (Canonical Verified)</span>
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500 italic">No specific citations used.</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Grounded Response, Action Bar & Audit History (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Grounded Response Card */}
          <div className="p-6 rounded-2xl saas-card space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Bot className="w-4 h-4 text-indigo-400" />
                <span>Grounded Agent Reply</span>
              </h2>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 text-sm text-slate-200 leading-relaxed font-sans whitespace-pre-line">
              {ticket.generated_reply || 'No generated reply recorded for this ticket.'}
            </div>

            {/* Resolve AI Safety Notice */}
            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 flex items-start space-x-2.5">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div className="leading-tight">
                <strong className="text-amber-300">Resolve AI Safety Guardrail:</strong> High-risk or financial operations (e.g., refund issuance, account resets) are strictly simulated recommendations awaiting human agent review and approval.
              </div>
            </div>
          </div>

          {/* Supervisor Management Controls */}
          <form onSubmit={handleUpdate} className="p-6 rounded-2xl saas-card space-y-4">
            <div className="border-b border-slate-800/80 pb-3">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <FileCheck className="w-4 h-4 text-indigo-400" />
                <span>Human Supervisor Controls</span>
              </h2>
              <p className="text-[11px] text-slate-400 mt-1">
                Override automated agent decisions or update workflow state.
              </p>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Lifecycle Status</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value as TicketStatus)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus-ring"
                >
                  <option value="open">Open (Awaiting Agent)</option>
                  <option value="in_progress">In Progress (Agent Working)</option>
                  <option value="resolved">Resolved (Outcome Approved)</option>
                  <option value="escalated">Escalated (Senior Review)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Reassign Department</label>
                <select
                  value={editTeam}
                  onChange={(e) => setEditTeam(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus-ring"
                >
                  <option value="Finance Team">Finance Team</option>
                  <option value="Logistics Team">Logistics Team</option>
                  <option value="Tech Support">Tech Support</option>
                  <option value="General Support">General Support</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Override Urgency Priority</label>
                <select
                  value={editPriority}
                  onChange={(e) => setEditPriority(e.target.value as TicketPriority)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus-ring"
                >
                  <option value="High">High Priority</option>
                  <option value="Medium">Medium Priority</option>
                  <option value="Low">Low Priority</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={updating}
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs transition focus-ring shadow-sm"
            >
              {updating ? 'Saving Changes...' : 'Save Supervisor Decision'}
            </button>
          </form>

          {/* Audit History Timeline */}
          <div className="p-6 rounded-2xl saas-card space-y-4">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <History className="w-4 h-4 text-slate-400" />
              <span>Coordinated Audit Trail</span>
            </h2>

            <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
              {ticket.events && ticket.events.length > 0 ? (
                ticket.events.map((ev, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs space-y-1">
                    <div className="flex justify-between items-center text-slate-400">
                      <span className="font-semibold text-indigo-400 uppercase font-mono text-[11px]">{ev.event_type}</span>
                      <span className="text-[10px] font-mono">{new Date(ev.created_at).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-slate-300 text-[11px]">Actor: {ev.actor}</div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 italic">No recorded audit events.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
