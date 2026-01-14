import React, { useState } from 'react';
import { X, CheckCircle, AlertCircle } from 'lucide-react';
import { upsertJudgmentProfile } from '@/lib/quilloApi';
import { JUDGMENT_PROFILE_QUESTIONS } from './judgmentProfileQuestions';

interface OnboardingWizardProps {
  onComplete: () => void;
  onSkip: () => void;
}

export function OnboardingWizard({ onComplete, onSkip }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentQuestion = JUDGMENT_PROFILE_QUESTIONS[currentStep];
  const progress = ((currentStep + 1) / JUDGMENT_PROFILE_QUESTIONS.length) * 100;
  const isLastQuestion = currentStep === JUDGMENT_PROFILE_QUESTIONS.length - 1;
  const currentAnswer = answers[currentQuestion.id];

  const handleAnswer = (value: string) => {
    setAnswers({ ...answers, [currentQuestion.id]: value });
    setError(null);
  };

  const handleNext = () => {
    if (!currentAnswer) {
      setError('Please select an option to continue');
      return;
    }

    if (isLastQuestion) {
      handleSubmit();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    if (!currentAnswer) {
      setError('Please select an option to continue');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Build strict backend payload
      const profile: Record<string, any> = {};
      const constraintsParts: string[] = [];
      const localStorageData: Record<string, string> = {};
      const confirmedAt = new Date().toISOString();

      // Process answers
      JUDGMENT_PROFILE_QUESTIONS.forEach((question) => {
        const answer = answers[question.id];
        if (!answer) return;

        if (question.category === 'profile') {
          // Direct schema fields
          if (question.schemaField) {
            // Special handling for jurisdiction "Other"
            if (question.id === 'jurisdiction' && answer === 'Other') {
              localStorageData['jurisdiction_other'] = 'true';
              return; // Don't add to profile
            }

            profile[question.schemaField] = {
              value: answer,
              source: 'explicit',
              confirmed_at: confirmedAt
            };
          }
        } else if (question.category === 'constraints') {
          // Map to constraints field as free-form text
          const optionLabel = question.options.find(o => o.value === answer)?.label || answer;
          constraintsParts.push(`${question.text}: ${optionLabel}`);
        } else if (question.category === 'local') {
          // Store in localStorage only
          localStorageData[question.id] = answer;
        }
      });

      // Add constraints field if we have constraint answers
      if (constraintsParts.length > 0) {
        profile['constraints'] = {
          value: constraintsParts.join('; '),
          source: 'explicit',
          confirmed_at: confirmedAt
        };
      }

      // Save to backend
      await upsertJudgmentProfile({ profile });

      // Save local-only data to localStorage
      if (Object.keys(localStorageData).length > 0) {
        localStorage.setItem('uorin_starter_profile_local', JSON.stringify(localStorageData));
      }

      // Clear skip flag if it exists
      localStorage.removeItem('uorin_onboarding_profile_skipped_until');

      onComplete();
    } catch (err) {
      console.error('Failed to save judgment profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to save profile. Please try again.');
      setIsSubmitting(false);
    }
  };

  const handleSkipForNow = () => {
    // Set skip TTL to 7 days from now
    const skipUntil = new Date();
    skipUntil.setDate(skipUntil.getDate() + 7);
    localStorage.setItem('uorin_onboarding_profile_skipped_until', skipUntil.toISOString());
    onSkip();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Starter Judgment Profile
            </h2>
            <button
              onClick={onSkip}
              className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            </button>
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Help Uorin tailor analysis to your preferences. This is explicit, user-controlled storage.
            You can edit or delete this anytime. Takes about 2 minutes.
          </p>

          {/* Progress bar */}
          <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Question {currentStep + 1} of {JUDGMENT_PROFILE_QUESTIONS.length}
          </p>
        </div>

        {/* Question */}
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {currentQuestion.text}
          </h3>

          <div className="space-y-3">
            {currentQuestion.options.map((option) => (
              <button
                key={option.value}
                onClick={() => handleAnswer(option.value)}
                className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                  currentAnswer === option.value
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100'
                    : 'border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{option.label}</span>
                  {currentAnswer === option.value && (
                    <CheckCircle className="w-5 h-5 text-blue-500 flex-shrink-0" />
                  )}
                </div>
              </button>
            ))}
          </div>

          {error && (
            <div className="mt-4 flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-slate-700 flex items-center justify-between gap-4">
          <button
            onClick={handleSkipForNow}
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
            disabled={isSubmitting}
          >
            Remind me later
          </button>

          <div className="flex items-center gap-3">
            {currentStep > 0 && (
              <button
                onClick={handleBack}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                disabled={isSubmitting}
              >
                Back
              </button>
            )}

            <button
              onClick={handleNext}
              disabled={!currentAnswer || isSubmitting}
              className="px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSubmitting ? 'Saving...' : isLastQuestion ? 'Complete Setup' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
