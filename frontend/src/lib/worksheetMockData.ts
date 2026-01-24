/**
 * Worksheet Mock Data
 *
 * Simulated feed items for Worksheet v1.
 * Each item represents a prioritized message-like triage item.
 */

export type WorksheetItemType = 'opportunity' | 'action' | 'reply' | 'fyi' | 'noise';
export type WorksheetPriority = 'P0' | 'P1' | 'P2' | 'P3';
export type WorksheetAction = 'Reply' | 'Schedule' | 'Escalate' | 'Ignore' | 'Review' | 'Approve' | 'Delegate';

export interface WorksheetItem {
  id: string;
  fromName: string;
  fromDomain: string;
  channel: 'email' | 'linkedin' | 'slack' | 'calendar';
  type: WorksheetItemType;
  priority: WorksheetPriority;
  synopsis: string;
  rawPreview: string;
  ageMinutes: number;
  suggestedAction: WorksheetAction;
  altAction: WorksheetAction;
  whatItIs: string;
  whyMatters: string[];
  riskNotes: string[];
}

export const worksheetMockData: WorksheetItem[] = [
  {
    id: 'ws-001',
    fromName: 'Harshit Sharma',
    fromDomain: 'linkedin.com',
    channel: 'linkedin',
    type: 'opportunity',
    priority: 'P1',
    synopsis: 'Series A founder wants to collaborate on AI governance research',
    rawPreview: 'Hey! Saw your post on responsible AI. We just raised our Series A and are building...',
    ageMinutes: 45,
    suggestedAction: 'Reply',
    altAction: 'Schedule',
    whatItIs: 'Partnership inquiry from a well-funded AI startup founder interested in collaboration.',
    whyMatters: [
      'Founder has strong network in AI/ML space',
      'Series A funding indicates serious commitment',
      'Alignment with your stated AI governance interests'
    ],
    riskNotes: [
      'No due diligence on company yet',
      'Could be time-intensive commitment',
      'Verify company legitimacy before deep engagement'
    ]
  },
  {
    id: 'ws-002',
    fromName: 'Building Manager',
    fromDomain: 'email',
    channel: 'email',
    type: 'action',
    priority: 'P0',
    synopsis: 'Urgent: Water leak in unit 4B needs access authorization today',
    rawPreview: 'Dear Property Owner, we have identified a water leak affecting unit 4B. We need immediate...',
    ageMinutes: 120,
    suggestedAction: 'Approve',
    altAction: 'Escalate',
    whatItIs: 'Maintenance emergency requiring your authorization for building access.',
    whyMatters: [
      'Water damage spreads quickly if not addressed',
      'Tenant liability concerns if delayed',
      'Building manager needs written authorization'
    ],
    riskNotes: [
      'Verify sender is legitimate building management',
      'Document authorization for insurance purposes',
      'May incur repair costs - check coverage'
    ]
  },
  {
    id: 'ws-003',
    fromName: 'Sarah Chen',
    fromDomain: 'acme-corp.com',
    channel: 'email',
    type: 'reply',
    priority: 'P1',
    synopsis: 'Waiting on your feedback for Q2 budget proposal',
    rawPreview: 'Hi, just following up on the Q2 budget I sent last week. The finance team needs...',
    ageMinutes: 1440,
    suggestedAction: 'Reply',
    altAction: 'Delegate',
    whatItIs: 'Follow-up on budget review that is blocking finance team progress.',
    whyMatters: [
      'Finance team deadline approaching',
      'Your input specifically requested',
      'Delay could impact Q2 planning cycle'
    ],
    riskNotes: [
      'One day overdue - shows as delayed on their end',
      'May affect team perception of responsiveness',
      'Budget decisions have downstream implications'
    ]
  },
  {
    id: 'ws-004',
    fromName: 'TechCrunch Newsletter',
    fromDomain: 'techcrunch.com',
    channel: 'email',
    type: 'fyi',
    priority: 'P3',
    synopsis: 'Weekly AI roundup: New Claude capabilities announced',
    rawPreview: 'This week in AI: Anthropic announces new Claude features, OpenAI responds with...',
    ageMinutes: 180,
    suggestedAction: 'Ignore',
    altAction: 'Review',
    whatItIs: 'Industry newsletter with AI news relevant to your interests.',
    whyMatters: [
      'Staying current on AI landscape',
      'Competitor intelligence',
      'Potential conversation starters'
    ],
    riskNotes: []
  },
  {
    id: 'ws-005',
    fromName: 'Invoice Bot',
    fromDomain: 'quickbooks.com',
    channel: 'email',
    type: 'action',
    priority: 'P2',
    synopsis: 'Invoice #4521 due in 3 days - vendor payment pending',
    rawPreview: 'Reminder: Invoice #4521 from CloudServices Inc for $2,450.00 is due on...',
    ageMinutes: 4320,
    suggestedAction: 'Approve',
    altAction: 'Review',
    whatItIs: 'Routine vendor invoice requiring payment authorization.',
    whyMatters: [
      'Maintaining good vendor relationships',
      'Avoiding late payment fees',
      'Keeping services active'
    ],
    riskNotes: [
      'Verify invoice matches expected services',
      'Check against budget allocation',
      'Large one-time charge vs recurring'
    ]
  },
  {
    id: 'ws-006',
    fromName: 'Mike Johnson',
    fromDomain: 'linkedin.com',
    channel: 'linkedin',
    type: 'opportunity',
    priority: 'P2',
    synopsis: 'Speaking invitation at AI Ethics Summit in March',
    rawPreview: 'Hi! I am organizing the AI Ethics Summit and would love to have you as a speaker...',
    ageMinutes: 2880,
    suggestedAction: 'Schedule',
    altAction: 'Reply',
    whatItIs: 'Invitation to speak at industry conference on AI ethics.',
    whyMatters: [
      'Visibility in AI ethics community',
      'Networking with industry leaders',
      'Thought leadership positioning'
    ],
    riskNotes: [
      'Time commitment for preparation',
      'Check calendar for conflicts',
      'Verify event legitimacy and audience'
    ]
  },
  {
    id: 'ws-007',
    fromName: 'Unknown Sender',
    fromDomain: 'promo-deals.xyz',
    channel: 'email',
    type: 'noise',
    priority: 'P3',
    synopsis: 'Promotional spam about limited time offer',
    rawPreview: 'URGENT: Your exclusive offer expires in 24 hours! Click here to claim your...',
    ageMinutes: 60,
    suggestedAction: 'Ignore',
    altAction: 'Ignore',
    whatItIs: 'Promotional email with spam characteristics.',
    whyMatters: [
      'None - appears to be unsolicited marketing'
    ],
    riskNotes: [
      'Suspicious sender domain',
      'Classic spam patterns detected',
      'Do not click any links'
    ]
  },
  {
    id: 'ws-008',
    fromName: 'Calendar',
    fromDomain: 'google.com',
    channel: 'calendar',
    type: 'fyi',
    priority: 'P2',
    synopsis: 'Reminder: Team sync moved to 3pm tomorrow',
    rawPreview: 'Your event "Weekly Team Sync" has been rescheduled by Alex to 3:00 PM...',
    ageMinutes: 30,
    suggestedAction: 'Review',
    altAction: 'Ignore',
    whatItIs: 'Calendar update notification for recurring team meeting.',
    whyMatters: [
      'Avoid scheduling conflicts',
      'Team expects your attendance',
      'May affect other planned activities'
    ],
    riskNotes: []
  },
  {
    id: 'ws-009',
    fromName: 'Lisa Park',
    fromDomain: 'clientco.com',
    channel: 'email',
    type: 'reply',
    priority: 'P0',
    synopsis: 'Contract renewal decision needed by EOD',
    rawPreview: 'Hi, as discussed, we need your decision on the contract renewal by end of day...',
    ageMinutes: 240,
    suggestedAction: 'Reply',
    altAction: 'Escalate',
    whatItIs: 'Time-sensitive client request for contract renewal decision.',
    whyMatters: [
      'Client relationship at stake',
      'EOD deadline is firm',
      'Revenue implications for renewal'
    ],
    riskNotes: [
      'Review contract terms before committing',
      'Verify pricing against market rates',
      'Consider negotiation leverage before responding'
    ]
  },
  {
    id: 'ws-010',
    fromName: 'James Wilson',
    fromDomain: 'slack.com',
    channel: 'slack',
    type: 'action',
    priority: 'P1',
    synopsis: 'PR review requested: Critical security patch',
    rawPreview: '@you please review this PR when you get a chance - it is a security fix that...',
    ageMinutes: 90,
    suggestedAction: 'Review',
    altAction: 'Delegate',
    whatItIs: 'Code review request for security-related pull request.',
    whyMatters: [
      'Security patches should not be delayed',
      'Your expertise specifically needed',
      'Blocking deployment pipeline'
    ],
    riskNotes: [
      'Thorough review needed for security code',
      'May require additional testing',
      'Consider risk of rushing review'
    ]
  },
  {
    id: 'ws-011',
    fromName: 'HR Notifications',
    fromDomain: 'workday.com',
    channel: 'email',
    type: 'fyi',
    priority: 'P3',
    synopsis: 'New company policy update: Remote work guidelines',
    rawPreview: 'Please review the updated remote work policy effective March 1st. Key changes include...',
    ageMinutes: 10080,
    suggestedAction: 'Review',
    altAction: 'Ignore',
    whatItIs: 'Company policy update notification from HR system.',
    whyMatters: [
      'Affects your work arrangements',
      'Compliance expectations',
      'May require acknowledgment'
    ],
    riskNotes: []
  },
  {
    id: 'ws-012',
    fromName: 'David Kim',
    fromDomain: 'linkedin.com',
    channel: 'linkedin',
    type: 'opportunity',
    priority: 'P2',
    synopsis: 'Angel investment opportunity in EdTech startup',
    rawPreview: 'Hi! A friend mentioned you might be interested in angel investing. We are raising...',
    ageMinutes: 5760,
    suggestedAction: 'Reply',
    altAction: 'Schedule',
    whatItIs: 'Cold outreach for potential angel investment in education technology.',
    whyMatters: [
      'Potential investment opportunity',
      'EdTech sector showing growth',
      'Referred through mutual connection'
    ],
    riskNotes: [
      'Verify referral source',
      'Request pitch deck before meeting',
      'Early stage = high risk investment',
      'Due diligence required before any commitment'
    ]
  }
];

/**
 * Format age in minutes to human-readable string
 */
export function formatAge(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h`;
  return `${Math.floor(minutes / 1440)}d`;
}

/**
 * Get priority color classes
 */
export function getPriorityClasses(priority: WorksheetPriority): { bg: string; text: string } {
  switch (priority) {
    case 'P0':
      return { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400' };
    case 'P1':
      return { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400' };
    case 'P2':
      return { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-400' };
    case 'P3':
      return { bg: 'bg-gray-100 dark:bg-gray-900/30', text: 'text-gray-700 dark:text-gray-400' };
  }
}

/**
 * Get type color classes
 */
export function getTypeClasses(type: WorksheetItemType): { bg: string; text: string } {
  switch (type) {
    case 'opportunity':
      return { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400' };
    case 'action':
      return { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400' };
    case 'reply':
      return { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-400' };
    case 'fyi':
      return { bg: 'bg-slate-100 dark:bg-slate-900/30', text: 'text-slate-700 dark:text-slate-400' };
    case 'noise':
      return { bg: 'bg-gray-100 dark:bg-gray-900/30', text: 'text-gray-500 dark:text-gray-500' };
  }
}

/**
 * Get channel icon name (for lucide-react)
 */
export function getChannelIcon(channel: WorksheetItem['channel']): string {
  switch (channel) {
    case 'email': return 'Mail';
    case 'linkedin': return 'Linkedin';
    case 'slack': return 'MessageSquare';
    case 'calendar': return 'Calendar';
  }
}
