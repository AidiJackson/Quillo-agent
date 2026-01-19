# Mode Toggle v1

**Date:** 2026-01-18
**Author:** Claude Opus 4.5
**Status:** Implemented

## Purpose

Enable users to switch between two operational modes in Uorin:

- **Work Mode** (default): Full Trust Contract enforcement with evidence auto-fetch, no-assumptions gating, and stress test activation
- **Normal Mode**: Free-form chat with no automatic guardrails

## Philosophy

Users need flexibility. Some interactions require Uorin's full judgment-layer protection (business decisions, contracts, risky actions). Others are casual conversations where guardrails would be intrusive.

Rather than guessing context, we give users explicit control with a simple toggle.

## Definitions

### Work Mode (default)
- Evidence default-on: Auto-fetches web evidence when prompts contain temporal/factual triggers
- No-assumptions enforcement: Asks clarifying questions when critical context is missing
- Stress Test activation: Detects consequential decisions and activates multi-lens analysis
- Structured outputs: Encourages Evidence/Interpretation/Recommendation format
- Full micro-disclosures: Shows all trust signals in responses

### Normal Mode
- No automatic evidence fetch (user can still manually request via "Fetch current facts")
- No no-assumptions gating (prompts proceed to LLM without clarifying questions)
- No stress test activation (no consequence detection or lens assignment)
- Free-form responses (no forced structure)
- Minimal micro-disclosures (shows mode only)

## Default Behavior

**Default: Work Mode**

If no mode is specified in the request, the system defaults to Work mode. This ensures:
- Backward compatibility with existing clients
- Safe default for new users
- No behavior change for users who don't opt out

## API Contract

### Request Schema

Both `/ui/api/ask` and `/ui/api/multi-agent` accept an optional `mode` field:

```json
{
  "text": "User's message",
  "user_id": "optional-user-id",
  "mode": "work"  // or "normal", optional, defaults to "work"
}
```

### Mode Normalization

The backend normalizes mode values as follows:
- `null` / missing → `"work"`
- `""` (empty string) → `"work"`
- `"work"` (case-insensitive) → `"work"`
- `"normal"` (case-insensitive) → `"normal"`
- Any other value → `"work"` (fail-safe)

### Response Disclosure

Responses include a mode disclosure in micro-disclosures:

```
Mode: Work (guardrails + evidence triggers + stress test)
```

or

```
Mode: Normal (free-form; no auto guardrails)
```

## Backend Decision Matrix

| Behavior | Work Mode | Normal Mode |
|----------|-----------|-------------|
| `enforce_no_assumptions()` | Yes | No |
| `classify_prompt_needs_evidence()` | Yes | No |
| `retrieve_evidence()` auto-fetch | Yes | No |
| `detect_consequence()` | Yes | No |
| `stress_test_mode` flag | Computed | Always False |
| Structured output requirements | Yes | No |
| Mode in micro-disclosures | Yes | Yes |

## Frontend Implementation

### Storage

Mode preference is stored in `localStorage` with key: `uorin_default_mode_v1`

### Bootstrap from Onboarding

If `uorin_default_mode_v1` is not set, the system checks for onboarding Q10 preference in `uorin_starter_profile_local`:
- Q10 value "free" → Normal mode
- Q10 value "structured" → Work mode
- Otherwise → Work mode (default)

This is a one-time bootstrap; subsequent changes use the toggle directly.

### UI Components

1. **ModeToggle** (Settings): Full toggle with descriptions in `/frontend/src/app/components/ModeToggle.tsx`
2. **ModeIndicator** (Chat header): Compact read-only indicator showing current mode

### API Calls

Frontend includes `mode` in all `/ask` and `/multi-agent` requests:

```typescript
await ask(text, userId, getStoredMode());
await multiAgent(text, userId, undefined, getStoredMode());
```

## Known Limitations (v1)

1. **No server-side persistence**: Mode is stored in `localStorage` only. Switching devices requires re-setting preference.
2. **No per-conversation mode**: Mode applies globally to all requests. Future versions may support per-conversation override.
3. **No mode history**: We don't track mode changes for audit purposes yet.
4. **Manual evidence still available**: In Normal mode, users can still manually click "Fetch current facts" to retrieve evidence.

## Rollback Instructions

If this feature needs to be rolled back:

```bash
git checkout main
git reset --hard ROLLBACK_PRE_MODE_TOGGLE_V1_2026_01_18
```

Or to create a revert commit:

```bash
git revert <commit-hash>
```

## Files Changed

### Backend
- `quillo_agent/mode.py` (new) - Mode constants and normalization
- `quillo_agent/schemas.py` - Added `mode` field to `AskRequest` and `MultiAgentRequest`
- `quillo_agent/routers/ui_proxy.py` - Mode-conditional trust contract enforcement
- `quillo_agent/self_explanation.py` - Added mode to `build_micro_disclosures()`

### Frontend
- `frontend/src/lib/uorinMode.ts` (new) - Mode type, storage, and helpers
- `frontend/src/lib/quilloApi.ts` - Added `mode` parameter to `ask()` and `multiAgent()`
- `frontend/src/app/components/ModeToggle.tsx` (new) - Toggle component
- `frontend/src/app/components/SettingsScreen.tsx` - Added ModeToggle section
- `frontend/src/app/components/ChatScreen.tsx` - Added ModeIndicator and mode in API calls

### Tests
- `tests/test_mode_toggle_v1.py` (new) - Comprehensive tests for mode functionality

## Related Documentation

- `TRUST_CONTRACT_V1.md` - Trust contract behaviors (applies in Work mode)
- `STRESS_TEST_V1.md` - Stress test behaviors (only activates in Work mode)
- `SELF_EXPLANATION_V1.md` - Self-explanation behaviors (mode disclosure added)
