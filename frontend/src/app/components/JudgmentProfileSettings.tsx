import React, { useState, useEffect } from 'react';
import { GlassCard } from './GlassCard';
import { Edit2, Trash2, Save, X, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { getJudgmentProfile, upsertJudgmentProfile, JudgmentProfileResponse } from '@/lib/quilloApi';
import { JUDGMENT_PROFILE_QUESTIONS, getFieldLabel, formatConstraints } from './judgmentProfileQuestions';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from './ui/alert-dialog';

type Mode = 'view' | 'edit';

export function JudgmentProfileSettings() {
  const [mode, setMode] = useState<Mode>('view');
  const [profile, setProfile] = useState<JudgmentProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editedAnswers, setEditedAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getJudgmentProfile();
      setProfile(response);
    } catch (err) {
      console.error('Failed to load judgment profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    if (!profile?.profile) return;

    // Pre-fill answers from existing profile
    const answers: Record<string, string> = {};

    // Extract answers from profile and localStorage
    JUDGMENT_PROFILE_QUESTIONS.forEach(question => {
      if (question.category === 'profile' && question.schemaField && profile.profile[question.schemaField]) {
        answers[question.id] = profile.profile[question.schemaField].value;
      } else if (question.category === 'constraints') {
        // Extract from constraints field
        const constraintsValue = profile.profile['constraints']?.value || '';
        const constraintsParsed = formatConstraints(constraintsValue);
        const matchingConstraint = constraintsParsed.find(c => c.question === question.text);
        if (matchingConstraint) {
          const option = question.options.find(o => matchingConstraint.answer.includes(o.label));
          if (option) {
            answers[question.id] = option.value;
          }
        }
      } else if (question.category === 'local') {
        // Load from localStorage
        const localData = localStorage.getItem('uorin_starter_profile_local');
        if (localData) {
          try {
            const parsed = JSON.parse(localData);
            if (parsed[question.id]) {
              answers[question.id] = parsed[question.id];
            }
          } catch {}
        }
      }
    });

    setEditedAnswers(answers);
    setMode('edit');
  };

  const handleCancelEdit = () => {
    setEditedAnswers({});
    setError(null);
    setMode('view');
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);

    try {
      // Build strict backend payload (same logic as OnboardingWizard)
      const profilePayload: Record<string, any> = {};
      const constraintsParts: string[] = [];
      const localStorageData: Record<string, string> = {};
      const confirmedAt = new Date().toISOString();

      // Process answers
      JUDGMENT_PROFILE_QUESTIONS.forEach((question) => {
        const answer = editedAnswers[question.id];
        if (!answer) return;

        if (question.category === 'profile') {
          if (question.schemaField) {
            // Special handling for jurisdiction "Other"
            if (question.id === 'jurisdiction' && answer === 'Other') {
              localStorageData['jurisdiction_other'] = 'true';
              return;
            }

            profilePayload[question.schemaField] = {
              value: answer,
              source: 'explicit',
              confirmed_at: confirmedAt
            };
          }
        } else if (question.category === 'constraints') {
          const optionLabel = question.options.find(o => o.value === answer)?.label || answer;
          constraintsParts.push(`${question.text}: ${optionLabel}`);
        } else if (question.category === 'local') {
          localStorageData[question.id] = answer;
        }
      });

      // Add constraints field if we have constraint answers
      if (constraintsParts.length > 0) {
        profilePayload['constraints'] = {
          value: constraintsParts.join('; '),
          source: 'explicit',
          confirmed_at: confirmedAt
        };
      }

      // Save to backend
      const response = await upsertJudgmentProfile({ profile: profilePayload });

      // Save local-only data to localStorage
      if (Object.keys(localStorageData).length > 0) {
        localStorage.setItem('uorin_starter_profile_local', JSON.stringify(localStorageData));
      }

      // Update local state
      setProfile(response);
      setMode('view');
      setEditedAnswers({});

      toast.success('Judgment Profile updated. You remain in full control.');
    } catch (err) {
      console.error('Failed to save judgment profile:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to save profile. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);

    try {
      const response = await fetch('/ui/api/profile/judgment?user_key=global', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-UI-Token': import.meta.env.VITE_UI_TOKEN || '',
        },
      });

      if (!response.ok) {
        throw new Error(`Delete failed: ${response.status}`);
      }

      // Clear local state
      setProfile({ version: 'judgment_profile_v1', profile: null, updated_at: null });
      setMode('view');

      // Clear localStorage
      localStorage.removeItem('uorin_starter_profile_local');
      localStorage.removeItem('uorin_onboarding_profile_skipped_until');

      toast.success('Judgment Profile deleted.');
    } catch (err) {
      console.error('Failed to delete judgment profile:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete profile';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <GlassCard className="p-6">
        <h3 className="font-semibold text-lg mb-4">Judgment Profile</h3>
        <p className="text-sm text-muted-foreground">Loading...</p>
      </GlassCard>
    );
  }

  const hasProfile = profile?.profile && Object.keys(profile.profile).length > 0;

  // Empty state
  if (!hasProfile && mode === 'view') {
    return (
      <GlassCard className="p-6">
        <h3 className="font-semibold text-lg mb-4">Judgment Profile</h3>
        <div className="text-center py-8">
          <div className="w-16 h-16 rounded-full bg-accent mx-auto mb-4 flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-muted-foreground" />
          </div>
          <h4 className="font-medium text-lg mb-2">No profile saved</h4>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            You haven't created a Judgment Profile yet. Complete the onboarding wizard to help Uorin tailor analysis to your preferences.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Edit mode
  if (mode === 'edit') {
    return (
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg">Edit Judgment Profile</h3>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCancelEdit}
              disabled={saving}
              className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>

        <div className="space-y-6">
          {JUDGMENT_PROFILE_QUESTIONS.map((question, index) => (
            <div key={question.id} className="space-y-3">
              <h4 className="text-sm font-medium">
                {index + 1}. {question.text}
              </h4>
              <div className="space-y-2">
                {question.options.map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                      editedAnswers[question.id] === option.value
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-border hover:border-muted-foreground/30'
                    }`}
                  >
                    <input
                      type="radio"
                      name={question.id}
                      value={option.value}
                      checked={editedAnswers[question.id] === option.value}
                      onChange={(e) => setEditedAnswers({ ...editedAnswers, [question.id]: e.target.value })}
                      className="mt-0.5"
                    />
                    <span className="text-sm">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}
      </GlassCard>
    );
  }

  // Read-only view
  return (
    <GlassCard className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-lg">Judgment Profile</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={handleEdit}
            className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2"
          >
            <Edit2 className="w-4 h-4" />
            Edit
          </button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <button
                disabled={deleting}
                className="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Judgment Profile</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete your Judgment Profile. Uorin will no longer use any saved preferences.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  {deleting ? 'Deleting...' : 'Delete Profile'}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      <div className="space-y-4">
        {/* Trust note */}
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            These preferences are used only when explicitly relevant. Nothing is inferred.
          </p>
        </div>

        {/* Profile fields */}
        <div className="space-y-3">
          {profile?.profile && Object.entries(profile.profile).map(([key, field]: [string, any]) => {
            if (key === 'constraints') {
              const constraints = formatConstraints(field.value);
              return (
                <div key={key} className="p-4 bg-accent/50 rounded-lg">
                  <h4 className="text-sm font-medium mb-2">Preferences</h4>
                  <ul className="space-y-1.5">
                    {constraints.map((constraint, idx) => (
                      <li key={idx} className="text-sm text-muted-foreground">
                        <span className="font-medium text-foreground">{constraint.question}:</span> {constraint.answer}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            }

            const question = JUDGMENT_PROFILE_QUESTIONS.find(q => q.schemaField === key);
            return (
              <div key={key} className="p-4 bg-accent/50 rounded-lg">
                <h4 className="text-sm font-medium mb-1">{question?.text || key}</h4>
                <p className="text-sm text-muted-foreground">{getFieldLabel(question?.id || key, field.value)}</p>
              </div>
            );
          })}

          {/* Show local-only data if exists */}
          {(() => {
            const localData = localStorage.getItem('uorin_starter_profile_local');
            if (localData) {
              try {
                const parsed = JSON.parse(localData);
                const localQuestion = JUDGMENT_PROFILE_QUESTIONS.find(q => q.category === 'local');
                if (localQuestion && parsed[localQuestion.id]) {
                  return (
                    <div key="local-data" className="p-4 bg-accent/50 rounded-lg">
                      <h4 className="text-sm font-medium mb-1">{localQuestion.text}</h4>
                      <p className="text-sm text-muted-foreground">
                        {getFieldLabel(localQuestion.id, parsed[localQuestion.id])}
                      </p>
                    </div>
                  );
                }
              } catch {}
            }
            return null;
          })()}
        </div>

        {/* Last updated */}
        {profile?.updated_at && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground pt-3 border-t border-border">
            <Clock className="w-3.5 h-3.5" />
            <span>Last updated: {new Date(profile.updated_at).toLocaleString()}</span>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}
    </GlassCard>
  );
}
