/**
 * Uorin Mode Utility
 *
 * Manages the "Normal" vs "Work" mode toggle.
 * - Normal: Free chat mode (no auto guardrails, evidence can be fetched manually)
 * - Work: Judgment-first mode (evidence + stress-test + guardrails)
 */

export type UorinMode = 'normal' | 'work';

const STORAGE_KEY = 'uorin_mode';

/**
 * Get the current mode from localStorage.
 * Defaults to 'normal' if not set.
 */
export function getUorinMode(): UorinMode {
  if (typeof window === 'undefined') return 'normal';
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'normal' || stored === 'work') {
    return stored;
  }
  return 'normal';
}

/**
 * Set the mode and persist to localStorage.
 */
export function setUorinMode(mode: UorinMode): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, mode);
}

/**
 * Check if the current mode is "work".
 */
export function isWorkMode(): boolean {
  return getUorinMode() === 'work';
}

/**
 * Check if the current mode is "normal".
 */
export function isNormalMode(): boolean {
  return getUorinMode() === 'normal';
}
