# Starter Judgment Profile Onboarding v1

**Status:** ✅ Implemented
**Date:** 2026-01-14
**Version:** 1.0.0
**Branch:** `feature/onboarding-starter-profile-2026-01-14`
**Rollback Tag:** `rollback-pre-onboarding-starter-profile-2026-01-14`

---

## Purpose

Starter Judgment Profile Onboarding v1 provides a **first-run wizard** to help users create an initial Judgment Profile through 10 multiple-choice questions. This is a **storage-only** implementation that does NOT change orchestration, prompts, stress-test, or evidence behavior.

### Key Principles

- **Explicit only** - Only stores what the user explicitly selects
- **Optional** - Users can skip ("Remind me later" with 7-day TTL)
- **User-controlled** - Users can edit or delete anytime
- **Privacy-first** - Clear explanation of what's stored and why
- **Schema-strict** - Only persists fields allowed by Judgment Profile v1 schema

---

## What It Does

1. **First-run check**: On app mount, checks if user has a Judgment Profile
2. **Skip TTL check**: Respects "Remind me later" 7-day skip period
3. **Modal wizard**: Shows 10-question multiple-choice wizard if:
   - No profile exists, AND
   - Skip period has expired (or doesn't exist)
4. **Saves profile**: Creates Judgment Profile via `POST /ui/api/profile/judgment`
5. **Shows in transparency**: Profile presence now shows as ✅ in Self-Explanation v1

---

## What It Does NOT Do

This implementation explicitly **does NOT**:

1. **Change LLM behavior** - Storage-only, does NOT affect prompts or orchestration
2. **Automatic updates** - Never changes profile without explicit user action
3. **Automatic inference** - Never fills in missing fields
4. **Force completion** - Users can skip indefinitely
5. **Affect stress test** - Does NOT change consequence detection or trust signals
6. **Affect evidence layer** - Does NOT change sourcing or fact extraction

---

## The 10 Questions

### Questions Mapped to Schema Fields

| # | Question | Schema Field | Allowed Values |
|---|----------|--------------|----------------|
| 1 | How do you approach risk? | `risk_posture` | conservative, moderate, aggressive |
| 2 | Relationship harmony importance? | `relationship_sensitivity` | low, medium, high |
| 3 | System decision authority? | `decision_authority` | none, limited, full |
| 4 | Preferred communication tone? | `default_tone` | formal, neutral, casual |
| 5 | Primary jurisdiction/locale? | `jurisdiction` | UK, US, EU, Other (free-form) |

### Questions Mapped to Constraints Field

| # | Question | Stored In | Format |
|---|----------|-----------|--------|
| 6 | Speed vs certainty? | `constraints` | Free-form text concatenated |
| 7 | Irreversible actions handling? | `constraints` | Free-form text concatenated |
| 8 | Communication style? | `constraints` | Free-form text concatenated |
| 9 | Evidence strictness? | `constraints` | Free-form text concatenated |

**Constraints Field Example:**
```
"How do you balance speed and certainty?: Balanced - Balance speed with confidence; How do you handle irreversible actions?: Case-by-case - Evaluate based on context; ..."
```

### Questions Stored Locally Only

| # | Question | Storage | Key |
|---|----------|---------|-----|
| 10 | Default mode preference? | localStorage | `uorin_starter_profile_local` |

**Reason:** Default mode preference is not yet supported by Judgment Profile v1 schema. Stored locally for future use when orchestration supports it.

---

## Storage Details

### Backend (Judgment Profile v1)

**Endpoint:** `POST /ui/api/profile/judgment?user_key=global`

**Payload Structure:**
```json
{
  "profile": {
    "risk_posture": {
      "value": "conservative",
      "source": "explicit",
      "confirmed_at": "2026-01-14T10:00:00Z"
    },
    "relationship_sensitivity": {
      "value": "high",
      "source": "explicit",
      "confirmed_at": "2026-01-14T10:00:00Z"
    },
    "decision_authority": {
      "value": "limited",
      "source": "explicit",
      "confirmed_at": "2026-01-14T10:00:00Z"
    },
    "default_tone": {
      "value": "formal",
      "source": "explicit",
      "confirmed_at": "2026-01-14T10:00:00Z"
    },
    "jurisdiction": {
      "value": "UK",
      "source": "explicit",
      "confirmed_at": "2026-01-14T10:00:00Z"
    },
    "constraints": {
      "value": "How do you balance speed and certainty?: Balanced - Balance speed with confidence; How do you handle irreversible actions?: Case-by-case - Evaluate based on context; What communication style resonates with you?: Warm & clear - Friendly but straightforward; When do you want sources and evidence cited?: Always want sources - Always cite sources when facts are involved",
      "source": "explicit",
      "confirmed_at": "2026-01-14T10:00:00Z"
    }
  }
}
```

### localStorage

**Keys:**
- `uorin_starter_profile_local` - Local-only profile data (JSON)
  ```json
  {
    "default_mode": "work_mode"
  }
  ```

- `uorin_onboarding_profile_skipped_until` - Skip TTL (ISO timestamp)
  ```
  "2026-01-21T10:00:00Z"
  ```

---

## Privacy Guarantees

1. **Explicit consent** - User must click through wizard and select each answer
2. **Skip anytime** - "Remind me later" or close wizard to skip
3. **Delete anytime** - Users can delete profile via Settings (future) or API
4. **No inference** - System never guesses or fills in missing fields
5. **Transparent storage** - Clear explanation of what's stored and where
6. **Local-first for unsupported fields** - Fields not in schema stored locally only

---

## User Experience Flow

### First Run (No Profile)

1. User opens app
2. App checks for profile via `GET /ui/api/profile/judgment`
3. Profile is `null` or empty
4. Skip TTL doesn't exist or has expired
5. Modal wizard appears with:
   - Title: "Starter Judgment Profile"
   - Subtitle: "Help Uorin tailor analysis to your preferences. This is explicit, user-controlled storage. You can edit or delete this anytime. Takes about 2 minutes."
   - Progress bar showing X of 10
   - Single question with 3-4 options
   - "Remind me later" button (bottom-left)
   - "Back" button (if not on first question)
   - "Next" / "Complete Setup" button (bottom-right)

### Skip Flow

1. User clicks "Remind me later" or close (X) button
2. Skip TTL set to 7 days from now
3. Modal closes
4. User continues to app

### Completion Flow

1. User answers all 10 questions
2. Clicks "Complete Setup"
3. Profile saved to backend
4. Local-only data saved to localStorage
5. Skip TTL cleared (if exists)
6. Modal closes
7. Confirmation toast: "Saved. You can edit or delete this anytime." (future enhancement)

### Subsequent Visits

- If profile exists: No modal shown
- If profile doesn't exist but skip TTL active: No modal shown
- If profile doesn't exist and skip TTL expired: Modal shown again

---

## Implementation Files

### Frontend

- `frontend/src/lib/quilloApi.ts` - Added `getJudgmentProfile()` and `upsertJudgmentProfile()`
- `frontend/src/app/App.tsx` - Added profile check on mount + wizard state
- `frontend/src/app/components/OnboardingWizard.tsx` - New wizard component (10 questions)

### Backend

Uses existing Judgment Profile v1 endpoints (no backend changes):
- `GET /ui/api/profile/judgment` - Check if profile exists
- `POST /ui/api/profile/judgment` - Save profile

---

## Testing

### Manual Test Checklist

1. **Fresh user / no profile**
   - [ ] Open app
   - [ ] Wizard appears
   - [ ] Complete all 10 questions
   - [ ] Profile saved successfully
   - [ ] Wizard closes
   - [ ] Refresh app - wizard does NOT appear

2. **Skip flow**
   - [ ] Clear profile via API or DB
   - [ ] Open app
   - [ ] Wizard appears
   - [ ] Click "Remind me later"
   - [ ] Wizard closes
   - [ ] Refresh app - wizard does NOT appear (within 7 days)
   - [ ] Change skip TTL in localStorage to past date
   - [ ] Refresh app - wizard appears again

3. **Back button**
   - [ ] Start wizard
   - [ ] Answer Q1, go to Q2
   - [ ] Click "Back"
   - [ ] Q1 shows with previous answer selected

4. **Error handling**
   - [ ] Mock API failure
   - [ ] Try to submit wizard
   - [ ] Error message appears
   - [ ] Wizard stays open
   - [ ] Fix API
   - [ ] Retry - succeeds

5. **Profile presence in transparency**
   - [ ] Complete wizard
   - [ ] Type "What do you remember about me?"
   - [ ] Self-Explanation card shows: "Judgment Profile: ✅"

---

## Known Limitations

1. **No edit UI** - Users cannot edit profile from UI yet (must use API or delete and recreate)
2. **No delete UI** - Users cannot delete profile from UI yet (must use API)
3. **Default mode not used** - Q10 answer stored locally but not yet used by orchestration
4. **Jurisdiction "Other" not persisted** - If user selects "Other" for jurisdiction, only localStorage flag is set
5. **No confirmation toast** - After saving, no visual confirmation (wizard just closes)

---

## Future Enhancements

1. **Settings screen integration** - View, edit, delete profile from UI
2. **Default mode orchestration** - Use Q10 answer to set default interaction mode
3. **Jurisdiction "Other" text input** - Allow free-form jurisdiction entry
4. **Profile recommendations** - Suggest profile changes based on observed behavior (with user approval)
5. **Profile export/import** - Let users download/upload profiles
6. **Team profiles** - Share profiles across team members

---

## Rollback Instructions

If issues are detected, rollback to pre-onboarding state:

### Git Rollback

```bash
git checkout rollback-pre-onboarding-starter-profile-2026-01-14
git push --force origin main  # Only if already merged
```

### Database Rollback

No database changes in this implementation. Existing profiles remain valid.

To clear profiles for testing:

```bash
# Delete all profiles
DELETE FROM judgment_profiles WHERE user_key = 'global';
```

### localStorage Cleanup

Users can clear localStorage manually:

```javascript
localStorage.removeItem('uorin_starter_profile_local');
localStorage.removeItem('uorin_onboarding_profile_skipped_until');
```

---

## Integration with Existing Systems

### Self-Explanation v1

- Profile presence already integrated
- Transparency card shows: "Judgment Profile: ✅" when profile exists
- Fast DB read (no LLM calls)

### Stress Test v1

- No integration yet (intentional for v1)
- Profile NOT used in consequence detection
- Profile NOT used in trust signal generation

### Evidence Layer v1

- No integration yet (intentional for v1)
- Profile NOT used in source selection
- Profile NOT used in fact extraction

---

## Security & Privacy

### Authentication

- Uses existing X-UI-Token authentication (dev-only)
- user_key defaults to "global" (single-user mode)
- Future: Session-based auth when cookie infrastructure implemented

### Data Protection

- Profile data stored in PostgreSQL `judgment_profiles` table
- No PII required (all fields are preferences, not personal data)
- Users control all data (can delete anytime)
- No automatic learning or inference

### IDOR Prevention

- Each user_key has isolated profile
- Users cannot access other users' profiles
- Tested in `test_idor_prevention_profile_cannot_be_accessed_cross_user`

---

## Maintenance Notes

### Adding New Questions

To add new questions to the wizard:

1. Update `QUESTIONS` array in `OnboardingWizard.tsx`
2. Map to existing schema field or `constraints` or `local`
3. Update this documentation with new question details

### Changing Schema

If Judgment Profile v1 schema changes:

1. Update backend validation in `quillo_agent/services/judgment_profile/service.py`
2. Update wizard question mappings in `OnboardingWizard.tsx`
3. Update this documentation
4. Consider migration for existing profiles

---

## Contact

For questions or issues related to Starter Judgment Profile Onboarding v1, see:
- Judgment Profile v1: `OPS/AUDIT/JUDGMENT_PROFILE_V1.md`
- Self-Explanation v1: `OPS/AUDIT/SELF_EXPLANATION_V1.md`
- Trust Contract v1: `OPS/AUDIT/TRUST_CONTRACT_V1.md`

---

## Changelog

### v1.0.0 (2026-01-14)

- Initial implementation
- 10-question wizard with multiple-choice options
- Maps Q1-Q5 to schema fields, Q6-Q9 to constraints, Q10 to localStorage
- Skip with 7-day TTL
- Strict schema validation
- No orchestration changes (storage-only)
