import React, { useState, useEffect } from 'react';
import { GlassCard } from './GlassCard';
import { Send, ThumbsUp, ThumbsDown, Sparkles, Brain, Play, CheckCircle, XCircle, ChevronDown, ChevronUp, Zap, WifiOff, Settings } from 'lucide-react';
import { health, route, plan, ask, execute, RouteResponse, PlanResponse, AskResponse, ExecuteResponse } from '@/lib/quilloApi';
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
  routeResult?: RouteResponse;
  askResult?: AskResponse;
  executeResult?: ExecuteResponse;
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
  return providerOrModel.toLowerCase() === 'offline';
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

      {/* Metadata - User-friendly labels */}
      <div className="text-xs text-muted-foreground space-y-1">
        <p><span className="font-medium">Mode:</span> {isOffline ? 'Offline' : executeResult.provider_used}</p>
        <p><span className="font-medium">Result ID:</span> {executeResult.trace_id}</p>
      </div>

      {/* Steps Toggle (renamed from Step Trace) */}
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

export function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m Quillo, your AI Chief of Staff. How can I help you today?',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [showPlanTrace, setShowPlanTrace] = useState(true);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [intelligenceStatus, setIntelligenceStatus] = useState<'unknown' | 'ai-powered' | 'offline'>('offline');
  const [planResult, setPlanResult] = useState<PlanResponse | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);
  const [lastUserMessage, setLastUserMessage] = useState<{ text: string; routeResult?: RouteResponse } | null>(null);
  const [askLoading, setAskLoading] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const [executeLoading, setExecuteLoading] = useState(false);
  const [executeError, setExecuteError] = useState<string | null>(null);
  const [mode, setMode] = useState<'ask' | 'orchestrate'>('ask');

  // Check backend health on mount
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
    checkHealth();
  }, []);

  /**
   * Update intelligence status based on API response
   */
  const updateIntelligenceStatus = (providerOrModel: string | undefined) => {
    if (!providerOrModel) return;
    setIntelligenceStatus(isOfflineMode(providerOrModel) ? 'offline' : 'ai-powered');
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    const userInput = input;
    setInput('');

    try {
      const routeResult = await route(userInput, 'demo');

      setLastUserMessage({ text: userInput, routeResult });

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Routed to: **${routeResult.intent}**\n\nThis request has been classified and is ready for processing.`,
        timestamp: new Date(),
        routeResult,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Route API failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: Failed to route request. ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handlePlan = async () => {
    if (!lastUserMessage?.routeResult) {
      setPlanError('Please send a message first to get a route result');
      return;
    }

    setPlanLoading(true);
    setPlanError(null);

    try {
      const result = await plan(
        lastUserMessage.routeResult.intent,
        lastUserMessage.text,
        lastUserMessage.routeResult.slots,
        'demo'
      );
      setPlanResult(result);
    } catch (error) {
      console.error('Plan API failed:', error);
      setPlanError(error instanceof Error ? error.message : 'Failed to generate plan');
    } finally {
      setPlanLoading(false);
    }
  };

  const handleAsk = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    const userInput = input;
    setInput('');
    setAskLoading(true);
    setAskError(null);

    try {
      const askResult = await ask(userInput, 'demo');

      // Update intelligence status based on model used
      updateIntelligenceStatus(askResult.model);

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: askResult.answer,
        timestamp: new Date(),
        askResult,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Ask API failed:', error);
      setAskError(error instanceof Error ? error.message : 'Failed to get answer');
    } finally {
      setAskLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!planResult || !lastUserMessage?.routeResult) {
      setExecuteError('Please generate a plan first');
      return;
    }

    setExecuteLoading(true);
    setExecuteError(null);

    try {
      const executeResult = await execute(
        lastUserMessage.text,
        lastUserMessage.routeResult.intent,
        planResult.steps,
        lastUserMessage.routeResult.slots,
        'demo',
        true  // dry_run mode
      );

      // Update intelligence status based on provider used
      updateIntelligenceStatus(executeResult.provider_used);

      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: executeResult.output_text,
        timestamp: new Date(),
        executeResult,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Execute API failed:', error);
      setExecuteError(error instanceof Error ? error.message : 'Failed to execute plan');
    } finally {
      setExecuteLoading(false);
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
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
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
                      {message.routeResult.reasons && message.routeResult.reasons.length > 0 && (
                        <div>
                          <p className="font-medium">Why this classification:</p>
                          <ul className="list-disc list-inside pl-2 text-muted-foreground">
                            {message.routeResult.reasons.map((reason, idx) => (
                              <li key={idx}>{reason}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Ask Result Metadata - User-friendly labels */}
                {message.askResult && (
                  <div className="text-xs text-muted-foreground space-y-0.5">
                    <p>Mode: {isOfflineMode(message.askResult.model) ? 'Offline' : message.askResult.model}</p>
                    <p>Result ID: {message.askResult.trace_id}</p>
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
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask Quillo anything..."
                className="flex-1 px-4 py-3 bg-input-background border border-border rounded-[16px] focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <button
                onClick={handleSend}
                className="px-6 py-3 bg-gradient-to-r from-primary to-secondary text-white rounded-[16px] hover:shadow-lg transition-all"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>

            {/* Mode Switch */}
            <div className="space-y-2">
              <div className="flex items-center gap-3 flex-wrap">
                <div className="inline-flex bg-accent/30 rounded-[12px] p-1">
                  <button
                    onClick={() => setMode('ask')}
                    className={`px-4 py-2 rounded-[8px] text-sm font-medium transition-all ${
                      mode === 'ask'
                        ? 'bg-white dark:bg-slate-800 text-primary shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Ask
                  </button>
                  <button
                    onClick={() => setMode('orchestrate')}
                    className={`px-4 py-2 rounded-[8px] text-sm font-medium transition-all ${
                      mode === 'orchestrate'
                        ? 'bg-white dark:bg-slate-800 text-primary shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Orchestrate
                  </button>
                </div>
                <span className="text-xs text-muted-foreground">
                  {mode === 'ask' ? 'Get direct entrepreneur advice.' : 'Route and plan tool steps.'}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 flex-wrap">
              {mode === 'orchestrate' && (
                <>
                  <button className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all text-sm flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    Route
                  </button>
                  <button
                    onClick={handlePlan}
                    disabled={!lastUserMessage?.routeResult || planLoading}
                    className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Brain className="w-4 h-4" />
                    {planLoading ? 'Planning...' : 'Plan'}
                  </button>
                  <button
                    onClick={handleExecute}
                    disabled={!planResult || executeLoading}
                    className="px-4 py-2 bg-secondary/20 text-secondary rounded-[12px] hover:bg-secondary/30 transition-all text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="w-4 h-4" />
                    {executeLoading ? 'Running...' : 'Run Plan'}
                  </button>
                </>
              )}
              {mode === 'ask' && (
                <button
                  onClick={handleAsk}
                  disabled={!input.trim() || askLoading}
                  className="px-4 py-2 bg-primary/20 text-primary rounded-[12px] hover:bg-primary/30 transition-all text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Sparkles className="w-4 h-4" />
                  {askLoading ? 'Asking...' : 'Ask Quillopreneur'}
                </button>
              )}
              <div className="ml-auto flex gap-2">
                <button className="px-3 py-2 bg-green-100 text-green-700 rounded-[12px] hover:bg-green-200 transition-all">
                  <ThumbsUp className="w-4 h-4" />
                </button>
                <button className="px-3 py-2 bg-red-100 text-red-700 rounded-[12px] hover:bg-red-200 transition-all">
                  <ThumbsDown className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Ask Error Display */}
            {askError && (
              <div className="p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-[12px] text-xs">
                {askError}
              </div>
            )}

            {/* Execute Error Display */}
            {executeError && (
              <div className="p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-[12px] text-xs">
                {executeError}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Plan Panel (renamed from Plan Trace) */}
      {showPlanTrace && (
        <GlassCard className="w-80 hidden xl:block p-6 overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Plan
          </h3>

          {planError && (
            <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-[12px] text-xs">
              {planError}
            </div>
          )}

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
                <p className="font-medium text-secondary mb-1">Result ID</p>
                <p className="text-muted-foreground font-mono break-all">{planResult.trace_id}</p>
              </div>
            </>
          ) : (
            <div className="text-center text-muted-foreground text-sm py-8">
              Click "Plan" to generate an execution plan
            </div>
          )}
        </GlassCard>
      )}

    </div>
  );
}
