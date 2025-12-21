import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatScreen } from './components/ChatScreen';
import { WorkflowsScreen } from './components/WorkflowsScreen';
import { ProfileScreen } from './components/ProfileScreen';
import { SettingsScreen } from './components/SettingsScreen';
import { AuditLogScreen } from './components/AuditLogScreen';
import { IntegrationsScreen } from './components/IntegrationsScreen';
import { Menu } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const renderScreen = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatScreen />;
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
    <div className="h-screen flex bg-gradient-to-br from-gray-50 via-blue-50/30 to-sky-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isMobileOpen={isMobileSidebarOpen}
        onMobileClose={() => setIsMobileSidebarOpen(false)}
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
  );
}
