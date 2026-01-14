# Judgment Profile Settings v1

**Status:** ✅ Implemented
**Date:** 2026-01-14
**Version:** 1.0.0
**Rollback Tag:** `rollback-pre-judgment-profile-settings-v1-2026-01-14`

---

## Purpose

Judgment Profile Settings v1 provides a **user-controlled interface** for viewing, editing, and deleting Judgment Profiles. This is a **frontend-only** implementation that preserves trust, explicit control, and zero inference.

### Key Principles

- **Fully optional** - User-initiated only, no nudging or popups
- **Explicit control** - All changes require explicit user action and confirmation
- **Zero inference** - System never infers or auto-updates preferences
- **Trust-preserving** - Clear messaging about what data is stored and how it's used
- **Safe deletion** - Strong confirmation required with clear consequences

---

## What It Does

1. **Settings Entry Point**: Adds "Judgment Profile" section to Settings screen
2. **Read-Only View**: Displays current profile fields with clear labels
3. **Edit Mode**: Allows editing all fields with same questions as onboarding wizard
4. **Delete Functionality**: Allows permanent profile deletion with confirmation
5. **Toast Notifications**: Shows success/error feedback for all actions
6. **Transparency Alignment**: Profile changes reflected in Self-Explanation v1 transparency card

---

## What It Does NOT Do

This implementation explicitly **does NOT**:

1. **Auto-create profiles** - Never creates or modifies without explicit user action
2. **Infer preferences** - Never fills in missing fields automatically
3. **Nudge users** - No popups, no "we noticed", no recommendations
4. **Change backend** - Uses existing Judgment Profile v1 endpoints as-is
5. **Change orchestration** - Storage-only, does NOT affect LLM behavior
6. **Break existing functionality** - Zero breaking changes

---

## User Experience Flows

### View Existing Profile

1. User opens Settings
2. Scrolls to "Judgment Profile" section
3. Sees read-only view with:
   - Trust note: "These preferences are used only when explicitly relevant. Nothing is inferred."
   - All profile fields with human-readable labels
   - Last updated timestamp
   - Edit and Delete buttons

### Edit Profile

1. User clicks "Edit" button
2. Edit mode opens showing:
   - All 10 questions from onboarding wizard
   - Pre-filled with current answers
   - Save and Cancel buttons
3. User modifies answers
4. User clicks "Save Changes"
5. Backend saves via `POST /ui/api/profile/judgment`
6. Success toast shows: "Judgment Profile updated. You remain in full control."
7. Returns to read-only view with updated values

### Cancel Edit

1. User clicks "Edit" button
2. Modifies some answers
3. User clicks "Cancel"
4. No changes saved
5. Returns to read-only view with original values

### Delete Profile

1. User clicks "Delete" button
2. Confirmation dialog appears with exact copy:
   - Title: "Delete Judgment Profile"
   - Message: "This will permanently delete your Judgment Profile. Uorin will no longer use any saved preferences."
   - Cancel and Delete buttons
3. User confirms deletion
4. Backend deletes via `DELETE /ui/api/profile/judgment`
5. localStorage cleared (local-only fields)
6. Success toast shows: "Judgment Profile deleted."
7. Returns to empty state: "No profile saved"

### No Profile State

1. User opens Settings (no profile exists)
2. Sees empty state with:
   - Icon (AlertCircle)
   - Message: "No profile saved"
   - Guidance: "You haven't created a Judgment Profile yet. Complete the onboarding wizard to help Uorin tailor analysis to your preferences."

---

## Implementation Details

### Files Changed

**Frontend Components:**
1. `frontend/src/app/components/JudgmentProfileSettings.tsx` - New settings component
2. `frontend/src/app/components/judgmentProfileQuestions.ts` - Shared question definitions
3. `frontend/src/app/components/OnboardingWizard.tsx` - Updated to use shared questions
4. `frontend/src/app/components/SettingsScreen.tsx` - Added Judgment Profile section
5. `frontend/src/app/App.tsx` - Added Toaster component for toast notifications

**Backend:**
- No changes (uses existing endpoints)

### API Endpoints Used

**GET /ui/api/profile/judgment**
- Used on component mount
- Loads existing profile for display
- Returns null if no profile exists

**POST /ui/api/profile/judgment**
- Used when saving edits
- Validates strict schema (source="explicit", confirmed_at required)
- Upserts profile data

**DELETE /ui/api/profile/judgment**
- Used when deleting profile
- Removes profile from database
- Returns success even if no profile existed

### Question Reuse

All 10 questions from onboarding wizard are reused:
- Extracted to shared file `judgmentProfileQuestions.ts`
- Both OnboardingWizard and JudgmentProfileSettings import from shared file
- Ensures consistency between onboarding and editing

### Payload Building

Same strict payload logic as onboarding:
- Q1-Q5 → Direct schema fields (risk_posture, relationship_sensitivity, decision_authority, default_tone, jurisdiction)
- Q6-Q9 → Concatenated into constraints field
- Q10 → localStorage only (default_mode not in schema yet)
- All fields: `source="explicit"`, `confirmed_at=<ISO timestamp>`

### Toast Notifications

**Success:**
- "Judgment Profile updated. You remain in full control." (on save)
- "Judgment Profile deleted." (on delete)

**Error:**
- Shows backend validation errors (e.g., "Unknown keys not allowed...")
- Generic fallback: "Failed to save profile. Please try again."

---

## Trust & Messaging

All user-facing text adheres to trust principles:

**Trust Note (Read-Only View):**
> "These preferences are used only when explicitly relevant. Nothing is inferred."

**Success Toast (Save):**
> "Judgment Profile updated. You remain in full control."

**Delete Confirmation:**
> "This will permanently delete your Judgment Profile. Uorin will no longer use any saved preferences."

**Success Toast (Delete):**
> "Judgment Profile deleted."

**Empty State:**
> "You haven't created a Judgment Profile yet. Complete the onboarding wizard to help Uorin tailor analysis to your preferences."

---

## Error Handling

**Backend Validation Failures:**
- Error message shown inline in edit mode
- Toast notification with error details
- Edit mode stays open (does NOT silently close)
- User can fix and retry

**Network Failures:**
- Error message shown inline
- Toast notification with generic message
- Loading/saving states prevent double-submission

**Profile Load Failures:**
- Error message shown in card
- Does NOT prevent access to empty state
- User can retry or navigate away

---

## Integration with Existing Systems

### Self-Explanation v1 Transparency

**After Save:**
- Transparency card shows: "Judgment Profile: ✅"
- Uses existing integration (no code changes)

**After Delete:**
- Transparency card shows: "Judgment Profile: ❌"
- Uses existing integration (no code changes)

### Onboarding Wizard

- Shares same question definitions
- Consistent UX between onboarding and editing
- Same validation rules
- Same localStorage handling

### Stress Test v1

- No integration (intentional for v1)
- Profile NOT used in consequence detection

### Evidence Layer v1

- No integration (intentional for v1)
- Profile NOT used in source selection

---

## Manual Test Checklist

**Test 1: View Existing Profile**
- [ ] Open Settings
- [ ] Navigate to Judgment Profile section
- [ ] Verify all fields display correctly
- [ ] Verify trust note is visible
- [ ] Verify last updated timestamp shows
- [ ] Verify Edit and Delete buttons present

**Test 2: Edit and Save Profile**
- [ ] Click "Edit" button
- [ ] Verify all 10 questions show
- [ ] Verify current answers are pre-selected
- [ ] Change 2-3 answers
- [ ] Click "Save Changes"
- [ ] Verify success toast appears
- [ ] Verify profile updates in read-only view
- [ ] Refresh page - verify changes persisted
- [ ] Check transparency card shows "Judgment Profile: ✅"

**Test 3: Cancel Edit (No Changes)**
- [ ] Click "Edit" button
- [ ] Change 2-3 answers
- [ ] Click "Cancel"
- [ ] Verify no changes saved
- [ ] Verify read-only view shows original values
- [ ] Verify no toast appears

**Test 4: Delete Profile**
- [ ] Click "Delete" button
- [ ] Verify confirmation dialog appears
- [ ] Verify dialog message matches spec
- [ ] Click "Cancel" - verify nothing happens
- [ ] Click "Delete" again
- [ ] Click "Delete Profile" in dialog
- [ ] Verify success toast appears
- [ ] Verify empty state displays
- [ ] Refresh page - verify profile still deleted
- [ ] Check transparency card shows "Judgment Profile: ❌"

**Test 5: Backend Validation Error**
- [ ] Mock backend to return 400 error
- [ ] Click "Edit" button
- [ ] Click "Save Changes"
- [ ] Verify error message displays inline
- [ ] Verify error toast appears
- [ ] Verify edit mode stays open
- [ ] Fix mock and retry - verify success

**Test 6: No Profile State**
- [ ] Delete profile if exists
- [ ] Open Settings
- [ ] Verify empty state displays
- [ ] Verify message and icon show
- [ ] Complete onboarding wizard
- [ ] Return to Settings
- [ ] Verify profile now displays

**Test 7: localStorage Integration**
- [ ] Complete onboarding with Q10 answered
- [ ] Open Settings
- [ ] Verify Q10 answer shows in profile view
- [ ] Edit profile, change Q10 answer
- [ ] Save changes
- [ ] Verify localStorage updated
- [ ] Verify Q10 answer updated in view

---

## Known Limitations

1. **No jurisdiction "Other" text input** - If user selects "Other" for jurisdiction, only localStorage flag is set (no free-form text entry)
2. **Q10 not used by orchestration** - Default mode preference stored but not yet used by system
3. **No profile history** - Cannot see past versions or undo changes
4. **No profile export/import** - Cannot download/upload profiles
5. **Backend errors may be cryptic** - Validation errors pass through as-is from backend

---

## Future Enhancements (Post-v1)

1. **Profile history** - Track changes over time with undo capability
2. **Profile export/import** - Download/upload JSON profiles
3. **Jurisdiction "Other" free-form** - Allow custom text entry for jurisdiction
4. **Profile recommendations** - Suggest profile changes based on observed behavior (with user approval)
5. **Team profiles** - Share profiles across team members
6. **Default mode orchestration** - Use Q10 to set default interaction mode
7. **Inline editing** - Edit individual fields without full edit mode
8. **Profile templates** - Provide starter templates for common use cases

---

## Rollback Instructions

### Git Rollback

```bash
git checkout rollback-pre-judgment-profile-settings-v1-2026-01-14
git push --force origin main  # Only if already merged
```

### Database Rollback

No database changes in this implementation. Existing profiles remain valid.

To manually delete profile for testing:

```sql
DELETE FROM judgment_profiles WHERE user_key = 'global';
```

### localStorage Cleanup

Users can clear localStorage manually:

```javascript
localStorage.removeItem('uorin_starter_profile_local');
localStorage.removeItem('uorin_onboarding_profile_skipped_until');
```

---

## Security & Privacy

### Authentication

- Uses existing X-UI-Token authentication (dev-only)
- user_key defaults to "global" (single-user mode)
- Future: Session-based auth when cookie infrastructure implemented

### Data Protection

- Profile data stored in PostgreSQL `judgment_profiles` table
- No PII required (all fields are preferences)
- Users control all data (can delete anytime)
- No automatic learning or inference

### IDOR Prevention

- Each user_key has isolated profile
- Users cannot access other users' profiles
- Tested in backend tests

---

## Maintenance Notes

### Adding New Questions

To add new questions:

1. Update `judgmentProfileQuestions.ts` with new question
2. Map to schema field or constraints or local
3. Update documentation
4. Test onboarding and settings flows

### Changing Question Text

To change question text:

1. Update `judgmentProfileQuestions.ts`
2. Changes apply to both onboarding and settings automatically
3. Existing profiles NOT affected (stored values unchanged)

### Handling Schema Changes

If Judgment Profile v1 schema changes:

1. Update backend validation
2. Update `judgmentProfileQuestions.ts` if needed
3. Update JudgmentProfileSettings component if needed
4. Consider migration for existing profiles

---

## Contact

For questions or issues related to Judgment Profile Settings v1, see:
- Judgment Profile v1: `OPS/AUDIT/JUDGMENT_PROFILE_V1.md`
- Starter Onboarding v1: `OPS/AUDIT/STARTER_JUDGMENT_PROFILE_ONBOARDING_V1.md`
- Self-Explanation v1: `OPS/AUDIT/SELF_EXPLANATION_V1.md`

---

## Changelog

### v1.0.0 (2026-01-14)

- Initial implementation
- View, edit, delete functionality
- Toast notifications
- Shared question definitions with onboarding
- Strong delete confirmation
- Trust-preserving messaging
- Frontend-only (no backend changes)
