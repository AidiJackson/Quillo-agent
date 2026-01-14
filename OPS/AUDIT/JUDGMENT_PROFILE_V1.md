# Judgment Profile v1

**Status:** ✅ Implemented
**Date:** 2026-01-12
**Version:** 1.0.0

## Purpose

Judgment Profile v1 provides **explicit, user-controlled** storage for judgment preferences and constraints. This is NOT an automatic learning system - all fields must be explicitly set and confirmed by the user.

Key principles:
- **No automatic inference** - system never fills in missing fields
- **No automatic updates** - system never changes fields without explicit user action
- **Explicit confirmation required** - all fields must have `source="explicit"` and `confirmed_at` timestamp
- **User-controlled only** - users can create, read, update, and delete their profiles at any time

---

## Schema (v1)

### Allowed Top-Level Keys

ONLY these keys are allowed (unknown keys rejected with 400):

- `risk_posture`
- `relationship_sensitivity`
- `decision_authority`
- `default_tone`
- `jurisdiction`
- `constraints`

### Field Structure

Each field MUST be a dictionary with exactly these subfields:

```json
{
  "field_name": {
    "value": "<field-specific-value>",
    "source": "explicit",
    "confirmed_at": "<ISO8601-timestamp>"
  }
}
```

### Enum Values

#### risk_posture
- `conservative` - Prefer lower-risk options, prioritize safety
- `moderate` - Balance risk and reward
- `aggressive` - Accept higher risk for potentially higher reward

#### relationship_sensitivity
- `low` - Direct, task-focused communication
- `medium` - Balance directness with relationship maintenance
- `high` - Prioritize relationship harmony in all interactions

#### decision_authority
- `none` - User makes all decisions, system provides analysis only
- `limited` - System can make low-stakes suggestions
- `full` - System can recommend action plans for user approval

#### default_tone
- `formal` - Professional, structured communication
- `neutral` - Clear and direct without formality
- `casual` - Conversational, friendly tone

#### jurisdiction and constraints
- `jurisdiction`: Free-form text (no enum)
- `constraints`: Free-form text (no enum)

---

## Validation Rules (CRITICAL)

### 1. Unknown Keys Rejected
Profile with unknown keys → **400 Bad Request**

```json
{
  "unknown_field": { ... }  // REJECTED
}
```

### 2. Missing Required Subfields
Each field MUST have `source`, `value`, and `confirmed_at` → **400 Bad Request**

```json
{
  "risk_posture": {
    "value": "conservative"
    // Missing 'source' and 'confirmed_at' → REJECTED
  }
}
```

### 3. Source Must Be "explicit"
Only `source="explicit"` is allowed → **400 Bad Request**

```json
{
  "risk_posture": {
    "value": "conservative",
    "source": "inferred",  // REJECTED (must be "explicit")
    "confirmed_at": "2026-01-12T00:00:00Z"
  }
}
```

### 4. Invalid Enum Values Rejected
Enum fields must use valid values → **400 Bad Request**

```json
{
  "risk_posture": {
    "value": "invalid_value",  // REJECTED
    "source": "explicit",
    "confirmed_at": "2026-01-12T00:00:00Z"
  }
}
```

### 5. Max Payload Size: 20KB
Total JSON payload must be under 20KB → **400 Bad Request**

---

## API Endpoints

All endpoints are under `/ui/api/profile/judgment` and require X-UI-Token authentication.

### GET /ui/api/profile/judgment

Get judgment profile for a user.

**Query Parameters:**
- `user_key` (string, optional): User identifier (defaults to "global")

**Response (200):**
```json
{
  "version": "judgment_profile_v1",
  "profile": {
    "risk_posture": {
      "value": "conservative",
      "source": "explicit",
      "confirmed_at": "2026-01-12T00:00:00Z"
    },
    "default_tone": {
      "value": "formal",
      "source": "explicit",
      "confirmed_at": "2026-01-12T10:30:00Z"
    }
  },
  "updated_at": "2026-01-12T10:30:00.123456"
}
```

**Response when no profile exists:**
```json
{
  "version": "judgment_profile_v1",
  "profile": null,
  "updated_at": null
}
```

### POST /ui/api/profile/judgment

Create or update judgment profile for a user.

**Query Parameters:**
- `user_key` (string, optional): User identifier (defaults to "global")

**Request Body:**
```json
{
  "profile": {
    "risk_posture": {
      "value": "conservative",
      "source": "explicit",
      "confirmed_at": "2026-01-12T00:00:00Z"
    }
  }
}
```

**Response (200):**
```json
{
  "version": "judgment_profile_v1",
  "profile": { ... },
  "updated_at": "2026-01-12T00:00:00.123456"
}
```

**Error Response (400):**
```json
{
  "detail": "Unknown keys not allowed: unknown_field. Allowed keys: risk_posture, relationship_sensitivity, ..."
}
```

**Rate Limit:** 30 requests per minute per IP

### DELETE /ui/api/profile/judgment

Delete judgment profile for a user.

**Query Parameters:**
- `user_key` (string, optional): User identifier (defaults to "global")

**Response (200):**
```json
{
  "deleted": true
}
```

**Response when no profile exists (200):**
```json
{
  "deleted": false
}
```

**Rate Limit:** 30 requests per minute per IP

---

## Authentication & Authorization

### Current Implementation (v1)

- **Auth Method:** X-UI-Token header (shared token)
- **User Identity:** user_key query parameter (defaults to "global")
- **CSRF Protection:** Not implemented in v1

### Future Improvements (Post-v1)

TODO: Replace user_key query parameter with session-derived identity when cookie-session infrastructure is implemented.

TODO: Add CSRF protection when CSRF infrastructure is implemented.

### IDOR Prevention

Each user_key has its own isolated profile. Users cannot access or modify other users' profiles.

Test: `test_idor_prevention_profile_cannot_be_accessed_cross_user`

---

## Integration with Self-Explanation v1

Judgment Profile integrates with Self-Explanation v1 transparency system:

**Transparency Card Shows Profile Status:**
- `Judgment Profile: ✅` - when profile exists for user
- `Judgment Profile: ❌` - when no profile exists

**Transparency Query Example:**
```
User: "What do you remember about me?"

System Response:
Transparency
- Using right now:
  - Conversation context: ❌
  - Session context (24h): ❌
  - Judgment Profile: ✅    ← Shows profile presence
  - Live Evidence: ❌
  - Stress Test mode: ❌
...
```

**Profile Check Behavior:**
- Fast DB read in transparency path (no LLM calls)
- If DB error occurs: reports ❌ + adds note "Profile availability could not be verified" to facts

---

## Non-Goals

This implementation explicitly **does NOT**:

1. **Inject profile into prompts** - v1 is storage-only, does NOT affect LLM behavior
2. **Automatic learning or inference** - system never fills in missing fields
3. **Automatic updates** - system never changes fields without explicit user action
4. **UI changes** - backend-only implementation
5. **Affect orchestration** - profiles are stored but not yet used in decision-making

---

## Database Schema

### Table: judgment_profiles

```sql
CREATE TABLE judgment_profiles (
    user_key VARCHAR PRIMARY KEY,
    profile_json TEXT NOT NULL,
    version VARCHAR NOT NULL DEFAULT 'judgment_profile_v1',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_judgment_profile_user_key UNIQUE (user_key)
);

CREATE INDEX ix_judgment_profiles_user_key ON judgment_profiles (user_key);
```

**Migration:** `alembic/versions/0008_add_judgment_profiles.py`

---

## Testing

All tests are in `tests/test_judgment_profile_v1.py`. Test coverage includes:

1. **Unit Tests:** Validation logic (unknown keys, missing fields, invalid enums)
2. **API Tests:** GET/POST/DELETE endpoints
3. **Security Tests:** IDOR prevention, authentication requirements
4. **Integration Tests:** Self-explanation transparency card integration

Run tests:

```bash
pytest tests/test_judgment_profile_v1.py -v
```

---

## Example Valid Profile

```json
{
  "profile": {
    "risk_posture": {
      "value": "conservative",
      "source": "explicit",
      "confirmed_at": "2026-01-12T10:00:00Z"
    },
    "relationship_sensitivity": {
      "value": "high",
      "source": "explicit",
      "confirmed_at": "2026-01-12T10:05:00Z"
    },
    "decision_authority": {
      "value": "limited",
      "source": "explicit",
      "confirmed_at": "2026-01-12T10:10:00Z"
    },
    "default_tone": {
      "value": "formal",
      "source": "explicit",
      "confirmed_at": "2026-01-12T10:15:00Z"
    },
    "jurisdiction": {
      "value": "California, USA",
      "source": "explicit",
      "confirmed_at": "2026-01-12T10:20:00Z"
    },
    "constraints": {
      "value": "Avoid jargon, prefer visual examples, keep emails under 5 sentences",
      "source": "explicit",
      "confirmed_at": "2026-01-12T10:25:00Z"
    }
  }
}
```

---

## Rollback

If issues are detected, rollback to the pre-implementation state:

```bash
git checkout rollback-pre-judgment-profile-v1-2026-01-12
```

To rollback database:

```bash
alembic downgrade -1
```

---

## Known Limitations (v1)

1. **user_key from query parameter** - Should be session-derived (requires session infrastructure)
2. **No CSRF protection** - Should be added when CSRF infrastructure is available
3. **Storage-only** - Profiles are not yet used in prompts or decision-making (intentional for v1)
4. **No profile versioning** - If schema changes, old profiles may need migration

---

## Future Enhancements (Post-v1)

1. **Session-based auth** - Replace user_key query param with server-derived identity
2. **CSRF protection** - Add CSRF tokens for POST/DELETE
3. **Profile injection** - Use profiles to influence LLM behavior (requires orchestration changes)
4. **Profile history** - Track changes to profiles over time
5. **Profile recommendations** - Suggest profile values based on observed behavior (requires user approval)
6. **Profile sharing** - Allow users to share profiles with team members

---

## Maintenance Notes

### Adding New Allowed Keys

To add new allowed keys to the profile schema:

1. Update `ALLOWED_PROFILE_KEYS` in `quillo_agent/services/judgment_profile/service.py`
2. If the key has enum values, add to `ALLOWED_ENUMS`
3. Update this documentation with the new key and its values
4. Add tests for the new key

### Modifying Validation Rules

Validation logic is in `quillo_agent/services/judgment_profile/service.py`:
- `validate_profile()` - Main validation function
- `ALLOWED_PROFILE_KEYS` - Allowed top-level keys
- `ALLOWED_ENUMS` - Enum values for specific fields

---

## Contact

For questions or issues related to Judgment Profile v1, see:
- Trust Contract v1: OPS/AUDIT/TRUST_CONTRACT_V1.md
- Self-Explanation v1: OPS/AUDIT/SELF_EXPLANATION_V1.md
- Stress Test v1: OPS/AUDIT/STRESS_TEST_V1.md
