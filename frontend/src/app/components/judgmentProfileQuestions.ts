/**
 * Shared question definitions for Judgment Profile
 * Used by both OnboardingWizard and JudgmentProfileSettings
 */

export interface QuestionOption {
  value: string;
  label: string;
}

export interface Question {
  id: string;
  text: string;
  options: QuestionOption[];
  schemaField: string | null; // null means localStorage only
  category: 'profile' | 'constraints' | 'local';
}

export const JUDGMENT_PROFILE_QUESTIONS: Question[] = [
  {
    id: 'risk_posture',
    text: 'How do you approach risk in decision-making?',
    options: [
      { value: 'conservative', label: 'Conservative - Prefer lower-risk options, prioritize safety' },
      { value: 'moderate', label: 'Moderate - Balance risk and reward' },
      { value: 'aggressive', label: 'Aggressive - Accept higher risk for potentially higher reward' }
    ],
    schemaField: 'risk_posture',
    category: 'profile'
  },
  {
    id: 'relationship_sensitivity',
    text: 'How important is relationship harmony in your communications?',
    options: [
      { value: 'low', label: 'Low - Direct, task-focused communication' },
      { value: 'medium', label: 'Medium - Balance directness with relationship maintenance' },
      { value: 'high', label: 'High - Prioritize relationship harmony in all interactions' }
    ],
    schemaField: 'relationship_sensitivity',
    category: 'profile'
  },
  {
    id: 'decision_authority',
    text: 'What level of decision authority should the system have?',
    options: [
      { value: 'none', label: 'None - I make all decisions, system provides analysis only' },
      { value: 'limited', label: 'Limited - System can make low-stakes suggestions' },
      { value: 'full', label: 'Full - System can recommend action plans for my approval' }
    ],
    schemaField: 'decision_authority',
    category: 'profile'
  },
  {
    id: 'default_tone',
    text: 'What communication tone do you prefer?',
    options: [
      { value: 'formal', label: 'Formal - Professional, structured communication' },
      { value: 'neutral', label: 'Neutral - Clear and direct without formality' },
      { value: 'casual', label: 'Casual - Conversational, friendly tone' }
    ],
    schemaField: 'default_tone',
    category: 'profile'
  },
  {
    id: 'jurisdiction',
    text: 'What is your primary jurisdiction or locale?',
    options: [
      { value: 'UK', label: 'United Kingdom' },
      { value: 'US', label: 'United States' },
      { value: 'EU', label: 'European Union' },
      { value: 'Other', label: 'Other (stored locally)' }
    ],
    schemaField: 'jurisdiction',
    category: 'profile'
  },
  {
    id: 'speed_vs_certainty',
    text: 'How do you balance speed and certainty?',
    options: [
      { value: 'move_fast', label: 'Move fast - Prefer quick decisions even with some uncertainty' },
      { value: 'balanced', label: 'Balanced - Balance speed with confidence' },
      { value: 'prefer_certainty', label: 'Prefer certainty - Take time to ensure I\'m confident' }
    ],
    schemaField: 'constraints',
    category: 'constraints'
  },
  {
    id: 'irreversible_risk',
    text: 'How do you handle irreversible actions?',
    options: [
      { value: 'avoid_irreversible', label: 'Avoid irreversible - Very cautious with irreversible changes' },
      { value: 'case_by_case', label: 'Case-by-case - Evaluate based on context' },
      { value: 'comfortable_if_justified', label: 'Comfortable if justified - Fine with irreversible if reasoning is solid' }
    ],
    schemaField: 'constraints',
    category: 'constraints'
  },
  {
    id: 'communication_style',
    text: 'What communication style resonates with you?',
    options: [
      { value: 'blunt_efficient', label: 'Blunt & efficient - Get to the point quickly' },
      { value: 'warm_clear', label: 'Warm & clear - Friendly but straightforward' },
      { value: 'diplomatic_careful', label: 'Diplomatic & careful - Thoughtful and considerate phrasing' }
    ],
    schemaField: 'constraints',
    category: 'constraints'
  },
  {
    id: 'evidence_strictness',
    text: 'When do you want sources and evidence cited?',
    options: [
      { value: 'always_want_sources', label: 'Always want sources - Always cite sources when facts are involved' },
      { value: 'only_when_ask', label: 'Only when I ask - Provide sources only when I specifically request them' },
      { value: 'only_big_decisions', label: 'Only for big decisions - Cite sources for high-stakes decisions only' }
    ],
    schemaField: 'constraints',
    category: 'constraints'
  },
  {
    id: 'default_mode',
    text: 'What should be your default interaction mode?',
    options: [
      { value: 'normal_chat', label: 'Normal chat - Standard conversational mode by default' },
      { value: 'work_mode', label: 'Work mode - Trust signals + stress test behaviors by default' },
      { value: 'ask_each_time', label: 'Ask each time - Prompt me to choose mode each session' }
    ],
    schemaField: null, // Not in schema yet - localStorage only
    category: 'local'
  }
];

/**
 * Get user-friendly label for a schema field value
 */
export function getFieldLabel(fieldId: string, value: string): string {
  const question = JUDGMENT_PROFILE_QUESTIONS.find(q => q.id === fieldId);
  if (!question) return value;

  const option = question.options.find(o => o.value === value);
  return option ? option.label : value;
}

/**
 * Format constraints field into readable sections
 */
export function formatConstraints(constraintsValue: string): Array<{ question: string; answer: string }> {
  const parts = constraintsValue.split('; ').filter(Boolean);
  return parts.map(part => {
    const [question, answer] = part.split(': ');
    return { question: question || '', answer: answer || '' };
  });
}
