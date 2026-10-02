import React from 'react';
import { CustomerTier, TicketPriority, TicketStatus, TicketTopic } from '../types';

export const StatusBadge: React.FC<{ status: TicketStatus | string; className?: string }> = ({
  status,
  className = '',
}) => {
  const styles: Record<string, string> = {
    open: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-500/20',
    in_progress: 'bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-500/20',
    resolved: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/20',
    escalated: 'bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-500/20',
  };

  const labels: Record<string, string> = {
    open: 'Open',
    in_progress: 'In Progress',
    resolved: 'Resolved',
    escalated: 'Sent to Senior Team',
  };

  const style = styles[status] || 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';
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
    High: 'bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-500/20',
    Medium: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-500/20',
    Low: 'bg-slate-100 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700/60',
  };

  const style = styles[priority] || 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';

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
    Platinum: 'bg-purple-50 dark:bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-500/20',
    Gold: 'bg-amber-50 dark:bg-amber-400/10 text-amber-700 dark:text-amber-200 border-amber-200 dark:border-amber-400/20',
    Silver: 'bg-slate-100 dark:bg-slate-400/10 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-500/20',
    Bronze: 'bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-500/20',
  };

  const style = styles[tier] || 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border font-sans ${style} ${className}`}
    >
      {tier} Tier
    </span>
  );
};

export const TopicBadge: React.FC<{ topic?: TicketTopic | string; className?: string }> = ({
  topic,
  className = '',
}) => {
  if (!topic) return <span className="text-slate-400 text-xs">Unassigned</span>;

  const styles: Record<string, string> = {
    billing: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/20',
    shipping: 'bg-cyan-50 dark:bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border-cyan-200 dark:border-cyan-500/20',
    technical: 'bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-500/20',
    other: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700',
  };

  const labels: Record<string, string> = {
    billing: 'Billing & Charges',
    shipping: 'Shipping & Delivery',
    technical: 'Technical Support',
    other: 'General Inquiry',
  };

  const style = styles[topic.toLowerCase()] || 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';
  const label = labels[topic.toLowerCase()] || topic;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${style} ${className}`}
    >
      {label}
    </span>
  );
};

export const SentimentBadge: React.FC<{ sentiment?: string; className?: string }> = ({
  sentiment,
  className = '',
}) => {
  if (!sentiment) return null;
  const isPositive = sentiment.toUpperCase() === 'POSITIVE';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${
        isPositive
          ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/20'
          : 'bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-500/20'
      } ${className}`}
      title={isPositive ? 'Customer tone is calm or positive' : 'Customer tone is frustrated or urgent'}
    >
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${isPositive ? 'bg-emerald-500' : 'bg-rose-500'}`} />
      {isPositive ? 'Calm / Positive Mood' : 'Frustrated / Urgent Mood'}
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
        className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/20 ${className}`}
        title="Immediate pattern matching (Machine Learning)"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
        Fast Pattern Match
      </span>
    );
  }
  if (source === 'llm') {
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/20 ${className}`}
        title="Uncertain ticket analyzed deeply by AI language model"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mr-1.5" />
        Deep AI Analysis
      </span>
    );
  }
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-500/20 ${className}`}
      title="Safe fallback to pattern matching"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5" />
      Safety Fallback
    </span>
  );
};
