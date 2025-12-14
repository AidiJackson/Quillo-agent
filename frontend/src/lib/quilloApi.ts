/**
 * Quillo API Client
 *
 * TODO: Production should use a backend session/token or server-side proxy
 * instead of embedding the API key in the frontend.
 */

const API_BASE = import.meta.env.VITE_QUILLO_API_BASE || '/api';
const API_KEY = import.meta.env.VITE_QUILLO_API_KEY || '';

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
 * Route user input to appropriate intent
 */
export async function route(text: string, userId: string): Promise<RouteResponse> {
  const request: RouteRequest = {
    text,
    user_id: userId,
  };

  const response = await fetch(`${API_BASE}/route`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    },
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

  const response = await fetch(`${API_BASE}/plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    },
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
 *
 * TODO: Production should use a backend session/token or server-side proxy
 * instead of embedding the API key in the frontend.
 */
export async function ask(text: string, userId?: string): Promise<AskResponse> {
  const request: AskRequest = {
    text,
    user_id: userId,
  };

  const response = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Ask failed: ${response.status} - ${error}`);
  }

  return response.json();
}
