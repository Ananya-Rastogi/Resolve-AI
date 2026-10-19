import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  LayoutDashboard,
  CheckCircle2,
  Clock,
  ArrowRight,
  ArrowLeft,
  X,
  Bot,
  Layers,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { BrandSymbol } from './BrandLogo';
import { User } from '@supabase/supabase-js';
import { UserProfile } from '../types';

interface OnboardingTourProps {
  isOpen: boolean;
  onClose: () => void;
  onStartTicket: () => void;
  user?: User | null;
  profile?: UserProfile | null;
  updateProfile?: (updates: any) => Promise<any>;
}

export const OnboardingTour: React.FC<OnboardingTourProps> = ({
  isOpen,
  onClose,
  onStartTicket,
  user,
  profile,
  updateProfile,
}) => {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') handleSkip();
      if (e.key === 'ArrowRight' && currentStep < steps.length - 1) handleNext();
      if (e.key === 'ArrowLeft' && currentStep > 0) handlePrev();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentStep]);

  if (!isOpen) return null;

  const markCompleted = async () => {
    try {
      const userKey = user?.id || user?.email || 'default';
      localStorage.setItem('resolve_onboarding_' + userKey, 'true');
      if (updateProfile && profile) {
        await updateProfile({
          preferences: {
            ...(profile.preferences || {}),
            onboarding_completed: true,
          },
        });
      }
    } catch (e) {
      console.warn('Error saving onboarding state:', e);
    }
  };

  const handleSkip = async () => {
    await markCompleted();
    onClose();
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleFinish = async () => {
    await markCompleted();
    onClose();
    onStartTicket();
  };

  const steps = [
    {
      badge: 'Welcome',
      title: 'Welcome to Resolve AI',
      subtitle: 'Enterprise Multi-Agent Ticket Resolution Platform',
      icon: Bot,
      color: 'indigo',
      description:
        'Resolve AI automates complex customer support workflows using specialized AI agents, ChromaDB knowledge grounding, and human-in-the-loop controls.',
      highlights: [
        { icon: Zap, label: 'ML & LLM Triage', desc: 'Instant classification and urgency analysis' },
        { icon: Layers, label: 'ChromaDB Grounding', desc: 'Verified FAQ search with cited sources' },
        { icon: ShieldCheck, label: 'Duplicate Detection', desc: 'Real-time prevention of duplicate tickets' },
      ],
    },
    {
      badge: 'Overview',
      title: 'Real-Time Dashboard',
      subtitle: 'Operational Telemetry at a Glance',
      icon: LayoutDashboard,
      color: 'blue',
      description:
        'Your dashboard provides clean, focused visibility into open tickets, resolution status, high-priority issues, and department distributions derived from live database data.',
      highlights: [
        { icon: Sparkles, label: '4 Primary KPIs', desc: 'Total, open, resolved, and high-priority metrics' },
        { icon: Clock, label: 'Needs Attention', desc: 'Urgent queue alerts and senior review monitoring' },
        { icon: Layers, label: 'Dynamic Analytics', desc: 'Toggleable category and priority distributions' },
      ],
    },
    {
      badge: 'Automation',
      title: 'Intelligent Ticket Triage',
      subtitle: 'Multi-Agent Processing Pipeline',
      icon: Sparkles,
      color: 'violet',
      description:
        'Create tickets with automatic routing. Each inquiry passes through ML topic classification, LLM entity extraction (orders, deadlines), and automated duplicate checking.',
      highlights: [
        { icon: Zap, label: 'Auto-Routing', desc: 'Direct assignment to Finance, Tech, or Logistics' },
        { icon: ShieldCheck, label: 'Duplicate Warnings', desc: 'Similarity matching against existing queue' },
        { icon: Bot, label: 'AI Response Drafts', desc: 'Contextually generated replies with citations' },
      ],
    },
    {
      badge: 'Quality & SLAs',
      title: 'Queue & Resolution SLAs',
      subtitle: 'Never Miss a Service Commitment',
      icon: Clock,
      color: 'amber',
      description:
        'Stay on top of customer commitments. Dynamic SLA indicators calculate exact deadlines across Platinum, Gold, Silver, and Bronze tiers with clear overdue warnings.',
      highlights: [
        { icon: Clock, label: 'Live Timers', desc: 'On Track, Due Soon, and Overdue countdowns' },
        { icon: Layers, label: 'Queue Filtering', desc: 'Instant filter by team, priority, or category' },
        { icon: ShieldCheck, label: 'Audit Trail', desc: 'Complete chronological history for every ticket' },
      ],
    },
    {
      badge: 'Get Started',
      title: "You're All Set!",
      subtitle: 'Ready to Resolve Customer Inquiries',
      icon: CheckCircle2,
      color: 'emerald',
      description:
        'Your workspace is configured with complete data isolation. You can reopen this tour anytime from Settings or the floating Help Assistant.',
      highlights: [
        { icon: ShieldCheck, label: 'Private Workspace', desc: 'Your tickets are strictly isolated and secure' },
        { icon: Bot, label: 'Help Assistant', desc: 'Ask questions or explore features anytime' },
        { icon: Zap, label: 'Instant Triage', desc: 'Submit a ticket to see the AI agent pipeline' },
      ],
    },
  ];

  const current = steps[currentStep];
  const StepIcon = current.icon;
  const isLast = currentStep === steps.length - 1;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Welcome and Onboarding Tour"
      className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fade-in"
    >
      <div className="relative w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8 space-y-6">
        {/* Progress Bar & Header Controls */}
        <div>
          <div className="flex items-center justify-between pb-3">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/20">
                {current.badge}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {currentStep + 1} of {steps.length}
              </span>
            </div>
            <button
              onClick={handleSkip}
              className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition focus-ring rounded p-1"
              aria-label="Close onboarding tour"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-indigo-600 h-full transition-all duration-300 ease-out"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Step Content */}
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-200 dark:border-indigo-500/20 flex items-center justify-center shrink-0 text-indigo-600 dark:text-indigo-400">
              <StepIcon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                {current.title}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                {current.subtitle}
              </p>
            </div>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {current.description}
          </p>

          {/* Highlights List */}
          <div className="space-y-2 pt-1">
            {current.highlights.map((h, i) => {
              const HIcon = h.icon;
              return (
                <div
                  key={i}
                  className="flex items-start space-x-2.5 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800/80"
                >
                  <HIcon className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                  <div className="text-xs">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {h.label}:{' '}
                    </span>
                    <span className="text-slate-600 dark:text-slate-400">{h.desc}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Action Controls */}
        <div className="pt-2 flex items-center justify-between border-t border-slate-100 dark:border-slate-800">
          <button
            onClick={handleSkip}
            className="text-xs font-medium text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition focus-ring rounded py-1 px-1.5"
          >
            Skip Tour
          </button>

          <div className="flex items-center space-x-2">
            {currentStep > 0 && (
              <button
                onClick={handlePrev}
                className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition focus-ring"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>
            )}

            {!isLast ? (
              <button
                onClick={handleNext}
                className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition focus-ring"
              >
                <span>Next</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={handleFinish}
                className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition focus-ring shadow-indigo-500/20"
              >
                <span>Create Your First Ticket</span>
                <Sparkles className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
