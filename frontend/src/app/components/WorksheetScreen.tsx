import React, { useState, useEffect } from 'react';
import {
  Mail,
  Linkedin,
  MessageSquare,
  Calendar,
  X,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  ExternalLink,
  FileEdit,
  CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { getUorinMode, type UorinMode } from '@/lib/uorinMode';
import {
  worksheetMockData,
  formatAge,
  getPriorityClasses,
  getTypeClasses,
  type WorksheetItem,
  type WorksheetItemType
} from '@/lib/worksheetMockData';

type FilterType = 'all' | 'priority' | 'opportunity' | 'action' | 'reply' | 'fyi';

const filterMap: Record<FilterType, (item: WorksheetItem) => boolean> = {
  all: () => true,
  priority: (item) => item.priority === 'P0' || item.priority === 'P1',
  opportunity: (item) => item.type === 'opportunity',
  action: (item) => item.type === 'action',
  reply: (item) => item.type === 'reply',
  fyi: (item) => item.type === 'fyi'
};

function getChannelIconComponent(channel: WorksheetItem['channel']) {
  switch (channel) {
    case 'email':
      return Mail;
    case 'linkedin':
      return Linkedin;
    case 'slack':
      return MessageSquare;
    case 'calendar':
      return Calendar;
  }
}

function formatTypeName(type: WorksheetItemType): string {
  switch (type) {
    case 'opportunity':
      return 'Opportunity';
    case 'action':
      return 'Action';
    case 'reply':
      return 'Reply';
    case 'fyi':
      return 'FYI';
    case 'noise':
      return 'Noise';
  }
}

interface WorksheetScreenProps {
  onNavigateToChat?: (prefillText: string) => void;
}

export function WorksheetScreen({ onNavigateToChat }: WorksheetScreenProps) {
  const [mode, setMode] = useState<UorinMode>(getUorinMode);
  const [filter, setFilter] = useState<FilterType>('all');
  const [selectedItem, setSelectedItem] = useState<WorksheetItem | null>(null);
  const [hiddenItems, setHiddenItems] = useState<Set<string>>(new Set());
  const [riskExpanded, setRiskExpanded] = useState(false);

  // Sync mode with localStorage changes
  useEffect(() => {
    const handleModeChange = () => {
      setMode(getUorinMode());
    };
    window.addEventListener('storage', handleModeChange);
    window.addEventListener('uorin-mode-change', handleModeChange);
    return () => {
      window.removeEventListener('storage', handleModeChange);
      window.removeEventListener('uorin-mode-change', handleModeChange);
    };
  }, []);

  const filteredItems = worksheetMockData
    .filter((item) => !hiddenItems.has(item.id))
    .filter(filterMap[filter])
    .sort((a, b) => {
      // Sort by priority first (P0 > P1 > P2 > P3)
      const priorityOrder = { P0: 0, P1: 1, P2: 2, P3: 3 };
      const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
      if (priorityDiff !== 0) return priorityDiff;
      // Then by age (newer first)
      return a.ageMinutes - b.ageMinutes;
    });

  const handleMarkDone = (item: WorksheetItem) => {
    setHiddenItems((prev) => new Set(prev).add(item.id));
    setSelectedItem(null);
    toast.success('Moved to done.', {
      action: {
        label: 'Undo',
        onClick: () => {
          setHiddenItems((prev) => {
            const next = new Set(prev);
            next.delete(item.id);
            return next;
          });
        }
      }
    });
  };

  const handleOpenInChat = (item: WorksheetItem) => {
    const prefill = `Context: ${item.whatItIs}\n\nFrom: ${item.fromName} (${item.fromDomain})\nType: ${formatTypeName(item.type)}\nPriority: ${item.priority}\n\nSynopsis: ${item.synopsis}`;
    if (onNavigateToChat) {
      onNavigateToChat(prefill);
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(prefill);
      toast.success('Context copied to clipboard. Go to Chat to continue.');
    }
    setSelectedItem(null);
  };

  const handleDraftReply = (item: WorksheetItem) => {
    const prefill = `Draft a reply for this message:\n\nFrom: ${item.fromName} (${item.fromDomain})\nOriginal: "${item.rawPreview}"\n\nContext: ${item.whatItIs}\n\nSuggested approach: ${item.suggestedAction}`;
    if (onNavigateToChat) {
      onNavigateToChat(prefill);
    } else {
      navigator.clipboard.writeText(prefill);
      toast.success('Draft context copied. Go to Chat to draft your reply.');
    }
    setSelectedItem(null);
  };

  const filters: { key: FilterType; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'priority', label: 'Priority' },
    { key: 'opportunity', label: 'Opportunities' },
    { key: 'action', label: 'Action' },
    { key: 'reply', label: 'Reply' },
    { key: 'fyi', label: 'FYI' }
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative">
      {/* Header */}
      <div className="flex-none border-b border-border bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
        <div className="px-4 sm:px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold">Worksheet</h1>
              <p className="text-xs sm:text-sm text-muted-foreground mt-1">
                Triage what matters. Decide fast.
              </p>
            </div>
          </div>

          {/* Filter Chips */}
          <div className="flex flex-wrap gap-2 mt-4">
            {filters.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`
                  px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                  ${filter === f.key
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-accent text-foreground hover:bg-accent/80'
                  }
                `}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {filteredItems.length === 0 ? (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 rounded-full bg-accent flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">All caught up</h3>
              <p className="text-sm text-muted-foreground">
                {filter === 'all'
                  ? 'No items to triage right now.'
                  : `No ${filter} items to show.`}
              </p>
            </div>
          </div>
        ) : (
          <div className="p-4 sm:p-6 space-y-2">
            {filteredItems.map((item) => {
              const ChannelIcon = getChannelIconComponent(item.channel);
              const priorityClasses = getPriorityClasses(item.priority);
              const typeClasses = getTypeClasses(item.type);

              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setSelectedItem(item);
                    setRiskExpanded(false);
                  }}
                  className={`
                    w-full text-left bg-white dark:bg-slate-900 border border-border rounded-[16px] p-3 sm:p-4
                    hover:shadow-md hover:border-primary/30 transition-all
                    min-h-[56px] active:scale-[0.99]
                  `}
                >
                  <div className="flex items-start gap-3">
                    {/* Priority Badge */}
                    <div
                      className={`flex-none px-2 py-0.5 rounded text-xs font-bold ${priorityClasses.bg} ${priorityClasses.text}`}
                    >
                      {item.priority}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      {/* From + Channel */}
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                        <ChannelIcon className="w-3.5 h-3.5 flex-none" />
                        <span className="truncate">
                          {item.fromName}
                          <span className="text-muted-foreground/60"> ({item.fromDomain})</span>
                        </span>
                      </div>

                      {/* Synopsis */}
                      <p className="text-sm font-medium text-foreground line-clamp-2 leading-snug">
                        {item.synopsis}
                      </p>
                    </div>

                    {/* Right side: Type + Age */}
                    <div className="flex-none flex flex-col items-end gap-1.5">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeClasses.bg} ${typeClasses.text}`}
                      >
                        {formatTypeName(item.type)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatAge(item.ageMinutes)}
                      </span>
                    </div>
                  </div>

                  {/* Next Step Chip */}
                  <div className="flex items-center gap-2 mt-2 pt-2 border-t border-border/50">
                    <span className="text-xs text-muted-foreground">Next:</span>
                    <span className="px-2 py-0.5 rounded bg-primary/10 text-primary text-xs font-medium">
                      {item.suggestedAction}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Detail Sheet/Drawer */}
      {selectedItem && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
            onClick={() => setSelectedItem(null)}
          />

          {/* Sheet - Bottom on mobile, Right drawer on desktop */}
          <div
            className={`
              fixed z-50 bg-white dark:bg-slate-900 border-border
              transition-transform duration-300 ease-out

              /* Mobile: bottom sheet */
              inset-x-0 bottom-0 rounded-t-[20px] border-t max-h-[85vh]

              /* Desktop: right drawer */
              lg:inset-y-0 lg:right-0 lg:left-auto lg:w-[420px] lg:max-w-full lg:max-h-full
              lg:rounded-t-none lg:rounded-l-[20px] lg:border-t-0 lg:border-l
            `}
          >
            <div className="flex flex-col h-full max-h-[85vh] lg:max-h-full">
              {/* Sheet Header */}
              <div className="flex-none flex items-center justify-between px-4 sm:px-6 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-bold ${getPriorityClasses(selectedItem.priority).bg} ${getPriorityClasses(selectedItem.priority).text}`}
                  >
                    {selectedItem.priority}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${getTypeClasses(selectedItem.type).bg} ${getTypeClasses(selectedItem.type).text}`}
                  >
                    {formatTypeName(selectedItem.type)}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="p-2 hover:bg-accent rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Sheet Content */}
              <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-4">
                {/* From */}
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  {React.createElement(getChannelIconComponent(selectedItem.channel), {
                    className: 'w-4 h-4'
                  })}
                  <span>
                    {selectedItem.fromName}{' '}
                    <span className="text-muted-foreground/60">({selectedItem.fromDomain})</span>
                  </span>
                  <span className="ml-auto">{formatAge(selectedItem.ageMinutes)}</span>
                </div>

                {/* What it is */}
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                    What it is
                  </h3>
                  <p className="text-sm text-foreground leading-relaxed">{selectedItem.whatItIs}</p>
                </div>

                {/* Why it matters */}
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                    Why it matters
                  </h3>
                  <ul className="space-y-1">
                    {selectedItem.whyMatters.map((point, idx) => (
                      <li key={idx} className="text-sm text-foreground flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span className="leading-relaxed">{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Suggested Actions */}
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                    Suggested next action
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-sm font-medium">
                      {selectedItem.suggestedAction}
                    </span>
                    {selectedItem.altAction !== selectedItem.suggestedAction && (
                      <span className="px-3 py-1.5 rounded-lg bg-accent text-foreground text-sm">
                        or {selectedItem.altAction}
                      </span>
                    )}
                  </div>
                </div>

                {/* Risk/Consequence Block - Work Mode Only */}
                {mode === 'work' && selectedItem.riskNotes.length > 0 && (
                  <div className="border border-amber-200 dark:border-amber-800 rounded-[12px] bg-amber-50 dark:bg-amber-900/20">
                    <button
                      onClick={() => setRiskExpanded(!riskExpanded)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left"
                    >
                      <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-none" />
                      <span className="text-xs font-semibold text-amber-700 dark:text-amber-400 uppercase tracking-wide">
                        Risk / Consequence
                      </span>
                      {riskExpanded ? (
                        <ChevronDown className="w-4 h-4 text-amber-600 dark:text-amber-400 ml-auto" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-amber-600 dark:text-amber-400 ml-auto" />
                      )}
                    </button>
                    {riskExpanded && (
                      <ul className="px-3 pb-3 space-y-1">
                        {selectedItem.riskNotes.map((note, idx) => (
                          <li
                            key={idx}
                            className="text-sm text-amber-800 dark:text-amber-300 flex items-start gap-2"
                          >
                            <span className="mt-1">•</span>
                            <span className="leading-relaxed">{note}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Raw Preview (collapsed) */}
                <div className="text-xs text-muted-foreground bg-accent/50 rounded-lg p-3">
                  <span className="font-medium">Preview: </span>
                  <span className="italic">"{selectedItem.rawPreview}"</span>
                </div>
              </div>

              {/* Sheet Actions */}
              <div className="flex-none border-t border-border px-4 sm:px-6 py-4 space-y-2 pb-safe">
                <div className="flex gap-2">
                  <button
                    onClick={() => handleOpenInChat(selectedItem)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-[12px] font-medium text-sm hover:bg-primary/90 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Open in Chat
                  </button>
                  <button
                    onClick={() => handleDraftReply(selectedItem)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-accent text-foreground rounded-[12px] font-medium text-sm hover:bg-accent/80 transition-colors"
                  >
                    <FileEdit className="w-4 h-4" />
                    Draft reply
                  </button>
                </div>
                <button
                  onClick={() => handleMarkDone(selectedItem)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-border text-foreground rounded-[12px] font-medium text-sm hover:bg-accent transition-colors"
                >
                  <CheckCircle className="w-4 h-4" />
                  Mark done
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
