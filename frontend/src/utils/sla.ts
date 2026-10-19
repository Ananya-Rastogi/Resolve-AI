import { TicketPriority, TicketStatus, SLAStatusInfo } from '../types';

interface SLARules {
  resolutionHours: number;
  responseHours: number;
}

const SLA_RULES: Record<TicketPriority, SLARules> = {
  High: { resolutionHours: 4, responseHours: 1 },
  Medium: { resolutionHours: 24, responseHours: 4 },
  Low: { resolutionHours: 72, responseHours: 12 },
};

export function calculateTicketSLA(
  priority: TicketPriority = 'Medium',
  createdAtIso: string,
  status: TicketStatus = 'open'
): SLAStatusInfo {
  if (status === 'resolved') {
    return {
      status: 'Resolved',
      timeRemaining: 'Completed',
      deadlineText: 'Resolved within SLA',
      isOverdue: false,
      colorClass: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
    };
  }

  if (status === 'escalated') {
    return {
      status: 'Needs Review',
      timeRemaining: 'Senior team review required',
      deadlineText: 'Escalated for review',
      isOverdue: false,
      colorClass: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200 dark:border-amber-800',
    };
  }

  const createdTime = new Date(createdAtIso).getTime();
  if (isNaN(createdTime)) {
    return {
      status: 'On Track',
      timeRemaining: 'Standard window',
      deadlineText: 'Pending review',
      isOverdue: false,
      colorClass: 'bg-slate-50 text-slate-700 dark:bg-slate-900 dark:text-slate-300 border-slate-200 dark:border-slate-800',
    };
  }

  const rule = SLA_RULES[priority] || SLA_RULES.Medium;
  const totalWindowMs = rule.resolutionHours * 60 * 60 * 1000;
  const deadlineTime = createdTime + totalWindowMs;
  const now = Date.now();
  const diffMs = deadlineTime - now;

  const deadlineDate = new Date(deadlineTime).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    month: 'short',
    day: 'numeric',
  });

  if (diffMs <= 0) {
    const overdueMs = Math.abs(diffMs);
    const overdueHours = Math.floor(overdueMs / (1000 * 60 * 60));
    const overdueMins = Math.floor((overdueMs % (1000 * 60 * 60)) / (1000 * 60));
    const timeText = overdueHours > 0 ? `${overdueHours}h ${overdueMins}m` : `${overdueMins}m`;

    return {
      status: 'Overdue',
      timeRemaining: `Overdue by ${timeText}`,
      deadlineText: `Deadline was ${deadlineDate}`,
      isOverdue: true,
      colorClass: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 border-rose-200 dark:border-rose-800',
    };
  }

  const hoursRemaining = Math.floor(diffMs / (1000 * 60 * 60));
  const minsRemaining = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  const timeText = hoursRemaining > 0 ? `${hoursRemaining}h ${minsRemaining}m remaining` : `${minsRemaining}m remaining`;

  // If less than 25% of time remaining or less than 1 hour
  const isDueSoon = diffMs < totalWindowMs * 0.25 || diffMs < 60 * 60 * 1000;

  if (isDueSoon) {
    return {
      status: 'Due Soon',
      timeRemaining: timeText,
      deadlineText: `Due by ${deadlineDate}`,
      isOverdue: false,
      colorClass: 'bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400 border-orange-200 dark:border-orange-800',
    };
  }

  return {
    status: 'On Track',
    timeRemaining: timeText,
    deadlineText: `Target: ${deadlineDate}`,
    isOverdue: false,
    colorClass: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  };
}
