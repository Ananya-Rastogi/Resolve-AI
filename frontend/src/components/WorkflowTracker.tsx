import React from 'react';
import {
  Inbox,
  Cpu,
  Flame,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  UserCheck,
  Check,
} from 'lucide-react';
import { TicketDetail } from '../types';

interface WorkflowTrackerProps {
  ticket?: TicketDetail | null;
  compact?: boolean;
}

export const WorkflowTracker: React.FC<WorkflowTrackerProps> = ({ ticket, compact = false }) => {
  const isResolved = ticket?.status === 'resolved';
  const isEscalated =
    ticket?.escalation_level !== 'Not Escalated' && ticket?.escalation_level !== 'No Escalation Required';
  const hasAnalysis = Boolean(ticket?.analysis);
  const ragUsed = Boolean(ticket?.analysis?.rag_used);

  const steps = [
    {
      id: 'ingest',
      label: 'Ticket Ingest',
      sublabel: ticket?.ticket_id || 'Submitted',
      status: 'complete',
      icon: Inbox,
    },
    {
      id: 'classify',
      label: 'AI Classification',
      sublabel: ticket?.category ? `${ticket.category} (${ticket.classification_source || 'ml'})` : 'Pending',
      status: hasAnalysis || ticket?.category ? 'complete' : 'waiting',
      icon: Cpu,
    },
    {
      id: 'priority',
      label: 'Priority Assessment',
      sublabel: ticket?.priority ? `${ticket.priority} priority` : 'Pending',
      status: ticket?.priority ? 'complete' : 'waiting',
      icon: Flame,
    },
    {
      id: 'routing',
      label: 'Agent Routing',
      sublabel: ticket?.assigned_team || 'Pending',
      status: ticket?.assigned_team ? 'complete' : 'waiting',
      icon: ArrowRight,
    },
    {
      id: 'rag',
      label: 'Knowledge Retrieval',
      sublabel: ragUsed
        ? `${ticket?.analysis?.retrieval_count ?? 3} FAQs (${ticket?.analysis?.total_retrieval_ms?.toFixed(0) ?? '—'}ms)`
        : 'Canonical RAG',
      status: ticket?.generated_reply ? 'complete' : 'waiting',
      icon: BookOpen,
    },
    {
      id: 'response',
      label: 'Grounded Response',
      sublabel: ticket?.analysis?.used_faq_ids?.length
        ? `${ticket.analysis.used_faq_ids.length} Citation(s)`
        : 'Generated',
      status: ticket?.generated_reply ? 'complete' : 'waiting',
      icon: CheckCircle2,
    },
    {
      id: 'action',
      label: isEscalated ? 'Human Escalation' : 'Human Review',
      sublabel: isResolved ? 'Resolved' : isEscalated ? 'Escalated to Lead' : 'Awaiting Review',
      status: isResolved ? 'complete' : isEscalated ? 'escalated' : 'active',
      icon: UserCheck,
    },
  ];

  if (compact) {
    return (
      <div className="flex items-center space-x-1 sm:space-x-2 text-xs overflow-x-auto py-2">
        {steps.map((step, idx) => {
          const isDone = step.status === 'complete';
          const isEsc = step.status === 'escalated';
          return (
            <React.Fragment key={step.id}>
              <div
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md border font-sans whitespace-nowrap ${
                  isEsc
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                    : isDone
                    ? 'bg-slate-900 border-slate-700/80 text-slate-200'
                    : 'bg-slate-950 border-slate-800 text-slate-500'
                }`}
              >
                {isDone ? (
                  <Check className="w-3 h-3 text-emerald-400" />
                ) : (
                  <step.icon className={`w-3 h-3 ${isEsc ? 'text-rose-400' : 'text-slate-400'}`} />
                )}
                <span className="font-medium">{step.label}</span>
              </div>
              {idx < steps.length - 1 && <span className="text-slate-600 text-[10px]">&rarr;</span>}
            </React.Fragment>
          );
        })}
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-5 rounded-xl saas-panel border border-slate-800 space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-800/80 gap-1 text-xs">
        <span className="font-semibold text-slate-200 uppercase tracking-wider font-mono">
          Coordinated Agent Execution Lifecycle
        </span>
        <span className="text-slate-400">
          State: <strong className="text-indigo-400">{ticket?.status || 'Active Pipeline'}</strong>
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 pt-1">
        {steps.map((step) => {
          const isDone = step.status === 'complete';
          const isEsc = step.status === 'escalated';
          const isActive = step.status === 'active';
          const Icon = step.icon;

          return (
            <div
              key={step.id}
              className={`p-2.5 rounded-lg border flex flex-col justify-between transition ${
                isEsc
                  ? 'bg-rose-950/20 border-rose-500/40 text-rose-200'
                  : isActive
                  ? 'bg-indigo-950/20 border-indigo-500/40 text-indigo-200'
                  : isDone
                  ? 'bg-slate-900/80 border-slate-800 text-slate-200'
                  : 'bg-slate-950 border-slate-850 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <Icon
                  className={`w-3.5 h-3.5 ${
                    isEsc ? 'text-rose-400' : isActive ? 'text-indigo-400' : isDone ? 'text-emerald-400' : 'text-slate-500'
                  }`}
                />
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isEsc ? 'bg-rose-400' : isActive ? 'bg-indigo-400 animate-pulse' : isDone ? 'bg-emerald-400' : 'bg-slate-600'
                  }`}
                />
              </div>
              <div>
                <div className="text-[11px] font-semibold tracking-tight leading-tight">{step.label}</div>
                <div className="text-[10px] text-slate-400 font-mono truncate mt-0.5" title={step.sublabel}>
                  {step.sublabel}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
