import React, { useState, useEffect } from 'react';
import { GlassCard } from './GlassCard';
import { Send, ThumbsUp, ThumbsDown, Sparkles, Brain, Play, CheckCircle, XCircle, ChevronDown, ChevronUp, Zap, WifiOff, Settings, AlertCircle, Database, RefreshCw } from 'lucide-react';
import { health, route, plan, judgment, execute, authStatus as fetchAuthStatus, multiAgent, ask, config, fetchEvidence, createTaskIntent, RouteResponse, PlanResponse, JudgmentResponse, ExecuteResponse, MultiAgentResponse, MultiAgentMessage, AskResponse, ConfigResponse, EvidenceResponse, TaskIntentOut } from '@/lib/quilloApi';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'evidence';
  content: string;
  timestamp: Date;
  model?: string; // Model used for response (raw mode)
  judgmentResult?: JudgmentResponse;
  routeResult?: RouteResponse;
  executeResult?: ExecuteResponse;
  evidenceResult?: EvidenceResponse; // Evidence Layer v1
  showProceedButtons?: boolean;
  multiAgentMeta?: {
    provider: string;
    fallback_reason?: string | null;
    peers_unavailable?: boolean;
    userText: string;
    allMessages: MultiAgentMessage[];
  }; // For multi-agent transcript header
  agentMeta?: MultiAgentMessage; // Per-message agent metadata
}

/**
 * Map backend tool IDs to user-friendly QuillConnect Suite names
 */
function displayToolName(toolId: string): string {
  const toolMap: Record<string, string> = {
    'response_generator': 'Response',
    'tone_adjuster': 'Rewrite',
    'conflict_resolver': 'Argument',
    'clarity_summarizer': 'Clarity',
    'summarizer': 'Clarity',
  };

  if (toolMap[toolId]) {
    return toolMap[toolId];
  }

  return toolId
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Determine if a provider/model indicates offline mode
 */
function isOfflineMode(providerOrModel: string | undefined): boolean {
  if (!providerOrModel) return true;
  const lower = providerOrModel.toLowerCase();
  return lower === 'offline' || lower === 'template';
}

/**
 * Component to display execution results with step trace
 */
function ExecutionResultCard({ executeResult }: { executeResult: ExecuteResponse }) {
  const [showTrace, setShowTrace] = useState(false);
  const isOffline = isOfflineMode(executeResult.provider_used);

  return (
    <div className="bg-green-50 dark:bg-green-900/20 rounded-[16px] px-4 py-3 border border-green-200 dark:border-green-800 text-sm space-y-3">
      <div className="flex items-center gap-2">
        <Play className="w-4 h-4 text-green-600 dark:text-green-400" />
        <span className="font-semibold text-green-700 dark:text-green-300">Result</span>
      </div>

      {/* Mode Banner */}
      {isOffline ? (
        <div className="flex items-center gap-2 px-3 py-2 bg-amber-100 dark:bg-amber-900/30 rounded-[10px] border border-amber-200 dark:border-amber-800">
          <WifiOff className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
          <span className="text-xs text-amber-700 dark:text-amber-300">
            Offline output — template-based. Connect AI for stronger judgment.
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-2 px-3 py-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-[10px] border border-emerald-200 dark:border-emerald-800">
          <Zap className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span className="text-xs text-emerald-700 dark:text-emerald-300">
            AI-powered output — enhanced reasoning applied.
          </span>
        </div>
      )}

      {/* Warnings */}
      {executeResult.warnings && executeResult.warnings.length > 0 && (
        <div className="space-y-1">
          {executeResult.warnings.map((warning, idx) => (
            <p key={idx} className="text-xs text-orange-600 dark:text-orange-400 italic">
              ⚠️ {warning}
            </p>
          ))}
        </div>
      )}

      {/* Metadata */}
      <div className="text-xs text-muted-foreground space-y-1">
        <p><span className="font-medium">Mode:</span> {isOffline ? 'Offline' : executeResult.provider_used}</p>
        <p><span className="font-medium">Result ID:</span> {executeResult.trace_id}</p>
      </div>

      {/* Steps Toggle */}
      {executeResult.artifacts && executeResult.artifacts.length > 0 && (
        <div>
          <button
            onClick={() => setShowTrace(!showTrace)}
            className="flex items-center gap-2 text-xs text-green-700 dark:text-green-300 hover:text-green-800 dark:hover:text-green-200 font-medium"
          >
            {showTrace ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            Steps ({executeResult.artifacts.length})
          </button>

          {showTrace && (
            <div className="mt-3 space-y-2">
              {executeResult.artifacts.map((artifact, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-white/50 dark:bg-slate-800/50 rounded-[12px] border border-green-200/50 dark:border-green-800/50"
                >
                  <p className="font-medium text-xs text-green-700 dark:text-green-300 mb-1">
                    Step {artifact.step_index + 1}: {displayToolName(artifact.tool)}
                  </p>
                  <div className="text-xs text-muted-foreground space-y-1">
                    <p className="italic">Result: {artifact.output_excerpt}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Connect AI Provider Modal Component
 */
function ConnectAIModal() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button className="text-xs text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 font-medium underline underline-offset-2 ml-1">
          Connect
        </button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-border/50">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            Enable AI-Powered Mode
          </DialogTitle>
          <DialogDescription>
            Connect an AI provider to unlock enhanced reasoning capabilities.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-semibold flex-shrink-0">
                1
              </div>
              <div className="text-sm">
                <p className="font-medium">Open Secrets</p>
                <p className="text-muted-foreground">Go to Replit Secrets panel or your .env file</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-semibold flex-shrink-0">
                2
              </div>
              <div className="text-sm">
                <p className="font-medium">Add API Key</p>
                <p className="text-muted-foreground">Add OPENROUTER_API_KEY or ANTHROPIC_API_KEY</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-semibold flex-shrink-0">
                3
              </div>
              <div className="text-sm">
                <p className="font-medium">Restart Backend</p>
                <p className="text-muted-foreground">Restart the Uorin Agent API to apply changes</p>
              </div>
            </div>
          </div>
        </div>
        <DialogFooter>
          <DialogTrigger asChild>
            <button className="px-4 py-2 bg-primary text-primary-foreground rounded-[12px] hover:bg-primary/90 transition-all text-sm font-medium">
              Got it
            </button>
          </DialogTrigger>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Intelligence Status Badge Component
 */
function IntelligenceStatusBadge({
  status
}: {
  status: 'unknown' | 'ai-powered' | 'offline'
}) {
  if (status === 'unknown') {
    return null;
  }

  const isAIPowered = status === 'ai-powered';

  return (
    <div
      className={`group relative px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 ${
        isAIPowered
          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
          : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
      }`}
    >
      {isAIPowered ? (
        <>
          <Zap className="w-3 h-3" />
          AI-Powered
        </>
      ) : (
        <>
          <WifiOff className="w-3 h-3" />
          Offline Mode
          <ConnectAIModal />
        </>
      )}
      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs rounded-[8px] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
        {isAIPowered
          ? 'Enhanced reasoning enabled via connected model provider.'
          : 'Using offline fallbacks. Connect OpenRouter/Anthropic for best results.'
        }
        <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900 dark:border-t-slate-100" />
      </div>
    </div>
  );
}

/**
 * Agent Status Badge Component (for individual agent messages)
 */
function AgentStatusBadge({ message }: { message: MultiAgentMessage }) {
  if (message.live) {
    const modelShort = message.model_id?.split('/')[1] || message.model_id;
    return (
      <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
        <Zap className="w-2.5 h-2.5" />
        Live
        {modelShort && <span className="text-[10px] opacity-70">({modelShort})</span>}
      </div>
    );
  }

  const reasonText = message.unavailable_reason === 'rate_limited' ? 'Rate-limited' :
                     message.unavailable_reason === 'timeout' ? 'Timeout' :
                     message.unavailable_reason === 'not_found' ? 'Not found' :
                     'Unavailable';
  return (
    <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
      <WifiOff className="w-2.5 h-2.5" />
      {reasonText}
    </div>
  );
}

/**
 * Multi-Agent Provider Badge Component
 */
function MultiAgentProviderBadge({
  provider,
  fallbackReason,
  peersUnavailable,
  messages,
  onRetry
}: {
  provider: string;
  fallbackReason?: string | null;
  peersUnavailable?: boolean;
  messages: MultiAgentMessage[];
  onRetry?: () => void;
}) {
  const isLive = provider === 'openrouter';
  const failedAgents = messages.filter(m => !m.live && m.agent !== 'quillo');
  const hasSomeFailures = failedAgents.length > 0;

  return (
    <div className="mb-3 space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <div
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
            isLive
              ? hasSomeFailures
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
              : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
          }`}
        >
          {isLive ? (
            <>
              <Zap className="w-3 h-3" />
              {hasSomeFailures ? 'Partial Live' : 'Live'}
            </>
          ) : (
            <>
              <WifiOff className="w-3 h-3" />
              Fallback
            </>
          )}
        </div>

        {isLive && hasSomeFailures && onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
          >
            <Play className="w-3 h-3" />
            Retry {failedAgents.length} unavailable
          </button>
        )}

        {!isLive && onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
          >
            <Play className="w-3 h-3" />
            Retry live
          </button>
        )}
      </div>

      {!isLive && (
        <p className="text-xs text-muted-foreground">
          Live models were unavailable for this run — showing fallback output.
        </p>
      )}
      {isLive && peersUnavailable && (
        <p className="text-xs text-muted-foreground">
          Uorin responded live, but all peer agents were unavailable.
        </p>
      )}
      {isLive && hasSomeFailures && !peersUnavailable && (
        <p className="text-xs text-muted-foreground">
          Some agents were unavailable — showing partial live output.
        </p>
      )}
    </div>
  );
}

/**
 * Stakes Badge Component
 */
function StakesBadge({ stakes }: { stakes: 'low' | 'medium' | 'high' }) {
  const colors = {
    low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };

  const icons = {
    low: CheckCircle,
    medium: AlertCircle,
    high: XCircle,
  };

  const Icon = icons[stakes];

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${colors[stakes]}`}>
      <Icon className="w-3 h-3" />
      Stakes: {stakes}
    </div>
  );
}

export function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [showWorkflow, setShowWorkflow] = useState(true);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [intelligenceStatus, setIntelligenceStatus] = useState<'unknown' | 'ai-powered' | 'offline'>('offline');
  const [authStatus, setAuthStatus] = useState<{ env: string; ui_token_required: boolean; ui_token_configured: boolean; hint: string | null } | null>(null);
  const [planResult, setPlanResult] = useState<PlanResponse | null>(null);
  const [lastUserMessage, setLastUserMessage] = useState<{ text: string; routeResult?: RouteResponse; judgmentResult?: JudgmentResponse } | null>(null);
  const [loading, setLoading] = useState(false);
  const [showAdvancedTools, setShowAdvancedTools] = useState(false);
  const [rawChatMode, setRawChatMode] = useState<boolean>(true); // Default to raw mode

  // Task Intent Confirmation v1 state
  const [taskConfirmMessageId, setTaskConfirmMessageId] = useState<string | null>(null);
  const [taskCreating, setTaskCreating] = useState(false);

  // Check backend health, auth status, and config on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await health();
        setBackendStatus('online');
      } catch (error) {
        console.error('Backend health check failed:', error);
        setBackendStatus('offline');
      }
    };
    const checkAuthStatus = async () => {
      try {
        const status = await fetchAuthStatus();
        setAuthStatus(status);
      } catch (error) {
        console.error('Auth status check failed:', error);
      }
    };
    const checkConfig = async () => {
      try {
        const cfg = await config();
        setRawChatMode(cfg.raw_chat_mode);
      } catch (error) {
        console.error('Config check failed:', error);
        // Default to raw mode if check fails
        setRawChatMode(true);
      }
    };
    checkHealth();
    checkAuthStatus();
    checkConfig();
  }, []);

  // Evidence Layer v1: Handlers for manual evidence retrieval
  const handleFetchEvidence = async (query: string) => {
    setLoading(true);

    try {
      const evidenceResult = await fetchEvidence(query);

      const evidenceMessage: Message = {
        id: Date.now().toString(),
        role: 'evidence',
        content: `Evidence retrieved for: "${query}"`,
        timestamp: new Date(),
        evidenceResult,
      };

      setMessages((prev) => [...prev, evidenceMessage]);
    } catch (error) {
      console.error('Evidence retrieval failed:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Failed to retrieve evidence: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleEvidenceCommand = async (command: string) => {
    // Parse /evidence command
    const query = command.replace('/evidence', '').trim();

    if (query) {
      // User provided query: /evidence <query>
      setInput('');
      await handleFetchEvidence(query);
    } else {
      // No query provided: use last user message
      const lastUserMsg = messages.filter(m => m.role === 'user').pop();
      if (lastUserMsg) {
        setInput('');
        await handleFetchEvidence(lastUserMsg.content);
      } else {
        // No previous message found
        setInput('');
        const errorMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: 'No previous message found. Please provide a query: /evidence <your query>',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    // Check for /evidence slash command
    if (input.trim().startsWith('/evidence')) {
      await handleEvidenceCommand(input.trim());
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    const userInput = input;
    setInput('');
    setLoading(true);

    try {
      if (rawChatMode) {
        // RAW CHAT V1: Use /ask for real LLM output, no judgment/contract coupling
        const askResult = await ask(userInput, 'demo');

        // Update intelligence status based on model
        setIntelligenceStatus(isOfflineMode(askResult.model) ? 'offline' : 'ai-powered');

        // Handle offline mode with clear message
        if (isOfflineMode(askResult.model)) {
          const offlineMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: `I'm offline right now — hit Connect to enable live models.`,
            timestamp: new Date(),
            model: askResult.model,
          };
          setMessages((prev) => [...prev, offlineMessage]);
          return;
        }

        // Real LLM response
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: askResult.answer,
          timestamp: new Date(),
          model: askResult.model,
        };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        // ADVANCED MODE: Use judgment layer (existing behavior)
        const judgmentResult = await judgment(userInput, 'demo');
        setLastUserMessage({ text: userInput, judgmentResult });

        // Use contract v1 fields if available, otherwise fall back to legacy
        let messageContent = judgmentResult.assistant_message || judgmentResult.formatted_message;

        // Add questions if present (contract v1)
        if (judgmentResult.questions && judgmentResult.questions.length > 0) {
          const questionsList = judgmentResult.questions.map(q => `• ${q}`).join('\n');
          messageContent = `${messageContent}\n\n${questionsList}`;
        }

        // Add suggested next step if present (contract v1)
        if (judgmentResult.suggested_next_step) {
          messageContent = `${messageContent}\n\nNext step: ${judgmentResult.suggested_next_step}`;
        }

        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: messageContent,
          timestamp: new Date(),
          judgmentResult,
          showProceedButtons: judgmentResult.requires_confirmation,
        };
        setMessages((prev) => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Chat API failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I'm having trouble processing your request right now. ${error instanceof Error ? error.message : 'Please try again.'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleProceed = async (messageId: string) => {
    if (!lastUserMessage?.text) return;

    setLoading(true);

    try {
      // Step 1: Route the input
      const routeResult = await route(lastUserMessage.text, 'demo');

      // Step 2: Generate plan
      const planResult = await plan(
        routeResult.intent,
        lastUserMessage.text,
        routeResult.slots,
        'demo'
      );
      setPlanResult(planResult);
      setLastUserMessage(prev => prev ? { ...prev, routeResult } : null);

      // Update the message to remove proceed buttons
      setMessages(prev =>
        prev.map(msg =>
          msg.id === messageId
            ? { ...msg, showProceedButtons: false, routeResult }
            : msg
        )
      );

      // Add workflow notification
      const workflowMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I've created a workflow with ${planResult.steps.length} steps. You can review it in the Workflow panel and click "Run" when ready.`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, workflowMessage]);
    } catch (error) {
      console.error('Proceed failed:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I encountered an error creating the workflow: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleNotYet = (messageId: string) => {
    setMessages(prev =>
      prev.map(msg =>
        msg.id === messageId
          ? { ...msg, showProceedButtons: false }
          : msg
      )
    );
  };

  const handleBringInAgentsForMessage = async (userText: string) => {
    // Raw mode: Bring in other agents for a specific user message
    setLoading(true);

    try {
      // Call multi-agent chat with the user message
      const multiAgentResult = await multiAgent(userText, 'demo');

      // Add each agent message to the chat, with meta on the first one
      multiAgentResult.messages.forEach((msg, idx) => {
        // Determine if this is a synthesis message (Quillo's final message)
        const isSynthesis = msg.agent === 'quillo' && idx === multiAgentResult.messages.length - 1;

        const agentLabel = msg.agent === 'quillo' ?
          (isSynthesis ? 'Uorin — Synthesis' : 'Uorin') :
          msg.agent === 'claude' ? 'Claude' :
          msg.agent === 'deepseek' ? 'DeepSeek' :
          msg.agent === 'gemini' ? 'Gemini' :
          msg.agent;

        const agentMessage: Message = {
          id: (Date.now() + idx + 1).toString(),
          role: 'assistant',
          content: `${agentLabel}\n\n${msg.content}`,
          timestamp: new Date(),
          agentMeta: msg, // NEW: per-message agent metadata
          // Add meta to first message for the summary badge
          ...(idx === 0 && {
            multiAgentMeta: {
              provider: multiAgentResult.provider,
              fallback_reason: multiAgentResult.fallback_reason,
              peers_unavailable: multiAgentResult.peers_unavailable || false,
              userText,
              allMessages: multiAgentResult.messages
            }
          }),
        };
        setMessages(prev => [...prev, agentMessage]);
      });
    } catch (error) {
      console.error('Multi-agent chat failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I encountered an error bringing in other perspectives: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleBringInAgents = async (messageId: string) => {
    // Find the message and get the original user text
    const message = messages.find(msg => msg.id === messageId);
    if (!message) return;

    // Find the original user message (should be right before this assistant message)
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    const userMessage = messageIndex > 0 ? messages[messageIndex - 1] : null;
    if (!userMessage || userMessage.role !== 'user') return;

    // Hide the suggestion buttons
    setMessages(prev =>
      prev.map(msg =>
        msg.id === messageId
          ? { ...msg, showProceedButtons: false }
          : msg
      )
    );

    await handleBringInAgentsForMessage(userMessage.content);
  };

  const handleContinueSolo = (messageId: string) => {
    // Just hide the suggestion buttons and continue normally
    setMessages(prev =>
      prev.map(msg =>
        msg.id === messageId
          ? { ...msg, showProceedButtons: false }
          : msg
      )
    );
  };

  // Task Intent Confirmation v1 handlers
  const handleTurnIntoTask = (messageId: string) => {
    setTaskConfirmMessageId(messageId);
  };

  const handleConfirmTask = async (messageId: string) => {
    const message = messages.find(msg => msg.id === messageId);
    if (!message || message.role !== 'user') return;

    setTaskCreating(true);

    try {
      // Create task intent with minimal cleanup
      const intentText = message.content.trim();
      await createTaskIntent({
        intent_text: intentText,
        origin_chat_id: null, // v1: no chat ID tracking yet
        user_key: null, // v1: no user tracking yet
      });

      // Close confirmation card
      setTaskConfirmMessageId(null);

      // Add success note to chat
      const successNote: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Task created with scope. Default task approval: Plan then auto. You can view it in Tasks.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, successNote]);
    } catch (error) {
      console.error('Task creation failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Failed to create task: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setTaskCreating(false);
    }
  };

  const handleCancelTask = () => {
    setTaskConfirmMessageId(null);
  };

  const handleMultiAgent = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    const userInput = input;
    setInput('');
    setLoading(true);

    try {
      // Call multi-agent chat
      const multiAgentResult = await multiAgent(userInput, 'demo');

      // Add each agent message to the chat, with meta on the first one
      multiAgentResult.messages.forEach((msg, idx) => {
        // Determine if this is a synthesis message (Quillo's final message)
        const isSynthesis = msg.agent === 'quillo' && idx === multiAgentResult.messages.length - 1;

        const agentLabel = msg.agent === 'quillo' ?
          (isSynthesis ? 'Uorin — Synthesis' : 'Uorin') :
          msg.agent === 'claude' ? 'Claude' :
          msg.agent === 'deepseek' ? 'DeepSeek' :
          msg.agent === 'gemini' ? 'Gemini' :
          msg.agent;

        const agentMessage: Message = {
          id: (Date.now() + idx + 1).toString(),
          role: 'assistant',
          content: `${agentLabel}\n\n${msg.content}`,
          timestamp: new Date(),
          agentMeta: msg, // Per-message agent metadata
          // Add meta to first message for the badge
          ...(idx === 0 && {
            multiAgentMeta: {
              provider: multiAgentResult.provider,
              fallback_reason: multiAgentResult.fallback_reason,
              peers_unavailable: multiAgentResult.peers_unavailable || false,
              userText: userInput,
              allMessages: multiAgentResult.messages
            }
          }),
        };
        setMessages(prev => [...prev, agentMessage]);
      });
    } catch (error) {
      console.error('Multi-agent chat failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I encountered an error with the group chat: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!planResult || !lastUserMessage?.routeResult) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Please generate a workflow plan first by clicking "Proceed" on a previous message.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }

    setLoading(true);

    // Track whether reassurance message was already sent
    let reassuranceSent = false;

    // Start a timer for reassurance message (12 seconds)
    const reassuranceTimer = setTimeout(() => {
      if (!reassuranceSent) {
        reassuranceSent = true;
        const reassuranceMessage: Message = {
          id: Date.now().toString() + '-reassurance',
          role: 'assistant',
          content: 'Got it — I\'m working through this now. This one needs a careful pass.',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, reassuranceMessage]);
      }
    }, 12000); // 12 seconds

    try {
      const executeResult = await execute(
        lastUserMessage.text,
        lastUserMessage.routeResult.intent,
        planResult.steps,
        lastUserMessage.routeResult.slots,
        'demo',
        true
      );

      // Clear the reassurance timer if execution completes before 12s
      clearTimeout(reassuranceTimer);

      // Update intelligence status
      setIntelligenceStatus(isOfflineMode(executeResult.provider_used) ? 'offline' : 'ai-powered');

      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: executeResult.output_text,
        timestamp: new Date(),
        executeResult,
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      // Clear the reassurance timer on error
      clearTimeout(reassuranceTimer);

      console.error('Execute failed:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex gap-6 h-full overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Status Badges */}
        <div className="p-4 flex justify-end gap-2 flex-wrap">
          {/* Intelligence Status Badge */}
          <IntelligenceStatusBadge status={intelligenceStatus} />

          {/* Backend Status Badge */}
          <div className={`px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 ${
            backendStatus === 'online'
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              : backendStatus === 'offline'
              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              : 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
          }`}>
            {backendStatus === 'online' ? (
              <>
                <CheckCircle className="w-3 h-3" />
                Backend: OK
              </>
            ) : backendStatus === 'offline' ? (
              <>
                <XCircle className="w-3 h-3" />
                Backend: Offline
              </>
            ) : (
              <>Checking...</>
            )}
          </div>

          {/* Auth Status Badge */}
          {authStatus && (
            <div className={`group relative px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 cursor-default ${
              !authStatus.ui_token_required
                ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                : authStatus.ui_token_configured
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
            }`}>
              {!authStatus.ui_token_required ? (
                <>
                  <Settings className="w-3 h-3" />
                  Dev Bypass
                </>
              ) : authStatus.ui_token_configured ? (
                <>
                  <CheckCircle className="w-3 h-3" />
                  Auth: OK
                </>
              ) : (
                <>
                  <XCircle className="w-3 h-3" />
                  Auth: Missing
                </>
              )}
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs rounded-[8px] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg max-w-xs">
                {authStatus.hint || (
                  authStatus.ui_token_configured
                    ? 'UI token authentication is configured and active.'
                    : 'Set QUILLO_UI_TOKEN and VITE_UI_TOKEN to enable auth.'
                )}
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900 dark:border-t-slate-100" />
              </div>
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-20">
              <p className="text-lg font-medium mb-2">Welcome to Uorin</p>
              <p className="text-sm">Start chatting to get conversational assistance</p>
            </div>
          )}
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] space-y-2`}>
                {/* Multi-Agent Provider Badge (shown above first agent message) */}
                {message.multiAgentMeta && (
                  <MultiAgentProviderBadge
                    provider={message.multiAgentMeta.provider}
                    fallbackReason={message.multiAgentMeta.fallback_reason}
                    peersUnavailable={message.multiAgentMeta.peers_unavailable}
                    messages={message.multiAgentMeta.allMessages}
                    onRetry={message.multiAgentMeta.provider !== 'openrouter' ? () => handleBringInAgentsForMessage(message.multiAgentMeta!.userText) : undefined}
                  />
                )}

                <div
                  className={`${
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-primary to-secondary text-white'
                      : message.role === 'evidence'
                      ? 'bg-blue-50 dark:bg-blue-950/30 border-2 border-blue-200 dark:border-blue-800'
                      : 'bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl border border-border'
                  } rounded-[20px] px-5 py-3 shadow-lg`}
                >
                  {/* Evidence Layer v1: Render evidence block */}
                  {message.role === 'evidence' && message.evidenceResult ? (
                    <div className="space-y-3">
                      {/* Header */}
                      <div className="border-b border-blue-200 dark:border-blue-800 pb-2">
                        <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">Evidence (Live Data)</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Retrieved: {new Date(message.evidenceResult.retrieved_at).toLocaleString()}
                          {message.evidenceResult.duration_ms && ` • ${message.evidenceResult.duration_ms}ms`}
                        </p>
                      </div>

                      {/* Error state */}
                      {!message.evidenceResult.ok && message.evidenceResult.error && (
                        <div className="text-sm text-red-600 dark:text-red-400">
                          Error: {message.evidenceResult.error}
                        </div>
                      )}

                      {/* Evidence Guards v1.1: Empty evidence notice */}
                      {(message.evidenceResult.ok && message.evidenceResult.facts.length === 0) && (
                        <div className="space-y-3">
                          {/* Main notice */}
                          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                            <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                              No verifiable evidence was found for this query.
                            </p>
                            <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                              Interpretation is disabled to avoid speculation. Try refining the query.
                            </p>
                          </div>

                          {/* Why this can happen hint */}
                          <div className="bg-slate-50 dark:bg-slate-900/30 border border-slate-200 dark:border-slate-800 rounded-lg p-3">
                            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                              Why this can happen:
                            </p>
                            <p className="text-xs text-slate-600 dark:text-slate-400">
                              This question may be ambiguous (e.g., season vs calendar year), require calculation (e.g., win percentage), or rely on sources that can't be fetched.
                            </p>
                          </div>

                          {/* Query refinement suggestions */}
                          <div className="space-y-2">
                            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                              Try refining your query:
                            </p>
                            <div className="flex flex-wrap gap-2">
                              <button
                                onClick={() => {
                                  const originalQuery = message.content.replace('Evidence retrieved for: "', '').replace('"', '');
                                  setInput(`/evidence ${originalQuery} 2024 calendar year`);
                                }}
                                disabled={loading}
                                className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-all text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                + Add timeframe (e.g., "2024 calendar year")
                              </button>
                              <button
                                onClick={() => {
                                  const originalQuery = message.content.replace('Evidence retrieved for: "', '').replace('"', '');
                                  setInput(`/evidence ${originalQuery} raw stats wins losses`);
                                }}
                                disabled={loading}
                                className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-all text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                + Try raw stats instead of percentages
                              </button>
                              <button
                                onClick={() => {
                                  const originalQuery = message.content.replace('Evidence retrieved for: "', '').replace('"', '');
                                  setInput(`/evidence ${originalQuery} official report`);
                                }}
                                disabled={loading}
                                className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-all text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                + Add "official report"
                              </button>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Facts */}
                      {message.evidenceResult.ok && message.evidenceResult.facts.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Key Facts</p>
                          <ul className="space-y-2 list-none">
                            {message.evidenceResult.facts.map((fact, idx) => {
                              const source = message.evidenceResult!.sources.find(s => s.id === fact.source_id);
                              return (
                                <li key={idx} className="text-sm flex gap-2">
                                  <span className="text-blue-600 dark:text-blue-400">•</span>
                                  <div className="flex-1">
                                    <span className="text-foreground">{fact.text}</span>
                                    {source && (
                                      <a
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="ml-1 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                      >
                                        [{source.domain}]
                                      </a>
                                    )}
                                    {fact.published_at && (
                                      <span className="ml-1 text-xs text-muted-foreground">
                                        ({new Date(fact.published_at).toLocaleDateString()})
                                      </span>
                                    )}
                                  </div>
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                      )}

                      {/* Sources */}
                      {message.evidenceResult.ok && message.evidenceResult.sources.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Sources</p>
                          <ul className="space-y-1 list-none text-xs">
                            {message.evidenceResult.sources.map((source, idx) => (
                              <li key={idx}>
                                <a
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 dark:text-blue-400 hover:underline"
                                >
                                  {source.title}
                                </a>
                                <span className="text-muted-foreground ml-1">({source.domain})</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Limits note */}
                      {message.evidenceResult.limits && (
                        <p className="text-xs text-muted-foreground italic">
                          Note: {message.evidenceResult.limits}
                        </p>
                      )}
                    </div>
                  ) : message.agentMeta ? (
                    // Multi-agent message: parse and style the agent header
                    (() => {
                      const lines = message.content.split('\n');
                      const agentName = lines[0];
                      const content = lines.slice(2).join('\n'); // Skip agent name and blank line

                      return (
                        <>
                          <p className="text-sm font-semibold text-primary mb-2 pb-2 border-b border-border/30">{agentName}</p>
                          <p className="text-sm whitespace-pre-wrap">{content}</p>
                        </>
                      );
                    })()
                  ) : message.agentMeta ? (
                    // Per-agent status badge for multi-agent messages
                    <div className="mb-2">
                      <AgentStatusBadge message={message.agentMeta} />
                    </div>
                  ) : (
                    // Regular message
                    <>
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'}`}>
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </>
                  )}
                </div>

                {/* Evidence Layer v1.1: Post-evidence action buttons with Authority Guard */}
                {message.role === 'evidence' && message.evidenceResult && (
                  <div className="space-y-1.5">
                    {(() => {
                      // Authority Guard: Disable interpretation when no facts found
                      const hasEvidence = message.evidenceResult.ok && message.evidenceResult.facts.length > 0;

                      return (
                        <>
                          <div className="flex gap-2 flex-wrap">
                            <button
                              onClick={() => {
                                if (!hasEvidence) return; // Authority Guard: prevent action
                                setInput(`Based on the evidence above, `);
                              }}
                              disabled={loading || !hasEvidence}
                              className={`px-3 py-1.5 rounded-[12px] transition-all text-xs font-medium flex items-center gap-1.5 ${
                                hasEvidence
                                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50'
                                  : 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed'
                              } disabled:opacity-50 disabled:cursor-not-allowed`}
                            >
                              <Brain className="w-3 h-3" />
                              Ask Uorin to interpret this evidence
                            </button>
                            <button
                              onClick={() => {
                                if (!hasEvidence) return; // Authority Guard: prevent action
                                handleBringInAgentsForMessage(`Analyze this evidence: ${message.content}`);
                              }}
                              disabled={loading || !hasEvidence}
                              className={`px-3 py-1.5 rounded-[12px] transition-all text-xs font-medium flex items-center gap-1.5 ${
                                hasEvidence
                                  ? 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                  : 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed'
                              } disabled:opacity-50 disabled:cursor-not-allowed`}
                            >
                              <Brain className="w-3 h-3" />
                              Get second opinions on this evidence
                            </button>
                            <button
                              onClick={() => {
                                const query = message.content.replace('Evidence retrieved for: "', '').replace('"', '');
                                setInput(`/evidence ${query}`);
                              }}
                              disabled={loading}
                              className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-[12px] hover:bg-slate-200 dark:hover:bg-slate-700 transition-all text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                            >
                              <RefreshCw className="w-3 h-3" />
                              Refine evidence query
                            </button>
                          </div>
                          <p className="text-[10px] text-muted-foreground pl-1">
                            {hasEvidence
                              ? "Optional — interpret evidence, get other perspectives, or refine your search"
                              : "Interpretation disabled (no evidence found) — refine your query to try again"
                            }
                          </p>
                        </>
                      );
                    })()}
                  </div>
                )}

                {/* RAW MODE: Bring in other models button for user messages */}
                {rawChatMode && message.role === 'user' && (
                  <div className="space-y-1.5">
                    <div className="flex gap-2 flex-wrap">
                      <button
                        onClick={() => handleBringInAgentsForMessage(message.content)}
                        disabled={loading}
                        className="group relative px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-[12px] hover:bg-slate-200 dark:hover:bg-slate-700 transition-all text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                      >
                        <Brain className="w-3 h-3" />
                        Get second opinions
                        {/* Tooltip */}
                        <div className="absolute bottom-full left-0 mb-2 px-3 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs rounded-[8px] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
                          Claude, Gemini, and DeepSeek will each reply once. Uorin will summarize.
                          <div className="absolute top-full left-6 -mt-1 border-4 border-transparent border-t-slate-900 dark:border-t-slate-100" />
                        </div>
                      </button>
                      <button
                        onClick={() => handleFetchEvidence(message.content)}
                        disabled={loading}
                        className="group relative px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-[12px] hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-all text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                      >
                        <Database className="w-3 h-3" />
                        Fetch current facts
                        {/* Tooltip */}
                        <div className="absolute bottom-full left-0 mb-2 px-3 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs rounded-[8px] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
                          Adds an Evidence block with sources + timestamps
                          <div className="absolute top-full left-6 -mt-1 border-4 border-transparent border-t-slate-900 dark:border-t-slate-100" />
                        </div>
                      </button>
                      <button
                        onClick={() => handleTurnIntoTask(message.id)}
                        disabled={loading}
                        className="group relative px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-[12px] hover:bg-green-200 dark:hover:bg-green-900/50 transition-all text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                      >
                        <CheckCircle className="w-3 h-3" />
                        Turn into task
                        {/* Tooltip */}
                        <div className="absolute bottom-full left-0 mb-2 px-3 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs rounded-[8px] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
                          Uorin will paraphrase the intent and ask you to confirm.
                          <div className="absolute top-full left-6 -mt-1 border-4 border-transparent border-t-slate-900 dark:border-t-slate-100" />
                        </div>
                      </button>
                    </div>
                    <p className="text-[10px] text-muted-foreground pl-1">
                      Optional — manually bring in other models, fetch live evidence, or create a task for this message
                    </p>
                  </div>
                )}

                {/* Task Intent Confirmation Card (v1) */}
                {taskConfirmMessageId === message.id && (
                  <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl border-2 border-green-200 dark:border-green-800 rounded-[16px] px-4 py-3 space-y-3 shadow-lg">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-foreground mb-1">Create task?</h4>
                        <p className="text-sm text-muted-foreground">
                          Just to confirm: you want me to{' '}
                          <span className="font-medium text-foreground">
                            {message.content.length > 140
                              ? message.content.substring(0, 140) + '…'
                              : message.content}
                          </span>
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleConfirmTask(message.id)}
                        disabled={taskCreating}
                        className="px-4 py-2 bg-green-600 text-white rounded-[12px] hover:bg-green-700 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                      >
                        {taskCreating ? (
                          <>
                            <RefreshCw className="w-3 h-3 animate-spin" />
                            Creating...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-3 h-3" />
                            Confirm
                          </>
                        )}
                      </button>
                      <button
                        onClick={handleCancelTask}
                        disabled={taskCreating}
                        className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-[12px] hover:bg-slate-300 dark:hover:bg-slate-600 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                      >
                        <XCircle className="w-3 h-3" />
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* ADVANCED MODE ONLY: Stakes, Proceed, Agent Suggestion Buttons */}
                {!rawChatMode && (
                  <>
                    {/* Stakes Badge */}
                    {message.judgmentResult && (
                      <div className="flex items-center gap-2">
                        <StakesBadge stakes={message.judgmentResult.stakes} />
                      </div>
                    )}

                    {/* Proceed/Not Yet Buttons */}
                    {message.showProceedButtons && message.judgmentResult?.suggested_next_step !== 'add_agents' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleProceed(message.id)}
                          disabled={loading}
                          className="px-4 py-2 bg-primary text-white rounded-[12px] hover:bg-primary/90 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Proceed
                        </button>
                        <button
                          onClick={() => handleNotYet(message.id)}
                          disabled={loading}
                          className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Not yet
                        </button>
                      </div>
                    )}

                    {/* Agent Suggestion Buttons (v1) */}
                    {message.judgmentResult?.suggested_next_step === 'add_agents' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleBringInAgents(message.id)}
                          disabled={loading}
                          className="px-4 py-2 bg-primary text-white rounded-[12px] hover:bg-primary/90 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Bring in a second opinion
                        </button>
                        <button
                          onClick={() => handleContinueSolo(message.id)}
                          disabled={loading}
                          className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Continue with you
                        </button>
                      </div>
                    )}
                  </>
                )}

                {/* Route Result Card */}
                {message.routeResult && (
                  <div className="bg-accent/50 dark:bg-slate-700/50 rounded-[16px] px-4 py-3 border border-border/50 text-xs space-y-2">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary" />
                      <span className="font-semibold">Classification</span>
                    </div>
                    <div className="space-y-1">
                      <p><span className="font-medium">Intent:</span> {message.routeResult.intent}</p>
                      {message.routeResult.slots && Object.keys(message.routeResult.slots).length > 0 && (
                        <p><span className="font-medium">Details:</span> {JSON.stringify(message.routeResult.slots)}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Execute Result Card */}
                {message.executeResult && (
                  <ExecutionResultCard executeResult={message.executeResult} />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Action Bar */}
        <div className="p-6 border-t border-border bg-white/50 dark:bg-slate-900/50 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto space-y-3">
            {/* Input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
                placeholder="Message Uorin..."
                disabled={loading}
                className="flex-1 px-4 py-3 bg-input-background border border-border rounded-[16px] focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="px-6 py-3 bg-gradient-to-r from-primary to-secondary text-white rounded-[16px] hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
              <button
                onClick={handleMultiAgent}
                disabled={loading || !input.trim()}
                className="group relative px-4 py-3 bg-slate-600 text-white rounded-[16px] hover:bg-slate-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-1.5"
              >
                <Brain className="w-4 h-4" />
                Get second opinions
                {/* Tooltip */}
                <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs rounded-[8px] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
                  Claude, Gemini, and DeepSeek will each reply once. Uorin will summarize.
                  <div className="absolute top-full right-6 -mt-1 border-4 border-transparent border-t-slate-900 dark:border-t-slate-100" />
                </div>
              </button>
            </div>

            {/* Advanced Tools Toggle */}
            <div className="flex justify-between items-center">
              <button
                onClick={() => setShowAdvancedTools(!showAdvancedTools)}
                className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
              >
                {showAdvancedTools ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                Advanced Tools
              </button>
              <div className="flex gap-2">
                <button className="px-3 py-2 bg-green-100 text-green-700 rounded-[12px] hover:bg-green-200 transition-all">
                  <ThumbsUp className="w-4 h-4" />
                </button>
                <button className="px-3 py-2 bg-red-100 text-red-700 rounded-[12px] hover:bg-red-200 transition-all">
                  <ThumbsDown className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Advanced Tools */}
            {showAdvancedTools && (
              <div className="p-3 bg-accent/20 rounded-[12px] space-y-2">
                <p className="text-xs text-muted-foreground font-medium">Quick Actions:</p>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={handleExecute}
                    disabled={!planResult || loading}
                    className="px-3 py-1.5 bg-secondary/20 text-secondary rounded-[8px] hover:bg-secondary/30 transition-all text-xs flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="w-3 h-3" />
                    Run Workflow
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Workflow Panel (renamed from Plan) */}
      {showWorkflow && (
        <GlassCard className="w-80 hidden xl:block p-6 overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Workflow
          </h3>

          {planResult ? (
            <>
              <div className="space-y-3">
                {planResult.steps.map((step, index) => (
                  <div
                    key={index}
                    className="p-4 bg-accent/50 rounded-[16px] border border-border/50"
                  >
                    <p className="font-medium text-sm mb-2">
                      {index + 1}. {displayToolName(step.tool)}
                      {step.premium && (
                        <span className="ml-2 px-2 py-0.5 bg-secondary/20 text-secondary rounded text-xs">
                          Premium
                        </span>
                      )}
                    </p>
                    <div className="space-y-1 text-xs text-muted-foreground">
                      <p className="italic">{step.rationale}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 p-3 bg-secondary/10 rounded-[12px] text-xs">
                <p className="font-medium text-secondary mb-1">Workflow ID</p>
                <p className="text-muted-foreground font-mono break-all">{planResult.trace_id}</p>
              </div>

              <button
                onClick={handleExecute}
                disabled={loading}
                className="w-full mt-4 px-4 py-2 bg-primary text-white rounded-[12px] hover:bg-primary/90 transition-all text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" />
                {loading ? 'Running...' : 'Run Workflow'}
              </button>
            </>
          ) : (
            <div className="text-center text-muted-foreground text-sm py-8">
              Workflow will appear here when you click "Proceed" on a message
            </div>
          )}
        </GlassCard>
      )}

    </div>
  );
}
