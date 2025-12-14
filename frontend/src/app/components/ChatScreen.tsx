import React, { useState } from 'react';
import { GlassCard } from './GlassCard';
import { Send, ThumbsUp, ThumbsDown, Sparkles, Brain, Play } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
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

  const handleSend = () => {
    if (!input.trim()) return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    
    setMessages([...messages, newMessage]);
    setInput('');
    
    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I\'m processing your request using the optimal model and tools. This is a simulated response for the MVP.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    }, 1000);
  };

  return (
    <div className="flex-1 flex gap-6 h-full overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] ${
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
