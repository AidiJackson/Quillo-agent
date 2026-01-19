/**
 * Uorin Mode Toggle v1
 *
 * Frontend utilities for Work vs Normal mode.
 * Single source of truth for mode storage and normalization.
 */

// Mode type definition
export type UorinMode = "work" | "normal";

// Constants
export const DEFAULT_MODE: UorinMode = "work";
export const STORAGE_KEY = "uorin_default_mode_v1";

// Onboarding Q10 mapping key (from starter profile)
const ONBOARDING_PROFILE_KEY = "uorin_starter_profile_local";

/**
 * Normalize any value to a valid UorinMode.
 * Fail-safe: returns "work" for invalid/unknown values.
 */
export function normalizeMode(value: unknown): UorinMode {
  if (typeof value !== "string") {
    return DEFAULT_MODE;
  }

  const normalized = value.trim().toLowerCase();

  if (normalized === "work" || normalized === "normal") {
    return normalized;
  }

  return DEFAULT_MODE;
}

/**
 * Get the stored mode from localStorage.
 * If not set, attempts to bootstrap from onboarding Q10.
 */
export function getStoredMode(): UorinMode {
  // First, check if mode is already set
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    return normalizeMode(stored);
  }

  // Not set yet - try to bootstrap from onboarding Q10
  const onboardingProfile = localStorage.getItem(ONBOARDING_PROFILE_KEY);
  if (onboardingProfile) {
    try {
      const profile = JSON.parse(onboardingProfile);
      // Q10 is the default_mode question in onboarding
      // Expected values: "free" => "normal", "structured" => "work"
      const q10Value = profile?.Q10?.value;
      if (q10Value) {
        let bootstrappedMode: UorinMode = DEFAULT_MODE;
        if (q10Value === "free" || q10Value === "normal") {
          bootstrappedMode = "normal";
        } else if (q10Value === "structured" || q10Value === "work") {
          bootstrappedMode = "work";
        }
        // Set it once so we don't re-bootstrap
        setStoredMode(bootstrappedMode);
        return bootstrappedMode;
      }
    } catch (e) {
      // Ignore parse errors
    }
  }

  // Default to work mode
  return DEFAULT_MODE;
}

/**
 * Store the mode preference in localStorage.
 */
export function setStoredMode(mode: UorinMode): void {
  const normalized = normalizeMode(mode);
  localStorage.setItem(STORAGE_KEY, normalized);
}

/**
 * Check if current mode is work mode.
 */
export function isWorkMode(): boolean {
  return getStoredMode() === "work";
}

/**
 * Check if current mode is normal mode.
 */
export function isNormalMode(): boolean {
  return getStoredMode() === "normal";
}

/**
 * Get human-readable description of a mode.
 */
export function getModeDescription(mode: UorinMode): string {
  if (mode === "work") {
    return "Judgment-first (evidence + stress-test + guardrails)";
  }
  return "Free chat (no auto guardrails)";
}

/**
 * Get short label for a mode.
 */
export function getModeLabel(mode: UorinMode): string {
  return mode === "work" ? "Work" : "Normal";
}
