import React from 'react';
import { GlassCard } from './GlassCard';
import { Lock, Mail, MessageSquare, Calendar, FileText, Database } from 'lucide-react';

export function IntegrationsScreen() {
  const integrations = [
    {
      id: 'email',
      name: 'Email (Gmail, Outlook)',
      icon: Mail,
      description: 'Auto-draft responses, schedule sends, manage inbox',
      status: 'Coming Soon',
    },
    {
      id: 'slack',
      name: 'Slack',
      icon: MessageSquare,
      description: 'Integrate with team chat, auto-summarize threads',
      status: 'Coming Soon',
    },
    {
      id: 'calendar',
      name: 'Calendar',
      icon: Calendar,
      description: 'Meeting prep, scheduling assistance, agenda creation',
      status: 'Coming Soon',
    },
    {
      id: 'docs',
      name: 'Google Docs / Notion',
      icon: FileText,
      description: 'Document analysis, collaborative editing, templates',
      status: 'Coming Soon',
    },
    {
      id: 'crm',
      name: 'CRM (Salesforce, HubSpot)',
      icon: Database,
      description: 'Auto-log interactions, generate insights, update records',
      status: 'Coming Soon',
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-semibold">Integrations</h2>
          <p className="text-muted-foreground mt-1">
            Connect Uorin to your favorite tools and platforms
          </p>
        </div>

        {/* Coming Soon Banner */}
        <GlassCard className="p-6 border-2 border-dashed border-primary/30 bg-gradient-to-br from-primary/5 to-secondary/5">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-[16px] bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0">
              <Lock className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-lg mb-1">Integrations Coming Soon</h3>
              <p className="text-sm text-muted-foreground mb-4">
                We're working hard to bring powerful integrations to Uorin. These features will
                enable seamless workflow automation across your entire tech stack.
              </p>
              <div className="flex gap-2">
                <button className="px-4 py-2 bg-primary text-white rounded-[12px] hover:shadow-lg transition-all text-sm">
                  Join Waitlist
                </button>
                <button className="px-4 py-2 bg-accent text-accent-foreground rounded-[12px] hover:bg-accent/80 transition-all text-sm">
                  Request Integration
                </button>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Integrations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {integrations.map((integration) => {
            const Icon = integration.icon;
            return (
              <GlassCard key={integration.id} className="p-6 opacity-60">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-[16px] bg-accent flex items-center justify-center flex-shrink-0">
                    <Icon className="w-6 h-6 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold">{integration.name}</h4>
                      <span className="px-2 py-1 bg-muted text-muted-foreground rounded-full text-xs">
                        {integration.status}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{integration.description}</p>
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </div>

        {/* Feature Request */}
        <GlassCard className="p-6">
          <h3 className="font-semibold mb-4">Don't see what you need?</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Tell us which integrations would be most valuable for your workflow. We prioritize
            based on user feedback.
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Suggest an integration..."
              className="flex-1 px-4 py-2 bg-input-background border border-border rounded-[12px] focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button className="px-5 py-2 bg-primary text-white rounded-[12px] hover:shadow-lg transition-all">
              Submit
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
