import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatScreen } from './components/ChatScreen';
import { WorksheetScreen } from './components/WorksheetScreen';
import { TasksScreen } from './components/TasksScreen';
import { WorkflowsScreen } from './components/WorkflowsScreen';
import { ProfileScreen } from './components/ProfileScreen';
import { SettingsScreen } from './components/SettingsScreen';
import { AuditLogScreen } from './components/AuditLogScreen';
import { IntegrationsScreen } from './components/IntegrationsScreen';
import { OnboardingWizard } from './components/OnboardingWizard';
import { Toaster } from './components/ui/sonner';
import { Menu } from 'lucide-react';
import { getJudgmentProfile } from '@/lib/quilloApi';
import { getUorinMode, type UorinMode } from '@/lib/uorinMode';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [showOnboardingWizard, setShowOnboardingWizard] = useState(false);
  const [profileCheckComplete, setProfileCheckComplete] = useState(false);
  const [mode, setMode] = useState<UorinMode>(getUorinMode);

  // Sync mode with localStorage changes (e.g., from SettingsScreen)
  useEffect(() => {
    const handleStorageChange = () => {
      setMode(getUorinMode());
    };

    // Listen for storage events (cross-tab) and custom mode change events
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('uorin-mode-change', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('uorin-mode-change', handleStorageChange);
    };
  }, []);

  // If user somehow ends up on 'tasks' tab in Normal mode, redirect to chat
  useEffect(() => {
    if (mode === 'normal' && activeTab === 'tasks') {
      setActiveTab('chat');
    }
  }, [mode, activeTab]);

  // Check for judgment profile on mount
  useEffect(() => {
    const checkProfile = async () => {
      try {
        // Check skip TTL
        const skipUntilStr = localStorage.getItem('uorin_onboarding_profile_skipped_until');
        if (skipUntilStr) {
          const skipUntil = new Date(skipUntilStr);
          if (new Date() < skipUntil) {
            // Skip period still active
            setProfileCheckComplete(true);
            return;
          } else {
            // Skip period expired, remove it
            localStorage.removeItem('uorin_onboarding_profile_skipped_until');
          }
        }

        // Check if profile exists
        const response = await getJudgmentProfile();
        if (!response.profile || Object.keys(response.profile).length === 0) {
          // No profile exists - show wizard
          setShowOnboardingWizard(true);
        }
      } catch (error) {
        console.error('Failed to check judgment profile:', error);
        // Don't show wizard on error - fail silently
      } finally {
        setProfileCheckComplete(true);
      }
    };

    checkProfile();
  }, []);

  const handleOnboardingComplete = () => {
    setShowOnboardingWizard(false);
  };

  const handleOnboardingSkip = () => {
    setShowOnboardingWizard(false);
  };

  const handleNavigateToChat = (prefillText: string) => {
    // Store prefill in sessionStorage for ChatScreen to pick up
    sessionStorage.setItem('uorin_chat_prefill', prefillText);
    setActiveTab('chat');
  };

  const renderScreen = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatScreen />;
      case 'worksheet':
        return <WorksheetScreen onNavigateToChat={handleNavigateToChat} />;
      case 'tasks':
        return <TasksScreen />;
      case 'workflows':
        return <WorkflowsScreen />;
      case 'profile':
        return <ProfileScreen />;
      case 'settings':
        return <SettingsScreen />;
      case 'audit':
        return <AuditLogScreen />;
      case 'integrations':
        return <IntegrationsScreen />;
      default:
        return <ChatScreen />;
    }
  };

  return (
    <>
      {/* Toast notifications */}
      <Toaster />

      {/* Onboarding Wizard Modal */}
      {showOnboardingWizard && profileCheckComplete && (
        <OnboardingWizard
          onComplete={handleOnboardingComplete}
          onSkip={handleOnboardingSkip}
        />
      )}

      <div className="h-dvh flex bg-gradient-to-br from-gray-50 via-blue-50/30 to-sky-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
        {/* Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          isMobileOpen={isMobileSidebarOpen}
          onMobileClose={() => setIsMobileSidebarOpen(false)}
          mode={mode}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Mobile Header */}
          <div className="lg:hidden flex items-center gap-4 p-4 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-border">
            <button
              onClick={() => setIsMobileSidebarOpen(true)}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h1 className="flex items-center gap-2">
              <span className="text-lg font-semibold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Uorin AI
              </span>
            </h1>
          </div>

          {/* Screen Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {renderScreen()}
          </div>
        </div>
      </div>
    </>
  );
}
