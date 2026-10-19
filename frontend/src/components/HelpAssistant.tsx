import React, { useState, useRef, useEffect } from 'react';
import {
  Bot,
  Send,
  X,
  RotateCcw,
  Sparkles,
  ArrowRight,
  HelpCircle,
  AlertCircle,
  ChevronDown,
  ExternalLink,
} from 'lucide-react';
import { sendHelpChatMessage } from '../api';
import { ChatMessage, HelpChatResponse } from '../types';

interface HelpAssistantProps {
  currentPage: string;
  onNavigate: (view: string, ticketId?: string) => void;
}

interface DisplayMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  suggestedActions?: HelpChatResponse['suggested_actions'];
  timestamp: Date;
  isError?: boolean;
}

const DEFAULT_SUGGESTED_QUESTIONS = [
  'Take product tour',
  'How does ticket priority work?',
  'How do I create a ticket?',
  'What are the SLA deadlines?',
  'How do duplicate checks work?',
  'How does AI classification work?',
];

export const HelpAssistant: React.FC<HelpAssistantProps> = ({ currentPage, onNavigate }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastUserPrompt, setLastUserPrompt] = useState<string | null>(null);

  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hello! I'm your Resolve AI Assistant. How can I help you navigate, calculate SLAs, or manage tickets today?",
      suggestedActions: [
        { label: 'Take Product Tour', prompt: 'Take product tour' },
        { label: 'How does priority work?', prompt: 'How does ticket priority work?' },
        { label: 'How do I create a ticket?', prompt: 'How do I create a ticket?' },
        { label: 'What are the SLA rules?', prompt: 'What are the SLA deadlines?' },
      ],
      timestamp: new Date(),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, messages]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMessageId = `msg-${Date.now()}`;
    const userMsg: DisplayMessage = {
      id: userMessageId,
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    // Update conversation state immediately
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setLastUserPrompt(query);

    if (
      query.toLowerCase().includes('tour') ||
      query.toLowerCase().includes('walkthrough') ||
      query.toLowerCase().includes('onboarding')
    ) {
      const assistantMsg: DisplayMessage = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content:
          "Launching the 5-step interactive onboarding tour for Resolve AI now! Follow the highlighted cards to explore the platform.",
        suggestedActions: [
          { label: 'How does priority work?', prompt: 'How does ticket priority work?' },
          { label: 'How do I create a ticket?', prompt: 'How do I create a ticket?' },
        ],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      window.dispatchEvent(new CustomEvent('resolve-open-tour'));
      return;
    }

    setLoading(true);

    try {
      // Build history for backend (excluding error messages)
      const historyPayload: ChatMessage[] = updatedMessages
        .filter((m) => !m.isError)
        .slice(-6)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const res: HelpChatResponse = await sendHelpChatMessage(
        query,
        currentPage,
        historyPayload
      );

      const assistantMsg: DisplayMessage = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: res.reply || 'I am ready to assist with any questions about Resolve AI.',
        suggestedActions: res.suggested_actions,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: DisplayMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content:
          err.message ||
          'Unable to connect to the Help Assistant service. Please verify backend connectivity.',
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([
      {
        id: 'welcome-reset',
        role: 'assistant',
        content:
          "Conversation reset. How can I help you navigate or manage tickets in Resolve AI?",
        suggestedActions: [
          { label: 'How does priority work?', prompt: 'How does ticket priority work?' },
          { label: 'How do I create a ticket?', prompt: 'How do I create a ticket?' },
        ],
        timestamp: new Date(),
      },
    ]);
    setInput('');
    setLastUserPrompt(null);
  };

  const formatPageName = (page: string) => {
    switch (page) {
      case 'dashboard':
        return 'Overview';
      case 'create':
        return 'Create Ticket';
      case 'queue':
        return 'Ticket Queue';
      case 'detail':
        return 'Ticket Detail';
      case 'evaluation':
        return 'Quality Eval';
      case 'account':
        return 'Account Profile';
      case 'settings':
        return 'Settings';
      default:
        return page;
    }
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <div className="fixed bottom-6 right-6 z-40 print:hidden">
        <button
          onClick={() => setIsOpen((prev) => !prev)}
          className={`flex items-center space-x-2 px-4 py-3 rounded-full font-semibold text-xs shadow-lg transition-all duration-200 focus-ring ${
            isOpen
              ? 'bg-slate-800 dark:bg-slate-700 text-white hover:bg-slate-900'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5'
          }`}
          aria-label={isOpen ? 'Close Resolve AI Assistant' : 'Open Resolve AI Assistant'}
          title={isOpen ? 'Close Assistant' : 'Ask Resolve AI Assistant'}
        >
          {isOpen ? (
            <>
              <X className="w-4 h-4" />
              <span>Close Help</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>Help Assistant</span>
            </>
          )}
        </button>
      </div>

      {/* Floating Chat Panel */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="Resolve AI Help Assistant"
          className="fixed bottom-20 right-4 sm:right-6 z-50 w-[calc(100vw-2rem)] sm:w-[400px] h-[540px] max-h-[calc(100vh-6.5rem)] flex flex-col rounded-2xl bg-white dark:bg-[#0E1320] border border-slate-200 dark:border-slate-800 shadow-2xl shadow-indigo-500/10 dark:shadow-black/70 overflow-hidden transition-all duration-200"
        >
          {/* Panel Header */}
          <div className="px-4 py-3.5 bg-slate-50 dark:bg-[#13192B] border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center space-x-1.5">
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                    Resolve AI Assistant
                  </h3>
                  <span className="flex items-center space-x-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
                    <span>Ready</span>
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                  Context: <span className="text-indigo-600 dark:text-indigo-300 font-semibold">{formatPageName(currentPage)}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              <button
                type="button"
                onClick={handleReset}
                title="Reset conversation"
                className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 transition focus-ring"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Close chat panel"
                className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 transition focus-ring"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none'
                      : msg.isError
                      ? 'bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 rounded-bl-none'
                      : 'bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800/80 text-slate-800 dark:text-slate-200 rounded-bl-none'
                  }`}
                >
                  {msg.isError && (
                    <div className="flex items-center space-x-1.5 text-rose-600 dark:text-rose-400 font-semibold mb-1">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>Request Error</span>
                    </div>
                  )}

                  {/* Render response safely as plain text */}
                  <p className="whitespace-pre-line leading-relaxed font-sans">{msg.content}</p>

                  {/* Retry Option on Error */}
                  {msg.isError && lastUserPrompt && (
                    <div className="mt-2 pt-2 border-t border-rose-200/50 dark:border-rose-800/50">
                      <button
                        type="button"
                        onClick={() => handleSendMessage(lastUserPrompt)}
                        className="px-2 py-1 rounded bg-rose-600 hover:bg-rose-700 text-white text-[11px] font-semibold transition focus-ring"
                      >
                        Retry Last Question
                      </button>
                    </div>
                  )}
                </div>

                {/* Suggested Action Chips from Backend */}
                {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2 max-w-[90%]">
                    {msg.suggestedActions.map((action, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          if (
                            action.label.toLowerCase().includes('tour') ||
                            (action.prompt && action.prompt.toLowerCase().includes('tour'))
                          ) {
                            window.dispatchEvent(new CustomEvent('resolve-open-tour'));
                            setIsOpen(false);
                            return;
                          }
                          if (action.view) {
                            onNavigate(action.view);
                          } else if (action.prompt) {
                            handleSendMessage(action.prompt);
                          }
                        }}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/50 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 border border-indigo-200 dark:border-indigo-800/80 text-indigo-700 dark:text-indigo-300 font-medium text-[11px] transition focus-ring"
                      >
                        <span>{action.label}</span>
                        {action.view ? (
                          <ArrowRight className="w-3 h-3 text-indigo-500" />
                        ) : (
                          <Sparkles className="w-2.5 h-2.5 text-indigo-400" />
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex items-start">
                <div className="max-w-[85%] rounded-2xl rounded-bl-none px-3.5 py-2.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.2s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.4s]" />
                  </div>
                  <span className="text-[11px] font-mono">Consulting Resolve AI...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions Starter Bar (shown when only welcome message is present) */}
          {messages.length <= 1 && (
            <div className="px-4 py-2 border-t border-slate-200/60 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-900/30">
              <span className="text-[10px] uppercase font-mono text-slate-500 block mb-1.5">
                Suggested Questions:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {DEFAULT_SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(q)}
                    className="px-2 py-0.5 rounded-md bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-[11px] transition focus-ring"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input & Send Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="p-3 bg-white dark:bg-[#0E1320] border-t border-slate-200 dark:border-slate-800 flex items-center gap-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about tickets, priority, or SLAs..."
              disabled={loading}
              className="flex-1 px-3 py-2 text-xs rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus-ring"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition focus-ring shadow-sm"
              title="Send message"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}
    </>
  );
};
