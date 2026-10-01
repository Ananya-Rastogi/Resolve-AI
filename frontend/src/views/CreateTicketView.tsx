import React, { useState } from 'react';
import {
  Send,
  AlertCircle,
  CheckCircle,
  User,
  Mail,
  CreditCard,
  ShieldAlert,
  ArrowRight,
  BookOpen,
} from 'lucide-react';
import { createTicket } from '../api';
import { TicketDetail } from '../types';
import { StatusBadge, PriorityBadge, TopicBadge, TierBadge, SourceBadge } from '../components/Badges';
import { BRAND_CONFIG } from '../config/brand';
import { BrandSymbol } from '../components/BrandLogo';
import { WorkflowTracker } from '../components/WorkflowTracker';

interface CreateTicketViewProps {
  onNavigate: (view: string, ticketId?: string) => void;
}

export const CreateTicketView: React.FC<CreateTicketViewProps> = ({ onNavigate }) => {
  const [subject, setSubject] = useState('');
  const [customerName, setCustomerName] = useState('Sarah Jenkins');
  const [email, setEmail] = useState('sarah.jenkins@enterprise.io');
  const [customerId, setCustomerId] = useState('CUST-8492');
  const [tier, setTier] = useState('Gold');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TicketDetail | null>(null);

  // One-click demo presets
  const demoPresets = [
    {
      label: 'Duplicate Charge (Billing)',
      text: 'I was charged twice on my credit card for invoice #INV-20491. Please issue an immediate refund for the $149.00 duplicate deduction.',
      tier: 'Platinum',
      name: 'Michael Vance',
    },
    {
      label: 'Express Delay (Shipping)',
      text: 'My expedited package with tracking ID TRK-881290 has been stuck in transit for 4 days past the guaranteed delivery date. Where is my parcel?',
      tier: 'Gold',
      name: 'Jessica Reynolds',
    },
    {
      label: 'API Lockout (Technical)',
      text: 'Getting HTTP 403 Forbidden errors when calling the production REST API endpoints after resetting our corporate service credentials.',
      tier: 'Silver',
      name: 'DevOps Lead',
    },
    {
      label: 'General Inquiry (Other)',
      text: 'Do you have open career opportunities for senior distributed systems engineers on your cloud infrastructure team?',
      tier: 'Bronze',
      name: 'Alex Rivera',
    },
    {
      label: 'Unsupported / Crypto (Abstention)',
      text: 'Can I pay for my annual enterprise subscription using Ethereum or Bitcoin cryptocurrency tokens directly from a cold wallet?',
      tier: 'Platinum',
      name: 'Crypto Investor',
    },
  ];

  const handleApplyPreset = (preset: (typeof demoPresets)[0]) => {
    setSubject(preset.text);
    setTier(preset.tier);
    setCustomerName(preset.name);
    setEmail(`${preset.name.toLowerCase().replace(/\s+/g, '.')}@example.com`);
    setCustomerId(`CUST-${Math.floor(1000 + Math.random() * 9000)}`);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim()) {
      setError('Please provide an issue description before submitting.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const ticket = await createTicket({
        subject: subject.trim(),
        customer_name: customerName.trim() || undefined,
        customer_id: customerId.trim() || undefined,
        email: email.trim() || undefined,
        tier,
      });
      setResult(ticket);
    } catch (err: any) {
      setError(err.message || 'An error occurred during ticket triage.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <div className="flex items-center space-x-3">
          <BrandSymbol size="sm" />
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Ingest & Triage Ticket
          </h1>
        </div>
        <p className="text-sm text-slate-400 mt-1.5">
          Execute the {BRAND_CONFIG.name} multi-agent orchestration pipeline: classical ML classification, confidence-evaluated LLM fallback, ChromaDB RAG retrieval, and grounded response generation.
        </p>
      </div>

      {/* Demo Presets Bar */}
      <div className="p-4 rounded-xl saas-panel border border-slate-800 space-y-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 font-mono">
          Demo Scenarios (One-Click Pre-fill):
        </span>
        <div className="flex flex-wrap gap-2">
          {demoPresets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleApplyPreset(preset)}
              className="px-3 py-1.5 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs font-medium text-slate-300 hover:text-white transition focus-ring"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="p-6 sm:p-7 rounded-xl saas-card space-y-5">
        {error && (
          <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Submission Error</p>
              <p className="text-rose-200 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Issue Description */}
        <div className="space-y-1.5">
          <label htmlFor="subject" className="block text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Issue Description / Customer Inquiry <span className="text-rose-400">*</span>
          </label>
          <textarea
            id="subject"
            rows={4}
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Describe the issue, enter error messages, or ask an account question..."
            required
            className="w-full px-3.5 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus-ring text-sm font-sans"
          />
        </div>

        {/* Customer & Account Details */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 flex items-center space-x-1">
              <User className="w-3.5 h-3.5 text-slate-500" />
              <span>Customer Name</span>
            </label>
            <input
              type="text"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-200 text-xs focus-ring"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 flex items-center space-x-1">
              <Mail className="w-3.5 h-3.5 text-slate-500" />
              <span>Customer Email</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-200 text-xs focus-ring"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 flex items-center space-x-1">
              <CreditCard className="w-3.5 h-3.5 text-slate-500" />
              <span>Account ID</span>
            </label>
            <input
              type="text"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-200 text-xs focus-ring font-mono"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 flex items-center space-x-1">
              <ShieldAlert className="w-3.5 h-3.5 text-slate-500" />
              <span>Customer Tier</span>
            </label>
            <select
              value={tier}
              onChange={(e) => setTier(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-200 text-xs focus-ring"
            >
              <option value="Platinum">Platinum (Auto-Escalate on High)</option>
              <option value="Gold">Gold (Auto-Escalate on High)</option>
              <option value="Silver">Silver</option>
              <option value="Bronze">Bronze (Standard)</option>
            </select>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-lg font-semibold text-xs text-white shadow-sm transition focus-ring ${
              loading
                ? 'bg-slate-800 cursor-not-allowed text-slate-400'
                : 'bg-indigo-600 hover:bg-indigo-500'
            }`}
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Coordinating Agents...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Submit to {BRAND_CONFIG.name}</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Immediate Triage Result Preview */}
      {result && (
        <div className="p-6 sm:p-7 rounded-xl saas-card border-indigo-500/40 space-y-5 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-2">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
                <CheckCircle className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <span>Triage Complete:</span>
                  <span className="font-mono text-indigo-400">{result.ticket_id}</span>
                </h3>
                <p className="text-[11px] text-slate-400">Record successfully persisted into operational database.</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <StatusBadge status={result.status} />
              <PriorityBadge priority={result.priority} />
              <SourceBadge source={result.classification_source} />
            </div>
          </div>

          {/* Workflow Tracker */}
          <WorkflowTracker ticket={result} compact={true} />

          {/* AI Decision Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono block">Assigned Topic</span>
              <div className="mt-1">
                <TopicBadge topic={result.category} />
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono block">Sentiment</span>
              <span
                className={`text-xs font-bold uppercase mt-1 inline-block ${
                  result.sentiment === 'POSITIVE' ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {result.sentiment}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono block">Assigned Team</span>
              <span className="text-xs font-semibold text-slate-200 mt-1 block">
                {result.assigned_team || 'General Support'}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono block">Escalation Status</span>
              <span
                className={`text-xs font-semibold mt-1 block ${
                  result.escalation_level !== 'Not Escalated' && result.escalation_level !== 'No Escalation Required'
                    ? 'text-rose-400 font-bold'
                    : 'text-slate-300'
                }`}
              >
                {result.escalation_level}
              </span>
            </div>
          </div>

          {/* Grounded AI Response */}
          {result.generated_reply && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold uppercase tracking-wider font-mono flex items-center space-x-1.5 text-slate-300 text-[11px]">
                  <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Grounded Knowledge Base Resolution</span>
                </span>
                {result.analysis?.rag_used && (
                  <span className="text-emerald-400 font-mono text-[11px]">
                    Retrieved {result.analysis.retrieval_count} FAQs ({result.analysis.total_retrieval_ms?.toFixed(1)}ms)
                  </span>
                )}
              </div>
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs sm:text-sm text-slate-200 leading-relaxed font-sans whitespace-pre-line">
                {result.generated_reply}
              </div>
            </div>
          )}

          {/* Citations Preview */}
          {result.analysis?.used_faq_ids && result.analysis.used_faq_ids.length > 0 && (
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400 font-medium">Validated Citations:</span>
              <div className="flex flex-wrap gap-1.5">
                {result.analysis.used_faq_ids.map((id, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono text-[11px]"
                  >
                    {id}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Action Footer */}
          <div className="flex justify-end space-x-2.5 pt-2">
            <button
              onClick={() => setResult(null)}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition focus-ring"
            >
              Dismiss
            </button>
            <button
              onClick={() => onNavigate('detail', result.ticket_id)}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition focus-ring"
            >
              <span>View Full Lifecycle Details</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
