import React from 'react';
import { MessageSquare, Workflow, User, Settings, Activity, Lock, Menu, CheckSquare } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  isMobileOpen: boolean;
  onMobileClose: () => void;
}

const menuItems = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'tasks', label: 'Tasks', icon: CheckSquare },
  { id: 'workflows', label: 'Workflows', icon: Workflow },
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'audit', label: 'Audit Log', icon: Activity },
  { id: 'integrations', label: 'Integrations', icon: Lock, locked: true },
];

export function Sidebar({ activeTab, onTabChange, isMobileOpen, onMobileClose }: SidebarProps) {
  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onMobileClose}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-72 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl
          border-r border-border
          transform transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full p-6">
          {/* Logo */}
          <div className="mb-8">
            <h1 className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-[16px] bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <span className="text-white text-xl">Q</span>
              </div>
              <span className="text-xl font-semibold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Uorin AI
              </span>
            </h1>
            <p className="text-xs text-muted-foreground mt-1 ml-12">AI Chief of Staff</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    if (!item.locked) {
                      onTabChange(item.id);
                      onMobileClose();
                    }
                  }}
                  disabled={item.locked}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-[16px]
                    transition-all duration-200
                    ${isActive 
                      ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/30' 
                      : item.locked
                      ? 'text-muted-foreground cursor-not-allowed opacity-50'
                      : 'text-foreground hover:bg-accent'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                  {item.locked && (
                    <Lock className="w-4 h-4 ml-auto" />
                  )}
                </button>
              );
            })}
          </nav>

          {/* User Profile */}
          <div className="mt-auto pt-6 border-t border-border">
            <div className="flex items-center gap-3 px-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <span className="text-white text-sm">JD</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">John Doe</p>
                <p className="text-xs text-muted-foreground truncate">john@example.com</p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
