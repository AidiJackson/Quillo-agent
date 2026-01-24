import React, { useState, useEffect } from 'react';
import { GlassCard } from './GlassCard';
import { Zap, BarChart3, Sparkles, DollarSign, CheckCircle, ChevronDown, ChevronUp, Briefcase, MessageCircle } from 'lucide-react';
import { fetchUserPrefs, updateUserPrefs, UserPrefsOut } from '../../lib/quilloApi';
import { JudgmentProfileSettings } from './JudgmentProfileSettings';
import { getUorinMode, setUorinMode, UorinMode } from '../../lib/uorinMode';

export function SettingsScreen() {
  // Uorin mode: Normal vs Work
  const [uorinMode, setUorinModeState] = useState<UorinMode>(() => getUorinMode());

  // Model tier (Fast/Balanced/Premium)
  const [modelTier, setModelTier] = useState<'Fast' | 'Balanced' | 'Premium'>('Balanced');

  // Task-specific model overrides
  const [taskModels, setTaskModels] = useState({
    email: 'Auto',
    negotiation: 'Auto',
    research: 'Auto',
    coding: 'Auto',
  });

  // Task approval mode
  const [approvalMode, setApprovalMode] = useState<'confirm_every_step' | 'plan_then_auto' | 'auto_lowrisk_confirm_highrisk'>('plan_then_auto');
  const [loadingPrefs, setLoadingPrefs] = useState(true);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [savedIndicator, setSavedIndicator] = useState(false);

  // Advanced accordion state (for task-specific models)
  const [advancedOpen, setAdvancedOpen] = useState(false);

  // Load user preferences on mount
  useEffect(() => {
    const loadPrefs = async () => {
      try {
        const prefs = await fetchUserPrefs('global');
        setApprovalMode(prefs.approval_mode);
      } catch (error) {
        console.error('Failed to load user preferences:', error);
      } finally {
        setLoadingPrefs(false);
      }
    };
    loadPrefs();
  }, []);

  // Handle mode change
  const handleModeChange = (newMode: UorinMode) => {
    setUorinModeState(newMode);
    setUorinMode(newMode);
    // Dispatch custom event so App.tsx can react (e.g., hide Tasks nav)
    window.dispatchEvent(new Event('uorin-mode-change'));
  };

  const handleApprovalModeChange = async (newMode: 'confirm_every_step' | 'plan_then_auto' | 'auto_lowrisk_confirm_highrisk') => {
    setApprovalMode(newMode);
    setSavingPrefs(true);
    try {
      await updateUserPrefs({ approval_mode: newMode }, 'global');
      setSavedIndicator(true);
      setTimeout(() => setSavedIndicator(false), 2000);
    } catch (error) {
      console.error('Failed to save user preferences:', error);
    } finally {
      setSavingPrefs(false);
    }
  };

  const modelTiers = [
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

  const isWorkMode = uorinMode === 'work';

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6">
      <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-xl sm:text-2xl font-semibold">Settings</h2>
          <p className="text-muted-foreground mt-1 text-sm sm:text-base">
            Configure Uorin's behavior and model preferences
          </p>
        </div>

        {/* Mode Selector */}
        <GlassCard className="p-4 sm:p-6">
          <h3 className="font-semibold text-lg mb-2">Mode</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Choose how Uorin operates
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            {/* Normal Mode */}
            <button
              onClick={() => handleModeChange('normal')}
              className={`p-4 sm:p-5 rounded-[16px] sm:rounded-[20px] border-2 transition-all text-left ${
                uorinMode === 'normal'
                  ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 shadow-lg'
                  : 'border-border hover:border-muted-foreground/30'
              }`}
            >
              <div
                className={`w-10 h-10 sm:w-12 sm:h-12 rounded-[12px] sm:rounded-[16px] mb-3 sm:mb-4 flex items-center justify-center ${
                  uorinMode === 'normal'
                    ? 'bg-gradient-to-br from-blue-400 to-blue-600'
                    : 'bg-accent'
                }`}
              >
                <MessageCircle className={`w-5 h-5 sm:w-6 sm:h-6 ${uorinMode === 'normal' ? 'text-white' : 'text-muted-foreground'}`} />
              </div>
              <h4 className="font-semibold mb-1">Normal</h4>
              <p className="text-xs text-muted-foreground">
                Free chat (no auto guardrails). You can still manually fetch evidence.
              </p>
            </button>

            {/* Work Mode */}
            <button
              onClick={() => handleModeChange('work')}
              className={`p-4 sm:p-5 rounded-[16px] sm:rounded-[20px] border-2 transition-all text-left ${
                uorinMode === 'work'
                  ? 'border-purple-500 bg-purple-50/50 dark:bg-purple-950/30 shadow-lg'
                  : 'border-border hover:border-muted-foreground/30'
              }`}
            >
              <div
                className={`w-10 h-10 sm:w-12 sm:h-12 rounded-[12px] sm:rounded-[16px] mb-3 sm:mb-4 flex items-center justify-center ${
                  uorinMode === 'work'
                    ? 'bg-gradient-to-br from-purple-400 to-purple-600'
                    : 'bg-accent'
                }`}
              >
                <Briefcase className={`w-5 h-5 sm:w-6 sm:h-6 ${uorinMode === 'work' ? 'text-white' : 'text-muted-foreground'}`} />
              </div>
              <h4 className="font-semibold mb-1">Work</h4>
              <p className="text-xs text-muted-foreground">
                Judgment-first (evidence + stress-test + guardrails).
              </p>
            </button>
          </div>
        </GlassCard>

        {/* Global Model Tier */}
        <GlassCard className="p-4 sm:p-6">
          <h3 className="font-semibold text-lg mb-2">Global Model Tier</h3>
          <p className="text-sm text-muted-foreground mb-4 sm:mb-6">
            Choose the default intelligence level for all tasks
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
            {modelTiers.map((tierOption) => {
              const Icon = tierOption.icon;
              const isActive = modelTier === tierOption.id;
              return (
                <button
                  key={tierOption.id}
                  onClick={() => setModelTier(tierOption.id)}
                  className={`p-4 sm:p-6 rounded-[16px] sm:rounded-[20px] border-2 transition-all text-left ${
                    isActive
                      ? `border-${tierOption.color}-500 bg-${tierOption.color}-50/50 shadow-lg`
                      : 'border-border hover:border-muted-foreground/30'
                  }`}
                >
                  <div
                    className={`w-10 h-10 sm:w-12 sm:h-12 rounded-[12px] sm:rounded-[16px] mb-3 sm:mb-4 flex items-center justify-center ${
                      isActive
                        ? `bg-gradient-to-br ${
                            tierOption.color === 'green'
                              ? 'from-green-400 to-green-600'
                              : tierOption.color === 'blue'
                              ? 'from-blue-400 to-blue-600'
                              : 'from-purple-400 to-purple-600'
                          }`
                        : 'bg-accent'
                    }`}
                  >
                    <Icon className={`w-5 h-5 sm:w-6 sm:h-6 ${isActive ? 'text-white' : 'text-muted-foreground'}`} />
                  </div>
                  <h4 className="font-semibold mb-1">{tierOption.name}</h4>
                  <p className="text-xs text-muted-foreground mb-2 sm:mb-3">{tierOption.description}</p>
                  <div className="space-y-1 pt-2 sm:pt-3 border-t border-border">
                    <p className="text-xs font-medium">{tierOption.model}</p>
                    <p className="text-xs text-muted-foreground">{tierOption.cost}</p>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-secondary/10 rounded-[12px] sm:rounded-[16px] flex items-start gap-2 sm:gap-3">
            <DollarSign className="w-4 h-4 sm:w-5 sm:h-5 text-secondary flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-secondary">Cost Optimization</p>
              <p className="text-muted-foreground mt-1 text-xs sm:text-sm">
                {modelTier === 'Fast'
                  ? 'You\'re using the most economical option. Great for high-volume tasks!'
                  : modelTier === 'Balanced'
                  ? 'Good balance between cost and quality. Recommended for most use cases.'
                  : 'Premium mode delivers the best results. Consider for critical tasks.'}
              </p>
            </div>
          </div>
        </GlassCard>

        {/* Work-Only Section: Task Approval */}
        {isWorkMode && (
          <GlassCard className="p-4 sm:p-6">
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-lg">Task Approval</h3>
                  <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded-full">
                    Work mode only
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Controls how tasks progress once you approve them
                </p>
              </div>
              {savedIndicator && (
                <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                  <CheckCircle className="w-4 h-4" />
                  Saved
                </div>
              )}
            </div>

            {loadingPrefs ? (
              <div className="text-sm text-muted-foreground">Loading preferences...</div>
            ) : (
              <div className="space-y-2 sm:space-y-3">
                <label className="flex items-start gap-2 sm:gap-3 p-3 sm:p-4 bg-accent/50 rounded-[12px] sm:rounded-[16px] cursor-pointer hover:bg-accent transition-colors">
                  <input
                    type="radio"
                    name="approvalMode"
                    value="confirm_every_step"
                    checked={approvalMode === 'confirm_every_step'}
                    onChange={() => handleApprovalModeChange('confirm_every_step')}
                    disabled={savingPrefs}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-sm sm:text-base">Confirm every step</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      You'll be asked to approve each individual step before it runs
                    </p>
                  </div>
                </label>

                <label className="flex items-start gap-2 sm:gap-3 p-3 sm:p-4 bg-accent/50 rounded-[12px] sm:rounded-[16px] cursor-pointer hover:bg-accent transition-colors border-2 border-blue-500/50">
                  <input
                    type="radio"
                    name="approvalMode"
                    value="plan_then_auto"
                    checked={approvalMode === 'plan_then_auto'}
                    onChange={() => handleApprovalModeChange('plan_then_auto')}
                    disabled={savingPrefs}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-sm sm:text-base">Approve the plan, then auto-complete steps <span className="text-xs text-blue-600 dark:text-blue-400">(recommended)</span></p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Review the full plan first, then Uorin completes all steps automatically
                    </p>
                  </div>
                </label>

                <label className="flex items-start gap-2 sm:gap-3 p-3 sm:p-4 bg-accent/50 rounded-[12px] sm:rounded-[16px] cursor-pointer hover:bg-accent transition-colors opacity-50">
                  <input
                    type="radio"
                    name="approvalMode"
                    value="auto_lowrisk_confirm_highrisk"
                    checked={approvalMode === 'auto_lowrisk_confirm_highrisk'}
                    onChange={() => handleApprovalModeChange('auto_lowrisk_confirm_highrisk')}
                    disabled={true}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-sm sm:text-base">Auto-complete low-risk, confirm high-risk <span className="text-xs text-muted-foreground">(coming soon)</span></p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Uorin runs safe steps automatically, pauses for approval on sensitive actions
                    </p>
                  </div>
                </label>
              </div>
            )}
          </GlassCard>
        )}

        {/* Work-Only Section: Advanced Task-Specific Models (Accordion) */}
        {isWorkMode && (
          <GlassCard className="p-4 sm:p-6">
            <button
              onClick={() => setAdvancedOpen(!advancedOpen)}
              className="w-full flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-lg">Advanced: Task-Specific Models</h3>
                <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded-full">
                  Work mode only
                </span>
              </div>
              {advancedOpen ? (
                <ChevronUp className="w-5 h-5 text-muted-foreground" />
              ) : (
                <ChevronDown className="w-5 h-5 text-muted-foreground" />
              )}
            </button>

            {advancedOpen && (
              <div className="mt-4 space-y-4">
                <p className="text-sm text-muted-foreground">
                  Pin specific models for different task categories
                </p>

                <div className="space-y-3 sm:space-y-4">
                  {Object.entries(taskModels).map(([task, model]) => (
                    <div key={task} className="flex items-center justify-between p-3 sm:p-4 bg-accent/50 rounded-[12px] sm:rounded-[16px]">
                      <div>
                        <p className="font-medium capitalize text-sm sm:text-base">{task}</p>
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
                        className="px-3 sm:px-4 py-2 bg-input-background border border-border rounded-[10px] sm:rounded-[12px] focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                      >
                        <option>Auto</option>
                        <option>Fast</option>
                        <option>Balanced</option>
                        <option>Premium</option>
                      </select>
                    </div>
                  ))}
                </div>

                <p className="text-xs text-muted-foreground">
                  "Auto" lets Uorin intelligently select the best model for each task. Manual pinning
                  overrides global settings.
                </p>
              </div>
            )}
          </GlassCard>
        )}

        {/* Judgment Profile (always visible) */}
        <JudgmentProfileSettings />

        {/* Usage Stats (always visible) */}
        <GlassCard className="p-4 sm:p-6">
          <h3 className="font-semibold text-lg mb-3 sm:mb-4">This Month's Usage</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
            <div className="p-3 sm:p-4 bg-green-50 dark:bg-green-950/20 rounded-[12px] sm:rounded-[16px]">
              <p className="text-sm text-muted-foreground mb-1">Fast Requests</p>
              <p className="text-xl sm:text-2xl font-semibold text-green-700">1,247</p>
              <p className="text-xs text-muted-foreground mt-1">$0.37 total</p>
            </div>
            <div className="p-3 sm:p-4 bg-blue-50 dark:bg-blue-950/20 rounded-[12px] sm:rounded-[16px]">
              <p className="text-sm text-muted-foreground mb-1">Balanced Requests</p>
              <p className="text-xl sm:text-2xl font-semibold text-blue-700">583</p>
              <p className="text-xs text-muted-foreground mt-1">$0.87 total</p>
            </div>
            <div className="p-3 sm:p-4 bg-purple-50 dark:bg-purple-950/20 rounded-[12px] sm:rounded-[16px]">
              <p className="text-sm text-muted-foreground mb-1">Premium Requests</p>
              <p className="text-xl sm:text-2xl font-semibold text-purple-700">127</p>
              <p className="text-xs text-muted-foreground mt-1">$1.02 total</p>
            </div>
          </div>
          <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-border flex items-center justify-between">
            <p className="font-medium">Total Cost</p>
            <p className="text-xl sm:text-2xl font-semibold text-primary">$2.26</p>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
