# Framer Integration Guide for Quillo

## Overview
This guide explains how to wire Framer (frontend) to the Quillo FastAPI backend for a production-ready MVP.

---

## Prerequisites
- Framer project set up (free or paid plan)
- Quillo API deployed and accessible (e.g., `https://quillo-api.replit.app`)
- Basic understanding of Framer Code Overrides and fetch API

---

## Environment Setup

### 1. Set API Base URL
In your Framer project, create a **Code File** named `config.ts`:

```typescript
// config.ts
export const QUILLO_API_BASE =
  process.env.NODE_ENV === "production"
    ? "https://quillo-api.yourproductiondomain.com"
    : "http://localhost:8000";

export const DEFAULT_USER_ID = "demo-user-123"; // For MVP, static demo UUID
```

**Note**: For MVP, we use a static `DEFAULT_USER_ID`. In production, replace with proper authentication (OAuth, JWT, etc.).

---

## API Integration Functions

### 2. Create API Client
Create a **Code File** named `quilloAPI.ts`:

```typescript
// quilloAPI.ts
import { QUILLO_API_BASE, DEFAULT_USER_ID } from "./config";

interface RouteRequest {
  text: string;
  user_id?: string;
  context?: Record<string, any>;
}

interface RouteResponse {
  intent: string;
  reasons: string[];
  slots?: Record<string, any>;
}

interface PlanRequest {
  intent: string;
  user_id?: string;
  slots?: Record<string, any>;
  text?: string;
}

interface PlanStep {
  tool: string;
  premium?: boolean;
  rationale: string;
}

interface PlanResponse {
  steps: PlanStep[];
  trace_id: string;
}

interface ProfileResponse {
  profile_md: string;
  updated_at: string;
}

interface FeedbackRequest {
  user_id: string;
  tool: string;
  outcome: boolean;
  signals?: Record<string, any>;
}

export class QuilloAPI {
  private baseURL: string;
  private userId: string;

  constructor(baseURL: string = QUILLO_API_BASE, userId: string = DEFAULT_USER_ID) {
    this.baseURL = baseURL;
    this.userId = userId;
  }

  async health(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseURL}/health`);
    if (!response.ok) throw new Error("Health check failed");
    return response.json();
  }

  async route(text: string, context?: Record<string, any>): Promise<RouteResponse> {
    const body: RouteRequest = {
      text,
      user_id: this.userId,
      context,
    };

    const response = await fetch(`${this.baseURL}/route`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) throw new Error("Route request failed");
    return response.json();
  }

  async plan(
    intent: string,
    slots?: Record<string, any>,
    text?: string
  ): Promise<PlanResponse> {
    const body: PlanRequest = {
      intent,
      user_id: this.userId,
      slots,
      text,
    };

    const response = await fetch(`${this.baseURL}/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) throw new Error("Plan request failed");
    return response.json();
  }

  async getProfile(): Promise<ProfileResponse> {
    const response = await fetch(
      `${this.baseURL}/memory/profile?user_id=${this.userId}`
    );

    if (!response.ok) throw new Error("Get profile failed");
    return response.json();
  }

  async updateProfile(profileMd: string): Promise<ProfileResponse> {
    const response = await fetch(`${this.baseURL}/memory/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: this.userId,
        profile_md: profileMd,
      }),
    });

    if (!response.ok) throw new Error("Update profile failed");
    return response.json();
  }

  async feedback(
    tool: string,
    outcome: boolean,
    signals?: Record<string, any>
  ): Promise<{ ok: boolean }> {
    const body: FeedbackRequest = {
      user_id: this.userId,
      tool,
      outcome,
      signals,
    };

    const response = await fetch(`${this.baseURL}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) throw new Error("Feedback request failed");
    return response.json();
  }
}

// Singleton instance
export const quilloAPI = new QuilloAPI();
```

---

## Framer Component Examples

### 3. Conversation Input Component
Create a **Code Override** for the input field:

```typescript
// ConversationInput.tsx
import { useState } from "react";
import { Override } from "framer";
import { quilloAPI } from "./quilloAPI";

export function ConversationInput(): Override {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async () => {
    if (!input.trim()) return;

    setLoading(true);
    try {
      // Step 1: Route intent
      const routeResponse = await quilloAPI.route(input);
      console.log("Route response:", routeResponse);

      // Step 2: Generate plan
      const planResponse = await quilloAPI.plan(
        routeResponse.intent,
        routeResponse.slots,
        input
      );
      console.log("Plan response:", planResponse);

      setResult({ route: routeResponse, plan: planResponse });
    } catch (error) {
      console.error("Error:", error);
      alert("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return {
    value: input,
    onValueChange: setInput,
    onSubmit: handleSubmit,
    disabled: loading,
  };
}
```

### 4. Plan Display Component
Create a **Code Override** for displaying plan steps:

```typescript
// PlanDisplay.tsx
import { Override } from "framer";

export function PlanDisplay(planData: any): Override {
  if (!planData || !planData.steps) {
    return { visible: false };
  }

  return {
    visible: true,
    children: planData.steps.map((step: any, index: number) => (
      <div key={index} style={{ marginBottom: "16px" }}>
        <h3>
          {index + 1}. {step.tool} {step.premium && "(Premium)"}
        </h3>
        <p>{step.rationale}</p>
      </div>
    )),
  };
}
```

### 5. Feedback Buttons
Create a **Code Override** for ✅/❌ feedback buttons:

```typescript
// FeedbackButtons.tsx
import { Override } from "framer";
import { quilloAPI } from "./quilloAPI";

export function FeedbackSuccess(tool: string): Override {
  const handleFeedback = async () => {
    try {
      await quilloAPI.feedback(tool, true);
      alert("Thanks for your feedback! ✅");
    } catch (error) {
      console.error("Feedback error:", error);
    }
  };

  return {
    onTap: handleFeedback,
  };
}

export function FeedbackFailure(tool: string): Override {
  const handleFeedback = async () => {
    try {
      await quilloAPI.feedback(tool, false);
      alert("Thanks for your feedback! ❌ We'll improve.");
    } catch (error) {
      console.error("Feedback error:", error);
    }
  };

  return {
    onTap: handleFeedback,
  };
}
```

### 6. Profile Drawer
Create a **Code Override** for profile management:

```typescript
// ProfileDrawer.tsx
import { useState, useEffect } from "react";
import { Override } from "framer";
import { quilloAPI } from "./quilloAPI";

export function ProfileDrawer(): Override {
  const [profile, setProfile] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await quilloAPI.getProfile();
        setProfile(data.profile_md);
      } catch (error) {
        console.error("Error fetching profile:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await quilloAPI.updateProfile(profile);
      alert("Profile saved! ✅");
    } catch (error) {
      console.error("Error saving profile:", error);
      alert("Failed to save profile. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return {
    value: profile,
    onValueChange: setProfile,
    onSave: handleSave,
    disabled: loading,
  };
}
```

---

## Testing the Integration

### Local Testing
1. Run Quillo API locally: `make run` (starts on `http://localhost:8000`)
2. In Framer, ensure `config.ts` points to `http://localhost:8000`
3. Test each endpoint via Framer preview

### Production Testing
1. Deploy Quillo API to Replit, Railway, or Render
2. Update `QUILLO_API_BASE` in `config.ts` with production URL
3. Publish Framer site and test end-to-end

---

## Sample User Flow in Framer

### User Journey
1. **User lands on Quillo app** → Sees conversation canvas
2. **User types**: "Handle this client email and defuse conflict"
3. **User clicks "Send"** → Loading spinner shows
4. **Quillo routes intent** → Intent: "response", Slot: "Defuse"
5. **Quillo generates plan** → 3 steps displayed with rationale
6. **User reviews plan** → Clicks "Approve" button
7. **User provides feedback** → Clicks ✅ (success)
8. **Feedback recorded** → Profile updated, toast notification

---

## Authentication Upgrade (Post-MVP)

### Current: Static Demo UUID
- MVP uses `DEFAULT_USER_ID = "demo-user-123"`
- All users share same profile (demo mode)

### Future: Proper Auth
Replace static UUID with:
1. **Framer Auth** (built-in email/password)
2. **Clerk** (OAuth, magic links, SSO)
3. **Supabase Auth** (JWT-based)
4. **Custom JWT** (issued by Quillo API)

Update `QuilloAPI` constructor to accept dynamic `userId`:
```typescript
const userId = getCurrentUser(); // From auth provider
const api = new QuilloAPI(QUILLO_API_BASE, userId);
```

---

## CORS Configuration

Ensure your Quillo API allows Framer's domain. In `quillo_agent/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Framer dev
        "https://yourframerdomain.framer.app",  # Framer production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Error Handling Best Practices

### In Framer Code Overrides
- **Catch fetch errors** and show user-friendly messages
- **Log errors** to console for debugging
- **Show loading states** while waiting for API responses
- **Handle network timeouts** gracefully

Example:
```typescript
try {
  const response = await quilloAPI.route(input);
  // Success path
} catch (error) {
  if (error instanceof TypeError && error.message === "Failed to fetch") {
    alert("Network error. Please check your connection.");
  } else {
    alert("Something went wrong. Please try again.");
  }
  console.error("API Error:", error);
}
```

---

## Performance Tips

1. **Debounce user input** to avoid excessive API calls
2. **Cache profile data** in React state (fetch once per session)
3. **Show optimistic UI updates** before API confirmation
4. **Use skeleton loaders** for better perceived performance

---

## Deployment Checklist

- [ ] Update `QUILLO_API_BASE` with production URL
- [ ] Test all endpoints (health, route, plan, profile, feedback)
- [ ] Verify CORS settings allow Framer domain
- [ ] Add error handling and loading states
- [ ] Test on desktop, tablet, and mobile
- [ ] Monitor API logs for errors
- [ ] Set up analytics (PostHog, Mixpanel, etc.)

---

## Sample API Calls (curl)

### Route Intent
```bash
curl -X POST https://your-api.replit.app/route \
  -H "Content-Type: application/json" \
  -d '{"text": "Handle this client email and defuse conflict", "user_id": "demo-user-123"}'
```

### Generate Plan
```bash
curl -X POST https://your-api.replit.app/plan \
  -H "Content-Type: application/json" \
  -d '{"intent": "response", "slots": {"outcome": "Defuse"}, "text": "Handle this client email and defuse conflict", "user_id": "demo-user-123"}'
```

### Get Profile
```bash
curl https://your-api.replit.app/memory/profile?user_id=demo-user-123
```

### Send Feedback
```bash
curl -X POST https://your-api.replit.app/feedback \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user-123", "tool": "response_generator", "outcome": true}'
```

---

## Next Steps

1. **Wire up Framer components** using the code overrides above
2. **Test locally** with Quillo API running on `localhost:8000`
3. **Deploy Quillo API** to production (Replit, Railway, Render)
4. **Update Framer config** with production API URL
5. **Publish Framer site** and test end-to-end
6. **Collect user feedback** and iterate

---

## Support
For issues or questions:
- **Quillo API docs**: [GitHub repo](#)
- **Framer community**: [framer.com/community](https://framer.com/community)
- **Email**: dev@quillo.ai
