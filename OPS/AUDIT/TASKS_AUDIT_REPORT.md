# Tasks Audit Report

## Summary
- **Objective:** Understand intended Tasks feature + diagnose 500 error on /tasks fetch.
- **Date:** 2026-01-24 09:53 UTC
- **Branch:** audit/tasks-intent-500-2026-01-24
- **Rollback tag:** ROLLBACK_PRE_TASKS_AUDIT_2026_01_24

---

## Findings

### Root Cause: Database Tables Missing (CRITICAL)

The 500 error on `/tasks` fetch is caused by **missing database tables**:

```
Tables in DB: ['alembic_version', 'judgment_profiles']

Missing tables that should exist:
- task_intents (migration 0002)
- user_prefs (migration 0004)
- task_plans (migration 0006)
```

**Alembic version shows `0008` but tables were never created.** This is a corrupted migration state.

**Actual error when TasksScreen loads:**
```
ProgrammingError: (psycopg2.errors.UndefinedTable)
relation "task_intents" does not exist
```

### Secondary Issue: Missing Step Endpoints

The frontend calls endpoints that don't exist in the backend:

| Frontend API Call | Backend Route | Status |
|------------------|---------------|--------|
| `GET /tasks/intents` | `/ui/api/tasks/intents` | EXISTS (but 500s due to missing table) |
| `POST /tasks/intents` | `/ui/api/tasks/intents` | EXISTS |
| `POST /tasks/{id}/plan` | `/ui/api/tasks/{id}/plan` | EXISTS |
| `GET /tasks/{id}/plan` | `/ui/api/tasks/{id}/plan` | EXISTS |
| `POST /tasks/{id}/plan/approve` | `/ui/api/tasks/{id}/plan/approve` | EXISTS |
| `GET /tasks/{id}/steps` | - | **MISSING** |
| `POST /tasks/{id}/steps/{n}/complete` | - | **MISSING** |

---

## A) Tasks Feature Intent (Product Spec)

From `OPS/CANONICAL/UORIN_PRODUCT_SPEC.md`:

| Component | Normal Mode | Work Mode |
|-----------|-------------|-----------|
| Task Approval settings | **Hidden** | Visible |

**Original intent:** Tasks is a Work-mode feature for tracking approved work with execution plans.

**Current state:** Tasks tab is always visible in Sidebar (both modes), but product spec says Task Approval settings should be hidden in Normal mode.

---

## B) Frontend Implementation Status

**TasksScreen.tsx** - Full implementation exists:
- List task intents with status badges
- Collapsible task scope (will do / won't do / done when)
- Task plan generation and approval
- Step state tracking and completion (calls missing endpoints)

**Sidebar.tsx** - Tasks tab always visible:
```tsx
const menuItems = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'tasks', label: 'Tasks', icon: CheckSquare },  // Always visible
  ...
];
```

---

## C) Backend Implementation Status

**Routes registered in `/ui/api/`:**
- `POST /tasks/intents` - Create task intent
- `GET /tasks/intents` - List task intents
- `POST /tasks/{task_id}/plan` - Create execution plan
- `GET /tasks/{task_id}/plan` - Get execution plan
- `POST /tasks/{task_id}/plan/approve` - Approve plan

**Service layer exists:**
- `quillo_agent/services/tasks/service.py` - TaskIntentService
- `quillo_agent/services/tasks/plan_service.py` - TaskPlanService
- `quillo_agent/services/tasks/repo.py` - Repository layer

**Missing:**
- Step state endpoints (`/tasks/{id}/steps`, `/tasks/{id}/steps/{n}/complete`)
- The step tracking code exists in frontend but backend endpoints not implemented

---

## D) Database Migrations Status

| Migration | Description | Tables Created | Actual State |
|-----------|-------------|----------------|--------------|
| 0001 | Initial | - | OK |
| 0002 | Add task_intents | task_intents | **MISSING** |
| 0003 | Add task scope | (columns) | N/A |
| 0004 | Add user_prefs | user_prefs | **MISSING** |
| 0005 | Add approval_mode | (column) | N/A |
| 0006 | Add task_plans | task_plans | **MISSING** |
| 0007 | Add approved_at | (column) | N/A |
| 0008 | Add judgment_profiles | judgment_profiles | OK |

**Root problem:** `alembic_version` shows `0008` but tables from 0002-0006 never created.

---

## E) Impact Assessment

| User Action | Expected Result | Actual Result |
|-------------|-----------------|---------------|
| Click Tasks tab | See list of task intents | **500 error** |
| Create task from chat | Task saved to DB | **500 error** (table missing) |
| Generate plan | AI creates steps | **500 error** (table missing) |
| Mark step complete | Step marked done | **404 error** (endpoint missing) |

---

## K) Recommendation Framework

### Option 1 — HIDE Tasks (Normal mode) ✓ RECOMMENDED

**Why this option:**
1. Database state is corrupt and needs manual fix
2. Product spec says Tasks should be hidden in Normal mode anyway
3. Frontend implementation is incomplete (step endpoints missing)
4. Hiding now prevents user frustration while we fix properly

**Implementation:**
- Hide Tasks nav item based on mode (Normal = hidden, Work = visible but with "Coming soon")
- Add try/catch in TasksScreen to show graceful error if backend fails
- Do NOT attempt migration fix until we understand why tables weren't created

**Effort:** Small (UI change only)
**Risk:** Low (no data migration, no backend changes)

### Option 2 — GRACEFUL Tasks (both modes)

**Implementation:**
- Keep Tasks visible in both modes
- Show "Coming soon" or empty state when backend fails
- Log errors for debugging

**Why NOT recommended now:**
- Gives false impression feature works
- Product spec says hide in Normal mode

### Option 3 — FIX-NOW Tasks

**Implementation:**
1. Investigate why migrations didn't run (check deployment scripts)
2. Reset alembic_version to 0001 or manually run CREATE TABLE statements
3. Implement missing step endpoints
4. Test full flow

**Why NOT recommended now:**
- High risk (database manipulation)
- Root cause of migration failure unknown
- Time-sensitive - better to stabilize first

---

## L) Immediate Action

**Recommended: HIDE in Normal mode + graceful fallback**

1. Modify Sidebar to hide Tasks in Normal mode (per product spec)
2. Add try/catch in TasksScreen to show user-friendly error
3. Create ticket to investigate migration failure
4. Create ticket to implement missing step endpoints
5. DO NOT attempt database fixes until root cause understood

---

## Appendix: Evidence

### Error reproduction:
```python
from quillo_agent.services.tasks.service import TaskIntentService
TaskIntentService.list_intents(db, limit=5)
# ProgrammingError: relation "task_intents" does not exist
```

### Routes verified:
```
{'POST'} /ui/api/tasks/intents
{'GET'} /ui/api/tasks/intents
{'POST'} /ui/api/tasks/{task_id}/plan
{'GET'} /ui/api/tasks/{task_id}/plan
{'POST'} /ui/api/tasks/{task_id}/plan/approve
```

### Frontend API calls (quilloApi.ts lines 550, 591, 618, 640, 666, 708, 737):
- fetchTaskIntents() → GET /tasks/intents
- createTaskIntent() → POST /tasks/intents
- createTaskPlan() → POST /tasks/{id}/plan
- fetchTaskPlan() → GET /tasks/{id}/plan
- approveTaskPlan() → POST /tasks/{id}/plan/approve
- fetchTaskSteps() → GET /tasks/{id}/steps **← MISSING BACKEND**
- completeTaskStep() → POST /tasks/{id}/steps/{n}/complete **← MISSING BACKEND**
