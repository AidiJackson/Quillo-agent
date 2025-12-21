import React, { useState } from 'react';
import { GlassCard } from './GlassCard';
import { Zap, BarChart3, Sparkles, DollarSign } from 'lucide-react';

export function SettingsScreen() {
  const [mode, setMode] = useState<'Fast' | 'Balanced' | 'Premium'>('Balanced');
  const [taskModels, setTaskModels] = useState({
    email: 'Auto',
    negotiation: 'Auto',
    research: 'Auto',
    coding: 'Auto',
  });

  const modes = [
    {
      id: 'Fast' as const,
      name: 'Fast',
      icon: Zap,
      description: 'Quick responses, lower cost',
      model: 'GPT-4o-mini',
      cost: '$0.0003/request',
      color: 'green',
    },
    {
      id: 'Balanced' as const,
      name: 'Balanced',
      icon: BarChart3,
      description: 'Good balance of speed and quality',
      model: 'GPT-4o',
      cost: '$0.0015/request',
      color: 'blue',
    },
    {
      id: 'Premium' as const,
      name: 'Premium',
      icon: Sparkles,
      description: 'Best reasoning and accuracy',
      model: 'o3-mini',
      cost: '$0.0080/request',
      color: 'purple',
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-semibold">Model Settings</h2>
          <p className="text-muted-foreground mt-1">
            Configure how Uorin selects and uses AI models
          </p>
        </div>

        {/* Global Mode */}
        <GlassCard className="p-6">
          <h3 className="font-semibold text-lg mb-4">Global Mode</h3>
          <p className="text-sm text-muted-foreground mb-6">
            Choose the default intelligence level for all tasks
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {modes.map((modeOption) => {
              const Icon = modeOption.icon;
              const isActive = mode === modeOption.id;
              return (
                <button
                  key={modeOption.id}
                  onClick={() => setMode(modeOption.id)}
                  className={`p-6 rounded-[20px] border-2 transition-all text-left ${
                    isActive
                      ? `border-${modeOption.color}-500 bg-${modeOption.color}-50/50 shadow-lg`
                      : 'border-border hover:border-muted-foreground/30'
                  }`}
                >
                  <div
                    className={`w-12 h-12 rounded-[16px] mb-4 flex items-center justify-center ${
                      isActive
                        ? `bg-gradient-to-br ${
                            modeOption.color === 'green'
                              ? 'from-green-400 to-green-600'
                              : modeOption.color === 'blue'
                              ? 'from-blue-400 to-blue-600'
                              : 'from-purple-400 to-purple-600'
                          }`
                        : 'bg-accent'
                    }`}
                  >
                    <Icon className={`w-6 h-6 ${isActive ? 'text-white' : 'text-muted-foreground'}`} />
                  </div>
                  <h4 className="font-semibold mb-1">{modeOption.name}</h4>
                  <p className="text-xs text-muted-foreground mb-3">{modeOption.description}</p>
                  <div className="space-y-1 pt-3 border-t border-border">
                    <p className="text-xs font-medium">{modeOption.model}</p>
                    <p className="text-xs text-muted-foreground">{modeOption.cost}</p>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-6 p-4 bg-secondary/10 rounded-[16px] flex items-start gap-3">
            <DollarSign className="w-5 h-5 text-secondary flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-secondary">Cost Optimization</p>
              <p className="text-muted-foreground mt-1">
                {mode === 'Fast'
                  ? 'You\'re using the most economical option. Great for high-volume tasks!'
                  : mode === 'Balanced'
                  ? 'Good balance between cost and quality. Recommended for most use cases.'
                  : 'Premium mode delivers the best results. Consider for critical tasks.'}
              </p>
            </div>
          </div>
        </GlassCard>

        {/* Task-Specific Models */}
        <GlassCard className="p-6">
          <h3 className="font-semibold text-lg mb-4">Advanced: Task-Specific Models</h3>
          <p className="text-sm text-muted-foreground mb-6">
            Pin specific models for different task categories
          </p>

          <div className="space-y-4">
            {Object.entries(taskModels).map(([task, model]) => (
              <div key={task} className="flex items-center justify-between p-4 bg-accent/50 rounded-[16px]">
                <div>
                  <p className="font-medium capitalize">{task}</p>
                  <p className="text-xs text-muted-foreground">
                    {task === 'email'
                      ? 'Email composition and replies'
                      : task === 'negotiation'
                      ? 'Conflict resolution and persuasion'
                      : task === 'research'
                      ? 'Information gathering and analysis'
                      : 'Code generation and debugging'}
                  </p>
                </div>
                <select
                  value={model}
                  onChange={(e) =>
                    setTaskModels({ ...taskModels, [task]: e.target.value })
                  }
                  className="px-4 py-2 bg-input-background border border-border rounded-[12px] focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                >
                  <option>Auto</option>
                  <option>Fast</option>
                  <option>Balanced</option>
                  <option>Premium</option>
                </select>
              </div>
            ))}
          </div>

          <p className="text-xs text-muted-foreground mt-4">
            "Auto" lets Uorin intelligently select the best model for each task. Manual pinning
            overrides global settings.
          </p>
        </GlassCard>

        {/* Usage Stats */}
        <GlassCard className="p-6">
          <h3 className="font-semibold text-lg mb-4">This Month's Usage</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-50 dark:bg-green-950/20 rounded-[16px]">
              <p className="text-sm text-muted-foreground mb-1">Fast Requests</p>
              <p className="text-2xl font-semibold text-green-700">1,247</p>
              <p className="text-xs text-muted-foreground mt-1">$0.37 total</p>
            </div>
            <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-[16px]">
              <p className="text-sm text-muted-foreground mb-1">Balanced Requests</p>
              <p className="text-2xl font-semibold text-blue-700">583</p>
              <p className="text-xs text-muted-foreground mt-1">$0.87 total</p>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-950/20 rounded-[16px]">
              <p className="text-sm text-muted-foreground mb-1">Premium Requests</p>
              <p className="text-2xl font-semibold text-purple-700">127</p>
              <p className="text-xs text-muted-foreground mt-1">$1.02 total</p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
            <p className="font-medium">Total Cost</p>
            <p className="text-2xl font-semibold text-primary">$2.26</p>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
