/**
 * Quillo API Client
 *
 * Uses server-side proxy (BFF) to avoid exposing API keys in the browser.
 * The UI token is for dev-only scaffolding; production will use session auth.
 */

const API_BASE = import.meta.env.VITE_QUILLO_API_BASE || '/ui/api';
const UI_TOKEN = import.meta.env.VITE_UI_TOKEN || '';

export interface RouteRequest {
  text: string;
  user_id: string;
  context?: Record<string, any>;
}

export interface RouteResponse {
  intent: string;
  reasons: string[];
  slots?: Record<string, any> | null;
}

export interface HealthResponse {
  status: string;
}

export interface AuthStatusResponse {
  env: string;
  ui_token_required: boolean;
  ui_token_configured: boolean;
  hint: string | null;
}

export interface ConfigResponse {
  raw_chat_mode: boolean;
}

export interface PlanRequest {
  intent: string;
  text?: string;
  slots?: Record<string, any> | null;
  user_id?: string;
}

export interface PlanStep {
  tool: string;
  premium?: boolean;
  rationale: string;
}

export interface PlanResponse {
  steps: PlanStep[];
  trace_id: string;
}

export interface AskRequest {
  text: string;
  user_id?: string;
}

export interface AskResponse {
  answer: string;
  model: string;
  trace_id: string;
}

export interface ExecuteRequest {
  user_id?: string;
  text: string;
  intent: string;
  slots?: Record<string, any> | null;
  plan_steps: PlanStep[];
  dry_run?: boolean;
}

export interface ExecutionArtifact {
  step_index: number;
  tool: string;
  input_excerpt: string;
  output_excerpt: string;
}

export interface ExecuteResponse {
  output_text: string;
  artifacts: ExecutionArtifact[];
  trace_id: string;
  provider_used: string;
  warnings: string[];
}

export interface JudgmentRequest {
  text: string;
  user_id?: string;
  intent?: string;
  context?: Record<string, any>;
}

export interface JudgmentResponse {
  stakes: 'low' | 'medium' | 'high';
  what_i_see: string;
  why_it_matters: string | null;
  recommendation: string;
  requires_confirmation: boolean;
  formatted_message: string;
  // Interaction Contract v1 fields
  mode?: 'answer' | 'clarify' | 'confirm_required' | 'cannot_do_yet';
  assistant_message?: string;
  questions?: string[];
  suggested_next_step?: string;
}

/**
 * Check backend health status
 */
export async function health(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Check UI auth status (no auth required)
 * Returns info about whether UI token auth is configured/required
 */
export async function authStatus(): Promise<AuthStatusResponse> {
  const response = await fetch(`${API_BASE}/auth/status`);

  if (!response.ok) {
    throw new Error(`Auth status check failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Check if UI token is configured in the frontend
 */
export function hasUiToken(): boolean {
  return Boolean(UI_TOKEN);
}

/**
 * Get backend configuration (no auth required)
 * Returns mode settings for frontend adaptation
 */
export async function config(): Promise<ConfigResponse> {
  const response = await fetch(`${API_BASE}/config`);

  if (!response.ok) {
    throw new Error(`Config check failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Route user input to appropriate intent
 */
export async function route(text: string, userId: string): Promise<RouteResponse> {
  const request: RouteRequest = {
    text,
    user_id: userId,
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add UI token if configured (dev-only)
  if (UI_TOKEN) {
    headers['X-UI-Token'] = UI_TOKEN;
  }

  const response = await fetch(`${API_BASE}/route`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Route failed: ${response.status} - ${error}`);
  }

  return response.json();
}

/**
 * Generate execution plan for given intent
 */
export async function plan(
  intent: string,
  text?: string,
  slots?: Record<string, any> | null,
  userId?: string
): Promise<PlanResponse> {
  const request: PlanRequest = {
    intent,
    text,
    slots,
    user_id: userId,
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add UI token if configured (dev-only)
  if (UI_TOKEN) {
    headers['X-UI-Token'] = UI_TOKEN;
  }

  const response = await fetch(`${API_BASE}/plan`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Plan failed: ${response.status} - ${error}`);
  }

  return response.json();
}

/**
 * Ask Quillopreneur for business advice
 */
export async function ask(text: string, userId?: string): Promise<AskResponse> {
  const request: AskRequest = {
    text,
    user_id: userId,
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add UI token if configured (dev-only)
  if (UI_TOKEN) {
    headers['X-UI-Token'] = UI_TOKEN;
  }

  const response = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Ask failed: ${response.status} - ${error}`);
  }

  return response.json();
}

/**
 * Get judgment explanation for user input
 * Works offline - no LLM required, pure heuristic assessment
 */
export async function judgment(
  text: string,
  userId?: string,
  intent?: string,
  context?: Record<string, any>
): Promise<JudgmentResponse> {
  const request: JudgmentRequest = {
    text,
    user_id: userId,
    intent,
    context,
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add UI token if configured (dev-only)
  if (UI_TOKEN) {
    headers['X-UI-Token'] = UI_TOKEN;
  }

  const response = await fetch(`${API_BASE}/judgment`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Judgment failed: ${response.status} - ${error}`);
  }

  return response.json();
}

/**
 * Execute a plan by running each step
 */
export async function execute(
  text: string,
  intent: string,
  planSteps: PlanStep[],
  slots?: Record<string, any> | null,
  userId?: string,
  dryRun: boolean = true
): Promise<ExecuteResponse> {
  const request: ExecuteRequest = {
    user_id: userId,
    text,
    intent,
    slots,
    plan_steps: planSteps,
    dry_run: dryRun,
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add UI token if configured (dev-only)
  if (UI_TOKEN) {
    headers['X-UI-Token'] = UI_TOKEN;
  }

  const response = await fetch(`${API_BASE}/execute`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Execute failed: ${response.status} - ${error}`);
  }

  return response.json();
}

export interface MultiAgentMessage {
  role: string;
  agent: string;
  content: string;
  model_id?: string | null;
  live: boolean;
  unavailable_reason?: string | null;
}

export interface MultiAgentRequest {
  text: string;
  user_id?: string;
  agents?: string[];
}

export interface MultiAgentResponse {
  messages: MultiAgentMessage[];
  provider: string;
  trace_id: string;
  fallback_reason?: string | null;
  peers_unavailable?: boolean;
}

/**
 * Multi-agent chat (v0)
 * Get perspectives from multiple agents in one conversation
 */
export async function multiAgent(
  text: string,
  userId?: string,
  agents?: string[]
): Promise<MultiAgentResponse> {
  const request: MultiAgentRequest = {
    text,
    user_id: userId,
    agents,
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add UI token if configured (dev-only)
  if (UI_TOKEN) {
    headers['X-UI-Token'] = UI_TOKEN;
  }

  const response = await fetch(`${API_BASE}/multi-agent`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Multi-agent chat failed: ${response.status} - ${error}`);
  }

  return response.json();
}

/**
 * Evidence Layer v1 - Manual-only, sourced, non-authorial evidence retrieval
 */

export interface EvidenceFact {
  text: string;
  source_id: string;
  published_at?: string | null;
}

export interface EvidenceSource {
  id: string;
  title: string;
  domain: string;
  url: string;
  retrieved_at: string;
}

export interface EvidenceRequest {
  query?: string | null;
  use_last_message?: boolean;
}

export interface EvidenceResponse {
  ok: boolean;
  retrieved_at: string;
  duration_ms: number;
  facts: EvidenceFact[];
  sources: EvidenceSource[];
  limits?: string | null;
  error?: string | null;
}

/**
 * Retrieve evidence with sources and timestamps
 * Evidence Layer v1: Manual-only, non-authorial facts
 */
export async function fetchEvidence(
  query?: string,
  useLastMessage?: boolean
): Promise<EvidenceResponse> {
  const request: EvidenceRequest = {
    query: query || null,
    use_last_message: useLastMessage || false,
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add UI token if configured (dev-only)
  if (UI_TOKEN) {
    headers['X-UI-Token'] = UI_TOKEN;
  }

  const response = await fetch(`${API_BASE}/evidence`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Evidence retrieval failed: ${response.status} - ${error}`);
  }

  return response.json();
}
