import React, { useState, useEffect } from 'react';
import { GlassCard } from './GlassCard';
import { Send, ThumbsUp, ThumbsDown, Sparkles, Brain, Play, CheckCircle, XCircle } from 'lucide-react';
import { health, route, RouteResponse } from '@/lib/quilloApi';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  routeResult?: RouteResponse;
}

interface PlanStep {
  step: string;
  tool: string;
  model: string;
  rationale: string;
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

  const planSteps: PlanStep[] = [
    {
      step: '1. Analyze Request',
      tool: 'Intent Classifier',
      model: 'Fast (GPT-4o-mini)',
      rationale: 'Quick intent detection for routing',
    },
    {
      step: '2. Research Context',
      tool: 'Web Search',
      model: 'Balanced (GPT-4o)',
      rationale: 'Gather comprehensive information',
    },
    {
      step: '3. Draft Response',
      tool: 'Text Generator',
      model: 'Premium (o3-mini)',
      rationale: 'High-quality output required',
    },
  ];

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

            {/* Action Buttons */}
            <div className="flex gap-2 flex-wrap">
              <button className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all text-sm flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Route
              </button>
              <button className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all text-sm flex items-center gap-2">
                <Brain className="w-4 h-4" />
                Plan
              </button>
              <button className="px-4 py-2 bg-secondary/20 text-secondary rounded-[12px] hover:bg-secondary/30 transition-all text-sm flex items-center gap-2">
                <Play className="w-4 h-4" />
                Run Plan
              </button>
              <div className="ml-auto flex gap-2">
                <button className="px-3 py-2 bg-green-100 text-green-700 rounded-[12px] hover:bg-green-200 transition-all">
                  <ThumbsUp className="w-4 h-4" />
                </button>
                <button className="px-3 py-2 bg-red-100 text-red-700 rounded-[12px] hover:bg-red-200 transition-all">
                  <ThumbsDown className="w-4 h-4" />
                </button>
              </div>
            </div>
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
          
          <div className="space-y-3">
            {planSteps.map((step, index) => (
              <div
                key={index}
                className="p-4 bg-accent/50 rounded-[16px] border border-border/50"
              >
                <p className="font-medium text-sm mb-2">{step.step}</p>
                <div className="space-y-1 text-xs text-muted-foreground">
                  <p><span className="font-medium">Tool:</span> {step.tool}</p>
                  <p><span className="font-medium">Model:</span> {step.model}</p>
                  <p className="text-xs mt-2 italic">{step.rationale}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 bg-secondary/10 rounded-[12px] text-xs">
            <p className="font-medium text-secondary mb-1">Cost Estimate</p>
            <p className="text-muted-foreground">~$0.0023 per request</p>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
