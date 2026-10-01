import React from 'react';
import { CustomerTier, TicketPriority, TicketStatus, TicketTopic } from '../types';

export const StatusBadge: React.FC<{ status: TicketStatus | string; className?: string }> = ({
  status,
  className = '',
}) => {
  const styles: Record<string, string> = {
    open: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
    in_progress: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
    resolved: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
    escalated: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  };

  const labels: Record<string, string> = {
    open: 'Open',
    in_progress: 'In Progress',
    resolved: 'Resolved',
    escalated: 'Escalated',
  };

  const style = styles[status] || 'bg-slate-800 text-slate-300 border-slate-700';
  const label = labels[status] || status;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border font-sans ${style} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-90" />
      {label}
    </span>
  );
};

export const PriorityBadge: React.FC<{ priority: TicketPriority | string; className?: string }> = ({
  priority,
  className = '',
}) => {
  const styles: Record<string, string> = {
    High: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
    Medium: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
    Low: 'bg-slate-800/80 text-slate-400 border-slate-700/60',
  };

  const style = styles[priority] || 'bg-slate-800 text-slate-300 border-slate-700';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border font-sans ${style} ${className}`}
    >
      {priority} Priority
    </span>
  );
};

export const TierBadge: React.FC<{ tier: CustomerTier | string; className?: string }> = ({
  tier,
  className = '',
}) => {
  const styles: Record<string, string> = {
    Platinum: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
    Gold: 'bg-amber-400/10 text-amber-200 border-amber-400/20',
    Silver: 'bg-slate-400/10 text-slate-300 border-slate-500/20',
    Bronze: 'bg-orange-500/10 text-orange-300 border-orange-500/20',
  };

  const style = styles[tier] || 'bg-slate-800 text-slate-300 border-slate-700';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border font-sans ${style} ${className}`}
    >
      {tier}
    </span>
  );
};

export const TopicBadge: React.FC<{ topic?: TicketTopic | string; className?: string }> = ({
  topic,
  className = '',
}) => {
  if (!topic) return <span className="text-slate-500 text-xs">Unassigned</span>;

  const styles: Record<string, string> = {
    billing: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
    shipping: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20',
    technical: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
    other: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  const style = styles[topic.toLowerCase()] || 'bg-slate-800 text-slate-300 border-slate-700';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border uppercase tracking-wider font-mono ${style} ${className}`}
    >
      {topic}
    </span>
  );
};

export const SourceBadge: React.FC<{ source?: string; className?: string }> = ({
  source,
  className = '',
}) => {
  if (!source) return null;

  if (source === 'ml') {
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 ${className}`}
        title="Direct fast-path classification by scikit-learn Naive Bayes & Logistic Regression"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5" />
        ML Fast-Path
      </span>
    );
  }
  if (source === 'llm') {
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 ${className}`}
        title="Confidence < threshold: triage escalated to structured LLM classification"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mr-1.5" />
        LLM Fallback
      </span>
    );
  }
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20 ${className}`}
      title="Safe fallback to ML prediction"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5" />
      Safe ML Fallback
    </span>
  );
};
