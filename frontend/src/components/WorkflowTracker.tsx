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
      label: 'Ticket Created',
      sublabel: ticket?.ticket_id || 'Submitted',
      status: 'complete',
      icon: Inbox,
    },
    {
      id: 'classify',
      label: 'Category Match',
      sublabel: ticket?.category ? `${ticket.category} (${ticket.classification_source === 'llm' ? 'Deep AI' : 'Fast Match'})` : 'Waiting',
      status: hasAnalysis || ticket?.category ? 'complete' : 'waiting',
      icon: Cpu,
    },
    {
      id: 'priority',
      label: 'Priority Check',
      sublabel: ticket?.priority ? `${ticket.priority} priority` : 'Waiting',
      status: ticket?.priority ? 'complete' : 'waiting',
      icon: Flame,
    },
    {
      id: 'routing',
      label: 'Team Assignment',
      sublabel: ticket?.assigned_team || 'Waiting',
      status: ticket?.assigned_team ? 'complete' : 'waiting',
      icon: ArrowRight,
    },
    {
      id: 'rag',
      label: 'Answer Search',
      sublabel: ragUsed
        ? `${ticket?.analysis?.retrieval_count ?? 3} Answers Found`
        : 'FAQ Search',
      status: ticket?.generated_reply ? 'complete' : 'waiting',
      icon: BookOpen,
    },
    {
      id: 'response',
      label: 'Suggested Reply',
      sublabel: ticket?.analysis?.used_faq_ids?.length
        ? `${ticket.analysis.used_faq_ids.length} Citation(s)`
        : 'Draft Ready',
      status: ticket?.generated_reply ? 'complete' : 'waiting',
      icon: CheckCircle2,
    },
    {
      id: 'action',
      label: isEscalated ? 'Senior Review' : 'Team Review',
      sublabel: isResolved ? 'Resolved' : isEscalated ? 'Sent to Senior Lead' : 'Ready for Review',
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
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md border font-sans whitespace-nowrap transition-colors ${
                  isEsc
                    ? 'bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-500/30 text-rose-700 dark:text-rose-300'
                    : isDone
                    ? 'bg-slate-100 dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200'
                    : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-400 dark:text-slate-500'
                }`}
              >
                {isDone ? (
                  <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                ) : (
                  <step.icon className={`w-3 h-3 ${isEsc ? 'text-rose-600 dark:text-rose-400' : 'text-slate-400 dark:text-slate-500'}`} />
                )}
                <span className="font-medium">{step.label}</span>
              </div>
              {idx < steps.length - 1 && <span className="text-slate-400 dark:text-slate-600 text-[10px]">&rarr;</span>}
            </React.Fragment>
          );
        })}
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-5 rounded-xl saas-card space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800 gap-1 text-xs">
        <span className="font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider font-mono">
          Ticket Progress Steps
        </span>
        <span className="text-slate-500 dark:text-slate-400">
          Current State: <strong className="text-indigo-600 dark:text-indigo-400 capitalize">{ticket?.status || 'Active'}</strong>
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
              className={`p-2.5 rounded-lg border flex flex-col justify-between transition-colors ${
                isEsc
                  ? 'bg-rose-50 dark:bg-rose-950/20 border-rose-300 dark:border-rose-500/40 text-rose-800 dark:text-rose-200'
                  : isActive
                  ? 'bg-indigo-50 dark:bg-indigo-950/20 border-indigo-300 dark:border-indigo-500/40 text-indigo-900 dark:text-indigo-200'
                  : isDone
                  ? 'bg-slate-50 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200'
                  : 'bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-850 text-slate-400 dark:text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <Icon
                  className={`w-3.5 h-3.5 ${
                    isEsc ? 'text-rose-600 dark:text-rose-400' : isActive ? 'text-indigo-600 dark:text-indigo-400' : isDone ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-slate-500'
                  }`}
                />
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isEsc ? 'bg-rose-500' : isActive ? 'bg-indigo-500 animate-pulse' : isDone ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                />
              </div>
              <div>
                <div className="text-[11px] font-semibold tracking-tight leading-tight">{step.label}</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono truncate mt-0.5" title={step.sublabel}>
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
