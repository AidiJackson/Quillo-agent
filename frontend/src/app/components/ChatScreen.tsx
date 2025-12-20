import React, { useState, useEffect } from 'react';
import { GlassCard } from './GlassCard';
import { Send, ThumbsUp, ThumbsDown, Sparkles, Brain, Play, CheckCircle, XCircle, ChevronDown, ChevronUp, Zap, WifiOff, Settings, AlertCircle } from 'lucide-react';
import { health, route, plan, judgment, execute, authStatus as fetchAuthStatus, multiAgent, RouteResponse, PlanResponse, JudgmentResponse, ExecuteResponse, MultiAgentResponse } from '@/lib/quilloApi';
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
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  judgmentResult?: JudgmentResponse;
  routeResult?: RouteResponse;
  executeResult?: ExecuteResponse;
  showProceedButtons?: boolean;
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
                <p className="text-muted-foreground">Restart the Quillo Agent API to apply changes</p>
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

  // Check backend health and auth status on mount
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
    checkHealth();
    checkAuthStatus();
  }, []);

  const handleSend = async () => {
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
      // Call judgment layer for conversational response
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
    } catch (error) {
      console.error('Judgment API failed:', error);
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

      // Add each agent message to the chat
      multiAgentResult.messages.forEach((msg, idx) => {
        const agentLabel = msg.agent === 'quillo' ? 'Quillo' : msg.agent === 'claude' ? 'Claude' : 'Grok';
        const agentMessage: Message = {
          id: (Date.now() + idx + 1).toString(),
          role: 'assistant',
          content: `**${agentLabel}:** ${msg.content}`,
          timestamp: new Date(),
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
              <p className="text-lg font-medium mb-2">Welcome to Quillo</p>
              <p className="text-sm">Start chatting to get conversational assistance</p>
            </div>
          )}
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] space-y-2`}>
                <div
                  className={`${
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-primary to-secondary text-white'
                      : 'bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl border border-border'
                  } rounded-[20px] px-5 py-3 shadow-lg`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'}`}>
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>

                {/* Stakes Badge */}
                {message.judgmentResult && (
                  <div className="flex items-center gap-2">
                    <StakesBadge stakes={message.judgmentResult.stakes} />
                  </div>
                )}

                {/* Proceed/Not Yet Buttons */}
                {message.showProceedButtons && (
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
                placeholder="Message Quillo..."
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
                className="px-4 py-3 bg-slate-600 text-white rounded-[16px] hover:bg-slate-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                title="Get perspectives from multiple agents"
              >
                Group chat (v0)
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
