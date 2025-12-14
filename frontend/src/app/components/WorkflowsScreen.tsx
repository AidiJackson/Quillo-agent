import React, { useState } from 'react';
import { GlassCard } from './GlassCard';
import { Plus, Play, Edit, Trash2, Zap } from 'lucide-react';

interface Workflow {
  id: string;
  name: string;
  trigger: string;
  steps: string[];
  mode: 'Fast' | 'Balanced' | 'Premium';
}

export function WorkflowsScreen() {
  const [workflows, setWorkflows] = useState<Workflow[]>([
    {
      id: '1',
      name: 'Defuse Client Conflict Email',
      trigger: 'Angry client email detected',
      steps: ['Analyze tone', 'Generate empathetic response', 'Apply clarity filter'],
      mode: 'Premium',
    },
    {
      id: '2',
      name: 'Weekly Team Summary',
      trigger: 'Every Monday 9 AM',
      steps: ['Gather metrics', 'Summarize achievements', 'Create action items'],
      mode: 'Balanced',
    },
  ]);
  const [showNewWorkflow, setShowNewWorkflow] = useState(false);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Workflows</h2>
            <p className="text-muted-foreground mt-1">Automate your AI tasks and routines</p>
          </div>
          <button
            onClick={() => setShowNewWorkflow(true)}
            className="px-5 py-2.5 bg-gradient-to-r from-primary to-secondary text-white rounded-[16px] hover:shadow-lg transition-all flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            New Workflow
          </button>
        </div>

        {/* Workflows Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {workflows.map((workflow) => (
            <GlassCard key={workflow.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-lg mb-1">{workflow.name}</h3>
                  <p className="text-sm text-muted-foreground">{workflow.trigger}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    workflow.mode === 'Fast'
                      ? 'bg-green-100 text-green-700'
                      : workflow.mode === 'Balanced'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-purple-100 text-purple-700'
                  }`}
                >
                  {workflow.mode}
                </span>
              </div>

              <div className="space-y-2 mb-4">
                {workflow.steps.map((step, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm">
                    <div className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs">
                      {index + 1}
                    </div>
                    <span>{step}</span>
                  </div>
                ))}
              </div>

              <div className="flex gap-2 pt-4 border-t border-border">
                <button className="flex-1 px-4 py-2 bg-primary/10 text-primary rounded-[12px] hover:bg-primary/20 transition-all flex items-center justify-center gap-2">
                  <Play className="w-4 h-4" />
                  Run
                </button>
                <button className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all">
                  <Edit className="w-4 h-4" />
                </button>
                <button className="px-4 py-2 bg-destructive/10 text-destructive rounded-[12px] hover:bg-destructive/20 transition-all">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </GlassCard>
          ))}

          {/* New Workflow Card */}
          {showNewWorkflow && (
            <GlassCard className="p-6 border-2 border-dashed border-primary/30">
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Workflow name..."
                  className="w-full px-4 py-2 bg-input-background border border-border rounded-[12px] focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <input
                  type="text"
                  placeholder="Trigger (e.g., 'When email contains...')"
                  className="w-full px-4 py-2 bg-input-background border border-border rounded-[12px] focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <div className="space-y-2">
                  <label className="text-sm font-medium">Steps</label>
                  <input
                    type="text"
                    placeholder="Step 1: Response..."
                    className="w-full px-4 py-2 bg-input-background border border-border rounded-[12px] focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Model Mode</label>
                  <div className="flex gap-2">
                    {['Fast', 'Balanced', 'Premium'].map((mode) => (
                      <button
                        key={mode}
                        className="flex-1 px-3 py-2 bg-accent rounded-[12px] hover:bg-primary hover:text-white transition-all text-sm"
                      >
                        {mode}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="flex-1 px-4 py-2 bg-primary text-white rounded-[12px] hover:shadow-lg transition-all">
                    Save
                  </button>
                  <button
                    onClick={() => setShowNewWorkflow(false)}
                    className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </GlassCard>
          )}
        </div>

        {/* Quick Actions */}
        <GlassCard className="p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-secondary" />
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <button className="p-4 bg-accent/50 rounded-[16px] text-left hover:bg-accent transition-all">
              <p className="font-medium mb-1">Import Template</p>
              <p className="text-xs text-muted-foreground">Start from pre-built workflows</p>
            </button>
            <button className="p-4 bg-accent/50 rounded-[16px] text-left hover:bg-accent transition-all">
              <p className="font-medium mb-1">Schedule Batch</p>
              <p className="text-xs text-muted-foreground">Run multiple workflows at once</p>
            </button>
            <button className="p-4 bg-accent/50 rounded-[16px] text-left hover:bg-accent transition-all">
              <p className="font-medium mb-1">View Analytics</p>
              <p className="text-xs text-muted-foreground">See workflow performance</p>
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
