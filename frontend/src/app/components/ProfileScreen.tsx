import React, { useState } from 'react';
import { GlassCard } from './GlassCard';
import { Save, Download, AlertTriangle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function ProfileScreen() {
  const [profileContent, setProfileContent] = useState(`# User Profile

## Basic Information
- Name: John Doe
- Role: Product Manager
- Company: Tech Startup Inc.

## Preferences
- Writing Style: Professional yet approachable
- Response Length: Concise and actionable
- Primary Focus: Product strategy and team communication

## Context
I work on a fast-paced product team building B2B SaaS solutions. I value clarity, empathy, and data-driven decisions.

## Goals
- Improve team communication efficiency
- Reduce time spent on email composition
- Better conflict resolution strategies
`);

  const autoHighlights = `## Highlights (Auto-Generated)

Based on your recent interactions:
- **Communication Style**: You prefer structured, bullet-pointed responses
- **Key Topics**: Product strategy, team dynamics, customer feedback
- **Peak Activity**: Weekdays 9 AM - 6 PM EST
- **Preferred Tools**: Email, Slack, Notion

*Last updated: ${new Date().toLocaleDateString()}*`;

  const [activeView, setActiveView] = useState<'edit' | 'preview'>('edit');

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Memory & Profile</h2>
            <p className="text-muted-foreground mt-1">
              Customize how Quillo understands and assists you
            </p>
          </div>
          <div className="flex gap-2">
            <button className="px-5 py-2.5 bg-accent text-accent-foreground rounded-[16px] hover:bg-accent/80 transition-all flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export
            </button>
            <button className="px-5 py-2.5 bg-gradient-to-r from-primary to-secondary text-white rounded-[16px] hover:shadow-lg transition-all flex items-center gap-2">
              <Save className="w-4 h-4" />
              Save
            </button>
          </div>
        </div>

        {/* Editor */}
        <GlassCard className="overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-border bg-accent/30">
            <button
              onClick={() => setActiveView('edit')}
              className={`px-6 py-3 transition-colors ${
                activeView === 'edit'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Edit
            </button>
            <button
              onClick={() => setActiveView('preview')}
              className={`px-6 py-3 transition-colors ${
                activeView === 'preview'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Preview
            </button>
          </div>

          {/* Content */}
          <div className="grid grid-cols-1 lg:grid-cols-2 divide-x divide-border">
            {/* Editor / Preview */}
            <div className="p-6">
              {activeView === 'edit' ? (
                <textarea
                  value={profileContent}
                  onChange={(e) => setProfileContent(e.target.value)}
                  className="w-full h-[500px] bg-input-background border border-border rounded-[16px] p-4 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                  placeholder="Write your profile in Markdown..."
                />
              ) : (
                <div className="prose prose-sm max-w-none h-[500px] overflow-y-auto px-4">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {profileContent}
                  </ReactMarkdown>
                </div>
              )}
            </div>

            {/* Auto Highlights */}
            <div className="p-6">
              <div className="flex items-start gap-2 mb-4 p-3 bg-secondary/10 rounded-[12px]">
                <AlertTriangle className="w-5 h-5 text-secondary flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-secondary">Auto-generated content</p>
                  <p className="text-muted-foreground text-xs mt-1">
                    These highlights are automatically updated based on your interactions. Edit
                    with caution.
                  </p>
                </div>
              </div>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {autoHighlights}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <GlassCard className="p-4">
            <h4 className="font-medium mb-2">Profile Completeness</h4>
            <div className="w-full bg-accent rounded-full h-2 mb-2">
              <div className="bg-gradient-to-r from-primary to-secondary h-2 rounded-full w-3/4"></div>
            </div>
            <p className="text-xs text-muted-foreground">75% complete</p>
          </GlassCard>

          <GlassCard className="p-4">
            <h4 className="font-medium mb-2">Last Sync</h4>
            <p className="text-sm text-muted-foreground">2 hours ago</p>
            <p className="text-xs text-muted-foreground mt-1">All changes saved</p>
          </GlassCard>

          <GlassCard className="p-4">
            <button className="w-full px-4 py-2 bg-destructive/10 text-destructive rounded-[12px] hover:bg-destructive/20 transition-all font-medium">
              Redact Sensitive Data
            </button>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
