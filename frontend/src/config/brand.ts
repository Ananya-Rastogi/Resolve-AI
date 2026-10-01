/**
 * Centralized Brand Configuration for Resolve AI.
 * Keeps product name, taglines, category, and asset paths centralized
 * for effortless updating and white-labeling.
 */

export const BRAND_CONFIG = {
  name: 'Resolve AI',
  shortName: 'Resolve',
  category: 'Enterprise Multi-Agent AI Ticket Resolution Platform',
  primaryTagline: 'Every ticket. One intelligent resolution.',
  supportingMessage:
    'Multiple specialized agents. One coordinated system. Human-approved outcomes.',
  metaDescription:
    'Resolve AI is an enterprise multi-agent ticket resolution platform coordinating ML classification, specialized agent routing, ChromaDB RAG grounding, and human-in-the-loop oversight.',
  company: 'Resolve AI Systems',
  version: '1.0.0',
  workflowStages: [
    { id: 'ingest', label: 'Ticket Ingest' },
    { id: 'classify', label: 'AI Classification' },
    { id: 'priority', label: 'Priority Assessment' },
    { id: 'route', label: 'Agent Routing' },
    { id: 'rag', label: 'Knowledge Retrieval' },
    { id: 'response', label: 'Grounded Response' },
    { id: 'review', label: 'Human Review / Escalation' },
  ],
} as const;

export type BrandConfig = typeof BRAND_CONFIG;
