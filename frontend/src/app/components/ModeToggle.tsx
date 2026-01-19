import React, { useState, useEffect } from 'react';
import { Briefcase, MessageCircle, CheckCircle } from 'lucide-react';
import {
  UorinMode,
  getStoredMode,
  setStoredMode,
  getModeDescription,
  getModeLabel
} from '../../lib/uorinMode';

interface ModeToggleProps {
  onModeChange?: (mode: UorinMode) => void;
  compact?: boolean;
}

/**
 * Mode Toggle Component (v1)
 * Allows user to switch between Work and Normal modes.
 */
export function ModeToggle({ onModeChange, compact = false }: ModeToggleProps) {
  const [currentMode, setCurrentMode] = useState<UorinMode>(() => getStoredMode());
  const [savedIndicator, setSavedIndicator] = useState(false);

  const handleModeChange = (newMode: UorinMode) => {
    if (newMode === currentMode) return;

    setCurrentMode(newMode);
    setStoredMode(newMode);

    // Show saved indicator briefly
    setSavedIndicator(true);
    setTimeout(() => setSavedIndicator(false), 1500);

    // Notify parent
    if (onModeChange) {
      onModeChange(newMode);
    }
  };

  if (compact) {
    // Compact version for chat header
    return (
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => handleModeChange(currentMode === 'work' ? 'normal' : 'work')}
          className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 transition-colors ${
            currentMode === 'work'
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
              : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
          }`}
        >
          {currentMode === 'work' ? (
            <>
              <Briefcase className="w-3 h-3" />
              <span className="hidden sm:inline">Work</span>
            </>
          ) : (
            <>
              <MessageCircle className="w-3 h-3" />
              <span className="hidden sm:inline">Normal</span>
            </>
          )}
        </button>
      </div>
    );
  }

  // Full version for settings
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold">Mode</h4>
          <p className="text-sm text-muted-foreground mt-1">
            Choose how Uorin behaves by default
          </p>
        </div>
        {savedIndicator && (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <CheckCircle className="w-4 h-4" />
            Saved
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Work Mode Option */}
        <button
          onClick={() => handleModeChange('work')}
          className={`p-4 rounded-[16px] border-2 transition-all text-left ${
            currentMode === 'work'
              ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/20 shadow-md'
              : 'border-border hover:border-muted-foreground/30'
          }`}
        >
          <div className="flex items-start gap-3">
            <div
              className={`w-10 h-10 rounded-[12px] flex items-center justify-center flex-shrink-0 ${
                currentMode === 'work'
                  ? 'bg-gradient-to-br from-blue-400 to-blue-600'
                  : 'bg-accent'
              }`}
            >
              <Briefcase
                className={`w-5 h-5 ${
                  currentMode === 'work' ? 'text-white' : 'text-muted-foreground'
                }`}
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold">Work</p>
              <p className="text-xs text-muted-foreground mt-1">
                {getModeDescription('work')}
              </p>
            </div>
          </div>
          {currentMode === 'work' && (
            <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Default mode. Evidence auto-fetches when needed. Stress test activates for big decisions.
              </p>
            </div>
          )}
        </button>

        {/* Normal Mode Option */}
        <button
          onClick={() => handleModeChange('normal')}
          className={`p-4 rounded-[16px] border-2 transition-all text-left ${
            currentMode === 'normal'
              ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/20 shadow-md'
              : 'border-border hover:border-muted-foreground/30'
          }`}
        >
          <div className="flex items-start gap-3">
            <div
              className={`w-10 h-10 rounded-[12px] flex items-center justify-center flex-shrink-0 ${
                currentMode === 'normal'
                  ? 'bg-gradient-to-br from-emerald-400 to-emerald-600'
                  : 'bg-accent'
              }`}
            >
              <MessageCircle
                className={`w-5 h-5 ${
                  currentMode === 'normal' ? 'text-white' : 'text-muted-foreground'
                }`}
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold">Normal</p>
              <p className="text-xs text-muted-foreground mt-1">
                {getModeDescription('normal')}
              </p>
            </div>
          </div>
          {currentMode === 'normal' && (
            <div className="mt-3 pt-3 border-t border-emerald-200 dark:border-emerald-800">
              <p className="text-xs text-emerald-700 dark:text-emerald-300">
                Free chat mode. No automatic guardrails. You can still manually fetch evidence.
              </p>
            </div>
          )}
        </button>
      </div>
    </div>
  );
}

/**
 * Compact mode indicator for chat header (read-only display)
 */
export function ModeIndicator() {
  const [currentMode, setCurrentMode] = useState<UorinMode>(() => getStoredMode());

  // Listen for storage changes (in case mode changes in another tab/component)
  useEffect(() => {
    const handleStorageChange = () => {
      setCurrentMode(getStoredMode());
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <div
      className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${
        currentMode === 'work'
          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
          : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
      }`}
    >
      {currentMode === 'work' ? (
        <>
          <Briefcase className="w-3 h-3" />
          <span className="hidden sm:inline">Work</span>
        </>
      ) : (
        <>
          <MessageCircle className="w-3 h-3" />
          <span className="hidden sm:inline">Normal</span>
        </>
      )}
    </div>
  );
}
