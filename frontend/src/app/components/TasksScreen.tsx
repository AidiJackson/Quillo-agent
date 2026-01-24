import React, { useState, useEffect } from 'react';
import { fetchTaskIntents, TaskIntentOut, TaskPlanOut, createTaskPlan, fetchTaskPlan, approveTaskPlan, fetchTaskSteps, completeTaskStep, TaskStepsOut } from '../../lib/quilloApi';
import { CheckCircle2, Circle, XCircle, RefreshCw, Loader2, ChevronDown, ChevronRight, List, FileText, Check, Play } from 'lucide-react';

/**
 * TasksScreen - Read-only view of Task Intents (v1)
 *
 * Shows approved work that the user has asked Uorin to do.
 * Minimal, ChatGPT-native design.
 */
export function TasksScreen() {
  const [tasks, setTasks] = useState<TaskIntentOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedScopes, setExpandedScopes] = useState<Set<string>>(new Set());
  const [expandedPlans, setExpandedPlans] = useState<Set<string>>(new Set());
  const [plans, setPlans] = useState<Record<string, TaskPlanOut>>({});
  const [generatingPlan, setGeneratingPlan] = useState<string | null>(null);
  const [approvingPlan, setApprovingPlan] = useState<string | null>(null);
  const [stepStates, setStepStates] = useState<Record<string, TaskStepsOut>>({});
  const [loadingSteps, setLoadingSteps] = useState<string | null>(null);
  const [runningStep, setRunningStep] = useState<string | null>(null); // taskId:stepNum

  const loadTasks = async (showRefreshing = false) => {
    try {
      if (showRefreshing) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      // For v1, fetch all recent tasks (no user filtering yet)
      const data = await fetchTaskIntents(undefined, 50);
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
            <Circle className="w-3 h-3" />
            Approved
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle2 className="w-3 h-3" />
            Completed
          </span>
        );
      case 'cancelled':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400">
            <XCircle className="w-3 h-3" />
            Cancelled
          </span>
        );
      default:
        return null;
    }
  };

  const toggleScope = (taskId: string) => {
    setExpandedScopes(prev => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  };

  const hasScope = (task: TaskIntentOut): boolean => {
    return !!(task.scope_will_do?.length || task.scope_wont_do?.length || task.scope_done_when);
  };

  const togglePlan = async (taskId: string) => {
    const isCurrentlyExpanded = expandedPlans.has(taskId);

    setExpandedPlans(prev => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });

    // Load step state when expanding an approved plan
    if (!isCurrentlyExpanded && plans[taskId]?.status === 'approved' && !stepStates[taskId]) {
      await loadStepState(taskId);
    }
  };

  const loadStepState = async (taskId: string) => {
    try {
      setLoadingSteps(taskId);
      const steps = await fetchTaskSteps(taskId);
      setStepStates(prev => ({ ...prev, [taskId]: steps }));
    } catch (err) {
      console.error('Failed to load step state:', err);
    } finally {
      setLoadingSteps(null);
    }
  };

  const handleRunStep = async (taskId: string, stepNum: number) => {
    try {
      const stepKey = `${taskId}:${stepNum}`;
      setRunningStep(stepKey);
      await completeTaskStep(taskId, stepNum);
      // Refresh step state
      await loadStepState(taskId);
    } catch (err) {
      console.error('Failed to run step:', err);
    } finally {
      setRunningStep(null);
    }
  };

  const handleGeneratePlan = async (taskId: string) => {
    try {
      setGeneratingPlan(taskId);
      const plan = await createTaskPlan(taskId);
      setPlans(prev => ({ ...prev, [taskId]: plan }));
      setExpandedPlans(prev => new Set(prev).add(taskId));
    } catch (err) {
      console.error('Failed to generate plan:', err);
    } finally {
      setGeneratingPlan(null);
    }
  };

  const handleApprovePlan = async (taskId: string) => {
    try {
      setApprovingPlan(taskId);
      const approvedPlan = await approveTaskPlan(taskId);
      setPlans(prev => ({ ...prev, [taskId]: approvedPlan }));
    } catch (err) {
      console.error('Failed to approve plan:', err);
    } finally {
      setApprovingPlan(null);
    }
  };

  const getPlanStatus = (status: string) => {
    switch (status) {
      case 'draft':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400">
            Draft
          </span>
        );
      case 'approved':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
            Approved
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
            Rejected
          </span>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">Loading tasks...</p>
        </div>
      </div>
    );
  }

  if (error) {
    // Show friendly error for setup/backend issues (500 errors)
    const isSetupError = error.includes('500') || error.includes('fetch failed') || error.includes('network');
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="w-12 h-12 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mx-auto mb-3">
            <Circle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {isSetupError ? "Tasks aren't available right now" : "Failed to load tasks"}
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            {isSetupError
              ? "Setup incomplete. Nothing is lost - your tasks will appear once the service is ready."
              : error}
          </p>
          <button
            onClick={() => loadTasks()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-none border-b border-border bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Tasks</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Approved work you've asked Uorin to do.
              </p>
            </div>
            <button
              onClick={() => loadTasks(true)}
              disabled={refreshing}
              className="p-2 hover:bg-accent rounded-lg transition-colors disabled:opacity-50"
              title="Refresh tasks"
            >
              <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Tasks List */}
      <div className="flex-1 overflow-y-auto">
        {tasks.length === 0 ? (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 rounded-full bg-accent flex items-center justify-center mx-auto mb-4">
                <Circle className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">No tasks yet</h3>
              <p className="text-sm text-muted-foreground">
                When you approve work, it will appear here.
              </p>
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-3">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="bg-white dark:bg-slate-900 border border-border rounded-[16px] p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium mb-2 leading-relaxed">
                      {task.intent_text}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{formatDate(task.created_at)}</span>
                      {task.origin_chat_id && (
                        <>
                          <span>•</span>
                          <span className="truncate">Chat {task.origin_chat_id.slice(0, 8)}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex-none">
                    {getStatusBadge(task.status)}
                  </div>
                </div>

                {/* Task Scope v1 - Collapsible */}
                {hasScope(task) && (
                  <div className="mt-3 pt-3 border-t border-border/50">
                    <button
                      onClick={() => toggleScope(task.id)}
                      className="flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors w-full"
                    >
                      {expandedScopes.has(task.id) ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                      <span>Task Scope</span>
                    </button>

                    {expandedScopes.has(task.id) && (
                      <div className="mt-3 space-y-3 text-xs">
                        {task.scope_will_do && task.scope_will_do.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-foreground mb-1.5">Will do:</h4>
                            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                              {task.scope_will_do.map((item, idx) => (
                                <li key={idx} className="leading-relaxed">{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {task.scope_wont_do && task.scope_wont_do.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-foreground mb-1.5">Won't do:</h4>
                            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                              {task.scope_wont_do.map((item, idx) => (
                                <li key={idx} className="leading-relaxed">{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {task.scope_done_when && (
                          <div>
                            <h4 className="font-semibold text-foreground mb-1.5">Done when:</h4>
                            <p className="text-muted-foreground leading-relaxed">{task.scope_done_when}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Task Plan v2 Phase 1 */}
                <div className="mt-3 pt-3 border-t border-border/50">
                  {plans[task.id] ? (
                    <>
                      <button
                        onClick={() => togglePlan(task.id)}
                        className="flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors w-full"
                      >
                        {expandedPlans.has(task.id) ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5" />
                        )}
                        <List className="w-3.5 h-3.5" />
                        <span>Execution Plan</span>
                        <div className="ml-auto">{getPlanStatus(plans[task.id].status)}</div>
                      </button>

                      {expandedPlans.has(task.id) && (
                        <div className="mt-3 space-y-3 text-xs">
                          {plans[task.id].summary && (
                            <div className="p-2 bg-accent/50 rounded">
                              <p className="text-foreground font-medium">{plans[task.id].summary}</p>
                            </div>
                          )}

                          <div>
                            <h4 className="font-semibold text-foreground mb-2">Steps:</h4>
                            {loadingSteps === task.id ? (
                              <div className="flex items-center gap-2 p-2 text-muted-foreground">
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                <span className="text-xs">Loading step state...</span>
                              </div>
                            ) : (
                              <ol className="space-y-2">
                                {plans[task.id].plan_steps.map((step, idx) => {
                                  const stepState = stepStates[task.id]?.steps.find(s => s.step_num === step.step_num);
                                  const isCompleted = stepState?.status === 'completed';
                                  const isPlanApproved = plans[task.id].status === 'approved';
                                  const stepKey = `${task.id}:${step.step_num}`;
                                  const isRunning = runningStep === stepKey;

                                  return (
                                    <li key={idx} className="flex items-start gap-2">
                                      {isPlanApproved && stepState && (
                                        <div className="flex-none mt-0.5">
                                          {isCompleted ? (
                                            <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                                          ) : (
                                            <Circle className="w-4 h-4 text-muted-foreground" />
                                          )}
                                        </div>
                                      )}
                                      <span className="font-semibold text-muted-foreground min-w-[20px]">{step.step_num}.</span>
                                      <div className="flex-1 min-w-0">
                                        <span className="text-muted-foreground leading-relaxed">{step.description}</span>
                                        {isPlanApproved && stepState && !isCompleted && (
                                          <button
                                            onClick={() => handleRunStep(task.id, step.step_num)}
                                            disabled={isRunning}
                                            className="flex items-center gap-1.5 mt-1.5 px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors disabled:opacity-50 text-xs font-medium"
                                          >
                                            {isRunning ? (
                                              <>
                                                <Loader2 className="w-3 h-3 animate-spin" />
                                                <span>Running...</span>
                                              </>
                                            ) : (
                                              <>
                                                <Play className="w-3 h-3" />
                                                <span>Run step</span>
                                              </>
                                            )}
                                          </button>
                                        )}
                                        {isPlanApproved && stepState?.completed_at && (
                                          <div className="mt-1 text-[10px] text-muted-foreground">
                                            Completed {new Date(stepState.completed_at).toLocaleString()}
                                          </div>
                                        )}
                                      </div>
                                    </li>
                                  );
                                })}
                              </ol>
                            )}
                          </div>

                          {/* Approval section */}
                          {plans[task.id].status === 'draft' && (
                            <button
                              onClick={() => handleApprovePlan(task.id)}
                              disabled={approvingPlan === task.id}
                              className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 text-xs font-medium"
                            >
                              {approvingPlan === task.id ? (
                                <>
                                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                  <span>Approving...</span>
                                </>
                              ) : (
                                <>
                                  <Check className="w-3.5 h-3.5" />
                                  <span>Approve plan</span>
                                </>
                              )}
                            </button>
                          )}

                          {plans[task.id].status === 'approved' && plans[task.id].approved_at && (
                            <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
                              <p className="text-green-700 dark:text-green-400 text-xs">
                                <Check className="w-3 h-3 inline mr-1" />
                                Approved {new Date(plans[task.id].approved_at!).toLocaleString()}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  ) : (
                    <button
                      onClick={() => handleGeneratePlan(task.id)}
                      disabled={generatingPlan === task.id}
                      className="flex items-center gap-2 text-xs font-medium text-primary hover:text-primary/80 transition-colors w-full disabled:opacity-50"
                    >
                      {generatingPlan === task.id ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Generating plan...</span>
                        </>
                      ) : (
                        <>
                          <FileText className="w-3.5 h-3.5" />
                          <span>Generate execution plan</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
