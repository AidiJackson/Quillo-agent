import React, { useState } from 'react';
import { GlassCard } from './GlassCard';
import { ChevronDown, ChevronRight, ThumbsUp, ThumbsDown, Clock, Cpu } from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: Date;
  request: string;
  intent: string;
  model: string;
  steps: string[];
  feedback?: 'positive' | 'negative';
  duration: string;
  cost: string;
}

export function AuditLogScreen() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const logs: LogEntry[] = [
    {
      id: '1',
      timestamp: new Date('2024-12-14T10:30:00'),
      request: 'Help me draft a response to an angry client email',
      intent: 'Email Composition - Conflict Resolution',
      model: 'Premium (o3-mini)',
      steps: [
        'Detected emotional tone in client message',
        'Generated empathetic response framework',
        'Applied professional clarity filter',
      ],
      feedback: 'positive',
      duration: '2.3s',
      cost: '$0.0082',
    },
    {
      id: '2',
      timestamp: new Date('2024-12-14T09:15:00'),
      request: 'Summarize the key points from yesterday\'s team meeting',
      intent: 'Information Extraction',
      model: 'Balanced (GPT-4o)',
      steps: [
        'Parsed meeting transcript',
        'Identified action items',
        'Created structured summary',
      ],
      feedback: 'positive',
      duration: '1.8s',
      cost: '$0.0015',
    },
    {
      id: '3',
      timestamp: new Date('2024-12-14T08:45:00'),
      request: 'What\'s the weather today?',
      intent: 'Quick Query',
      model: 'Fast (GPT-4o-mini)',
      steps: ['Routed to weather API', 'Formatted response'],
      duration: '0.4s',
      cost: '$0.0003',
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-semibold">Activity & Audit Log</h2>
          <p className="text-muted-foreground mt-1">
            See how Uorin processes your requests and makes decisions
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <GlassCard className="p-4">
            <p className="text-sm text-muted-foreground mb-1">Requests Today</p>
            <p className="text-2xl font-semibold">37</p>
          </GlassCard>
          <GlassCard className="p-4">
            <p className="text-sm text-muted-foreground mb-1">Avg Response Time</p>
            <p className="text-2xl font-semibold">1.5s</p>
          </GlassCard>
          <GlassCard className="p-4">
            <p className="text-sm text-muted-foreground mb-1">Satisfaction</p>
            <p className="text-2xl font-semibold text-green-600">94%</p>
          </GlassCard>
          <GlassCard className="p-4">
            <p className="text-sm text-muted-foreground mb-1">Cost Today</p>
            <p className="text-2xl font-semibold">$0.18</p>
          </GlassCard>
        </div>

        {/* Timeline */}
        <div className="space-y-3">
          {logs.map((log) => {
            const isExpanded = expandedId === log.id;
            return (
              <GlassCard key={log.id} className="overflow-hidden">
                <button
                  onClick={() => setExpandedId(isExpanded ? null : log.id)}
                  className="w-full p-5 text-left hover:bg-accent/30 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      {isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <p className="font-medium text-sm truncate">{log.request}</p>
                          {log.feedback === 'positive' ? (
                            <ThumbsUp className="w-4 h-4 text-green-600 flex-shrink-0" />
                          ) : log.feedback === 'negative' ? (
                            <ThumbsDown className="w-4 h-4 text-red-600 flex-shrink-0" />
                          ) : null}
                        </div>
                        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {log.timestamp.toLocaleTimeString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <Cpu className="w-3 h-3" />
                            {log.model}
                          </span>
                          <span>{log.duration}</span>
                          <span>{log.cost}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </button>

                {isExpanded && (
                  <div className="px-5 pb-5 space-y-4 border-t border-border pt-4 mt-2">
                    <div>
                      <p className="text-sm font-medium mb-2">Detected Intent</p>
                      <div className="px-3 py-2 bg-primary/10 text-primary rounded-[12px] text-sm inline-block">
                        {log.intent}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-medium mb-3">Processing Steps</p>
                      <div className="space-y-2">
                        {log.steps.map((step, index) => (
                          <div key={index} className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-secondary/20 text-secondary flex items-center justify-center text-xs font-medium flex-shrink-0">
                              {index + 1}
                            </div>
                            <p className="text-sm text-muted-foreground pt-0.5">{step}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Model Selection</p>
                        <p className="text-sm font-medium">{log.model}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Chosen for: {log.model.includes('Premium') ? 'Complex reasoning required' : log.model.includes('Balanced') ? 'Balanced performance' : 'Quick response needed'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Performance</p>
                        <p className="text-sm font-medium">Duration: {log.duration}</p>
                        <p className="text-xs text-muted-foreground mt-1">Cost: {log.cost}</p>
                      </div>
                    </div>
                  </div>
                )}
              </GlassCard>
            );
          })}
        </div>

        {/* Export */}
        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Export Audit Log</p>
              <p className="text-sm text-muted-foreground mt-1">
                Download full activity history for compliance or analysis
              </p>
            </div>
            <button className="px-5 py-2.5 bg-accent text-accent-foreground rounded-[16px] hover:bg-accent/80 transition-all">
              Export CSV
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
