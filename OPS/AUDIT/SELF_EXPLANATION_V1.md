# UORIN Self-Explanation v1

**Status:** ✅ Implemented
**Date:** 2026-01-12
**Version:** 1.0.0

## Purpose

UORIN Self-Explanation v1 provides lightweight, user-initiated transparency about what context and signals the system is using. This implementation includes:

1. **Transparency Card**: A structured disclosure returned when users ask transparency questions (e.g., "what do you remember?", "what are you using?")
2. **Micro-disclosures**: Small trust signals prepended to responses when certain conditions are met (evidence used, stress test mode active, etc.)

This system is designed to build user trust through selective, non-intrusive transparency without overwhelming the user or exposing internal implementation details.

---

## Features

### 1. Transparency Card

When a user asks a transparency question, the system returns a structured card showing:

- **What's being used right now**: Conversation context, session context, judgment profile, live evidence, stress test mode (checkmarks/X marks)
- **What's being treated as facts**: Sources with timestamps (or explicit "No external facts fetched")
- **What's not being assumed**: Explicit list of things the system is NOT inferring
- **What's needed from user**: Questions or clarifications (or "Nothing needed")
- **Control options**: Instructions to clear context or view profile

**Critical behavior**: Transparency queries short-circuit ALL LLM calls and evidence fetches. The card is built from already-known state only.

### 2. Micro-disclosures

When applicable, single-line trust signals are prepended to responses in this order:

1. `Evidence: on (sources + timestamps below)` - When evidence was successfully fetched and used
2. `Mode: Stress Test (consequential decision detected)` - When stress test mode is active
3. `Context: using this conversation's history` - When conversation history exists and is used
4. `Profile: using your saved preferences (view/edit anytime)` - When user profile/preferences are actively used

**Critical behavior**: Disclosures appear ONLY when the condition is actually true. They must not be implied or guessed.

---

## When Micro-disclosures Appear

### Conditions (Copy-locked)

| Disclosure | Condition |
|-----------|-----------|
| `Evidence: on (sources + timestamps below)` | Evidence was fetched AND successfully used (has facts) |
| `Mode: Stress Test (consequential decision detected)` | Stress test mode is active (consequence detected via `detect_consequence()`) |
| `Context: using this conversation's history` | Conversation history exists, is non-empty, AND was passed to the LLM |
| `Profile: using your saved preferences (view/edit anytime)` | User profile/preferences were read AND actually used in the prompt/decision |

### Copy-locked Disclosure Lines

These exact strings must be used (do not paraphrase or modify):

```
Evidence: on (sources + timestamps below)
Mode: Stress Test (consequential decision detected)
Context: using this conversation's history
Profile: using your saved preferences (view/edit anytime)
```

---

## Transparency Query Triggers

The system detects transparency queries via simple substring matching against patterns like:

- "what do you remember"
- "what are you using"
- "why are you saying"
- "are you assuming"
- "is this up to date"
- "did you store"
- "what did you use"
- "what context"

**Note**: Pattern matching is case-insensitive and uses substring matching (not regex or complex NLP).

---

## Transparency Card Format

```
Transparency
- Using right now:
  - Conversation context: ✅/❌
  - Session context (24h): ✅/❌
  - Judgment Profile: ✅/❌
  - Live Evidence: ✅/❌
  - Stress Test mode: ✅/❌

- What I'm treating as facts:
  - [fact with source + timestamp]
  - OR: No external facts fetched.

- What I'm not assuming:
  - [explicit items]
  - OR: None

- What I need from you (if anything):
  - [questions/clarifications]
  - OR: Nothing needed

Control:
- Say "clear context" to reset this conversation.
- Say "view profile" to inspect saved preferences.
```

---

## Non-goals

This implementation explicitly **does NOT**:

1. **Expose internal prompts or system messages**: The transparency card shows only high-level flags and user-facing facts
2. **Leak internal heuristics**: No keyword lists, pattern matching logic, or internal implementation details are disclosed
3. **Expose model names or technical internals**: The card is user-friendly, not a technical debug tool
4. **Automatically trigger without user request**: Transparency cards only appear when users explicitly ask transparency questions
5. **Make assumptions about flags**: All flags are based on actual runtime state, not guesses or implications

---

## Implementation Details

### Files Modified

- `quillo_agent/routers/ui_proxy.py`: Added transparency query detection and micro-disclosure logic to `/ask` and `/multi-agent` endpoints

### Files Created

- `quillo_agent/self_explanation.py`: Core transparency detection and formatting logic
- `tests/test_self_explanation_v1.py`: Comprehensive test suite
- `OPS/AUDIT/SELF_EXPLANATION_V1.md`: This documentation

### Integration Points

1. **`/ui/api/ask` endpoint**:
   - Checks for transparency query BEFORE evidence fetch
   - Returns transparency card without LLM call if detected
   - Adds micro-disclosures to response if applicable

2. **`/ui/api/multi-agent` endpoint**:
   - Checks for transparency query BEFORE evidence fetch
   - Returns transparency card without LLM call if detected
   - Adds micro-disclosures to synthesis message (last quillo message) if applicable

---

## Known Limitations

### Current State (v1)

1. **Session context flag is always false**: Session context (24h buffer) is not yet implemented, so this flag will always show ❌
2. **Profile flag is conservative**: Profile disclosure only appears if profile/preferences are ACTUALLY used in the request. Currently most endpoints don't use profile, so this will typically be false.
3. **Conversation context disabled**: Conversation storage is not yet implemented, so conversation context flag is always false
4. **No conversation history tracking**: The "Context: using this conversation's history" disclosure won't appear until conversation storage is implemented

### Future Enhancements (Post-v1)

1. Enable conversation context tracking and disclosure when conversation storage is implemented
2. Enable session context (24h) when session buffer is implemented
3. Enable profile disclosure when profile injection into prompts is implemented
4. Consider adding more transparency query patterns based on user feedback
5. Consider adding transparency card export/download feature

---

## Testing

All tests are in `tests/test_self_explanation_v1.py`. Test coverage includes:

1. **Unit tests**: Transparency query detection, card building, micro-disclosure formatting
2. **Integration tests**: `/ask` and `/multi-agent` endpoints with various scenarios
3. **Security tests**: Verify profile disclosure only appears when actually used
4. **Negative tests**: Verify non-transparency queries are not detected
5. **Format tests**: Verify no internal heuristics or prompts leak in transparency card

Run tests:

```bash
pytest tests/test_self_explanation_v1.py -v
```

---

## Audit Checklist

- ✅ Transparency queries short-circuit LLM calls
- ✅ Transparency card does not leak internal prompts or heuristics
- ✅ Micro-disclosures only appear when conditions are actually true
- ✅ Copy-locked disclosure strings are used exactly as specified
- ✅ Profile disclosure is conservative (false unless actively used)
- ✅ Evidence disclosure only appears when evidence successfully fetched
- ✅ Stress test disclosure only appears when consequence detected
- ✅ All tests pass
- ✅ Backward compatible (no breaking changes)
- ✅ No UI changes required
- ✅ No schema/migration changes required

---

## Rollback

If issues are detected, rollback to the pre-implementation state:

```bash
git checkout rollback-pre-self-explanation-v1-2026-01-12
```

---

## Maintenance Notes

### Adding New Transparency Patterns

To add new transparency query patterns, edit `TRANSPARENCY_QUERY_PATTERNS` in `quillo_agent/self_explanation.py`:

```python
TRANSPARENCY_QUERY_PATTERNS = [
    "what do you remember",
    "what are you using",
    # Add new patterns here (lowercase, substring match)
]
```

### Modifying Disclosure Text

To modify disclosure text, edit `build_micro_disclosures()` in `quillo_agent/self_explanation.py`. **WARNING**: Disclosure text is copy-locked in this spec. Changes should be coordinated and documented.

### Enabling New Context Flags

When implementing conversation storage or session context:

1. Update the transparency state dict in `/ask` and `/multi-agent` endpoints
2. Update the `build_micro_disclosures()` calls to pass the new flags
3. Add tests to verify the new flags work correctly
4. Update this documentation to reflect the new capabilities

---

## Contact

For questions or issues, see: OPS/AUDIT/TRUST_CONTRACT_V1.md and OPS/AUDIT/STRESS_TEST_V1.md for related context.
