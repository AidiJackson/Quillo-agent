import React, { useState, useEffect } from 'react';
import { GlassCard } from './GlassCard';
import { Send, ThumbsUp, ThumbsDown, Sparkles, Brain, Play, CheckCircle, XCircle } from 'lucide-react';
import { health, route, plan, ask, RouteResponse, PlanResponse, AskResponse } from '@/lib/quilloApi';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  routeResult?: RouteResponse;
  askResult?: AskResponse;
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

  // Return mapped name if exists
  if (toolMap[toolId]) {
    return toolMap[toolId];
  }

  // Fallback: convert snake_case to Title Case
  return toolId
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
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
  const [planResult, setPlanResult] = useState<PlanResponse | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);
  const [lastUserMessage, setLastUserMessage] = useState<{ text: string; routeResult?: RouteResponse } | null>(null);
  const [askLoading, setAskLoading] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const [mode, setMode] = useState<'ask' | 'orchestrate'>('ask');
  const [showComingSoonModal, setShowComingSoonModal] = useState(false);

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

    // Call route API
    try {
      const routeResult = await route(userInput, 'demo');

      // Store last user message for plan button
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

  return (
    <div className="flex-1 flex gap-6 h-full overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Backend Status Badge */}
        <div className="p-4 flex justify-end">
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
                      <span className="font-semibold">Route Result</span>
                    </div>
                    <div className="space-y-1">
                      <p><span className="font-medium">Intent:</span> {message.routeResult.intent}</p>
                      {message.routeResult.slots && Object.keys(message.routeResult.slots).length > 0 && (
                        <p><span className="font-medium">Slots:</span> {JSON.stringify(message.routeResult.slots)}</p>
                      )}
                      {message.routeResult.reasons && message.routeResult.reasons.length > 0 && (
                        <div>
                          <p className="font-medium">Reasons:</p>
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

                {/* Ask Result Metadata */}
                {message.askResult && (
                  <div className="text-xs text-muted-foreground space-y-0.5">
                    <p>Model: {message.askResult.model}</p>
                    <p>Trace: {message.askResult.trace_id}</p>
                  </div>
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
              <div className="flex items-center gap-3">
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
                    onClick={() => setShowComingSoonModal(true)}
                    className="px-4 py-2 bg-secondary/20 text-secondary rounded-[12px] hover:bg-secondary/30 transition-all text-sm flex items-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Run Plan
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
          </div>
        </div>
      </div>

      {/* Plan Trace Panel */}
      {showPlanTrace && (
        <GlassCard className="w-80 hidden xl:block p-6 overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Plan Trace
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
                <p className="font-medium text-secondary mb-1">Trace ID</p>
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

      {/* Coming Soon Modal */}
      {showComingSoonModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 rounded-[20px] p-6 max-w-md w-full shadow-2xl border border-border">
            <h3 className="text-xl font-semibold mb-3 text-foreground">
              Execution Coming Soon
            </h3>
            <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
              Quillo will soon be able to automatically run multi-step plans using your QuillConnect tools.
              For now, review the plan and run each step manually.
            </p>
            <button
              onClick={() => setShowComingSoonModal(false)}
              className="w-full px-4 py-3 bg-gradient-to-r from-primary to-secondary text-white rounded-[16px] hover:shadow-lg transition-all font-medium"
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
