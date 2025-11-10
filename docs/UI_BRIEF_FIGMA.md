# Quillo UI Design Brief (Figma AI Prompt)

## Project Overview
**Title**: Quillo — AI Chief of Staff UI Design System

**Goal**: Create a premium, minimal UI that feels like interacting with a real Chief of Staff: intelligent, context-aware, trustworthy, and efficient.

**Target Users**: Executives, founders, sales leaders, and professionals handling high-stakes communications.

---

## Design Pages

### Page 1: Standalone Quillo App (Primary Interface)
**Purpose**: The main workspace where users interact with Quillo to route, plan, and execute communication tasks.

### Page 2: Marketing Landing Page
**Purpose**: Public-facing site to explain Quillo's value proposition and drive sign-ups.

---

## Design Language

### Brand Attributes
- **Premium**: High-end, professional, trustworthy
- **Minimal**: Clean, uncluttered, focus on content
- **Intelligent**: Thoughtful, context-aware, adaptive
- **Confident**: Executive-level polish and judgment

### Visual Style
- **Clean grid system**: 8px base unit, consistent spacing
- **Glassmorphic cards**: Subtle frosted glass effect for depth
- **Soft shadows**: `box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08)`
- **Rounded corners**: `border-radius: 16px` (cards), `12px` (buttons)
- **Accessible typography**: Clear hierarchy, generous line-height

---

## Color Palette

### Primary Colors
- **Royal Blue**: `#2563EB` (primary actions, accents)
- **Sky Blue**: `#0EA5E9` (secondary actions, highlights)
- **Platinum**: `#F8FAFC` (backgrounds, cards)
- **Charcoal**: `#1E293B` (primary text)
- **Slate Gray**: `#64748B` (secondary text)

### Status Colors
- **Success Green**: `#10B981` (✅ feedback, success states)
- **Warning Amber**: `#F59E0B` (caution, pending states)
- **Error Red**: `#EF4444` (❌ feedback, errors)
- **Info Blue**: `#3B82F6` (informational messages)

### Glassmorphic Effects
- **Glass Background**: `rgba(255, 255, 255, 0.7)` with `backdrop-filter: blur(12px)`
- **Glass Border**: `1px solid rgba(255, 255, 255, 0.3)`

---

## Typography Scale

### Font Family
- **Primary**: `Inter` (body, UI elements)
- **Display**: `Cal Sans` or `Clash Display` (headlines, marketing)
- **Monospace**: `JetBrains Mono` (code, trace IDs)

### Type Scale
| Style | Size | Weight | Line Height | Use Case |
|-------|------|--------|-------------|----------|
| Display | 48px | 700 | 1.1 | Hero headlines |
| H1 | 36px | 700 | 1.2 | Page titles |
| H2 | 24px | 600 | 1.3 | Section headers |
| H3 | 20px | 600 | 1.4 | Card titles |
| Body | 16px | 400 | 1.6 | Body text |
| Small | 14px | 400 | 1.5 | Captions, metadata |
| Tiny | 12px | 500 | 1.4 | Tags, labels |

---

## Core Components (Page 1: Quillo App)

### 1. Conversation Canvas
**Description**: Main chat-like interface for user input and Quillo responses.

**Layout**:
- Full-width content area with max-width `1200px`
- User messages: Right-aligned, royal blue background
- Quillo responses: Left-aligned, glass card with soft shadow
- Input bar: Bottom-fixed, glass effect, `48px` height

**Elements**:
- **User Input**: Textarea with placeholder "Tell Quillo what you need..."
- **Submit Button**: Royal blue pill button, icon + text "Send"
- **Message Cards**: Glassmorphic, rounded-2xl, avatar + timestamp
- **Optional Voice Mic**: Circular button, subtle pulse animation

---

### 2. Plan Trace Panel
**Description**: Side panel showing the "why" behind Quillo's plan steps.

**Layout**:
- Right sidebar, `360px` width
- Collapsible on mobile
- Glassmorphic background

**Elements**:
- **Trace ID**: Monospace font, tiny size, top-right badge
- **Step List**: Numbered vertical timeline
  - Each step: Tool name, premium badge (if applicable), rationale text
- **Confidence Meter**: Horizontal bar showing routing confidence
- **Expand/Collapse Button**: Icon-only, top-right corner

---

### 3. Toolchain Timeline
**Description**: Visual representation of the execution flow.

**Layout**:
- Horizontal stepper below conversation canvas
- Auto-scrolls as steps complete

**Elements**:
- **Step Nodes**: Circles with tool icons
  - Pending: Gray outline
  - In Progress: Royal blue fill with spinner
  - Complete: Green fill with checkmark
- **Connectors**: Dashed lines between nodes
- **Tool Labels**: Below each node, small font

**Flow Example**:
```
[Response Generator] → [Tone Adjuster] → [Conflict Resolver] → [Final Output]
```

---

### 4. Profile Drawer
**Description**: Slide-in drawer for viewing and editing user profile.

**Layout**:
- Right slide-in drawer, `480px` width
- Activated by avatar click or menu item
- Glassmorphic overlay + drawer

**Elements**:
- **Avatar**: Large circle, top-center, editable on hover
- **Profile Markdown Editor**: Live preview, syntax highlighting
- **Section Tabs**:
  - Core Identity
  - Tone & Style
  - Negotiation Patterns
  - Highlights
- **Save Button**: Royal blue, bottom-right sticky
- **Privacy Toggle**: Inline, each section (visible to Quillo or private)

---

### 5. Memory/Privacy Controls
**Description**: Settings panel for memory and privacy preferences.

**Layout**:
- Modal or slide-in drawer
- Glassmorphic card with sections

**Elements**:
- **Memory Mode Selector**:
  - **Strict**: "Only use explicitly provided context"
  - **Balanced**: "Use profile + recent interactions"
  - **Full**: "Use all data for maximum personalization"
- **Data Export**: Button to download profile and history (JSON/CSV)
- **Clear History**: Destructive action, confirmation modal
- **Delete Account**: Red button, final confirmation flow

---

### 6. Action Bar
**Description**: Fixed bottom bar with primary actions.

**Layout**:
- Bottom-fixed, glass effect, `72px` height
- Max-width `1200px`, centered

**Elements**:
- **Run Plan Button**: Large royal blue button, icon + text
- **Approve/Send Button**: Green button, appears after plan completion
- **Feedback Buttons**: ✅ and ❌ icon buttons, small, right-aligned
- **More Options**: Overflow menu (vertical dots)

---

### 7. Optional Voice Mic
**Description**: Voice input toggle for hands-free interaction.

**Layout**:
- Floating action button (FAB), bottom-right corner
- Circular, `56px` diameter, royal blue

**States**:
- **Idle**: Mic icon, solid fill
- **Listening**: Pulsing animation, red dot indicator
- **Processing**: Spinner overlay

---

## Interactions

### Primary Flow
1. **User submits input** → Conversation canvas shows loading state
2. **Quillo routes intent** → Plan Trace Panel populates with reasoning
3. **Quillo generates plan** → Toolchain Timeline animates steps
4. **User reviews plan** → Action Bar shows "Approve" button
5. **User provides feedback** → ✅/❌ buttons update profile, toast confirmation

### Micro-Interactions
- **Hover**: Buttons lift (`transform: translateY(-2px)`) + shadow increase
- **Click**: Brief scale animation (`transform: scale(0.98)`)
- **Loading**: Shimmer effect on skeleton placeholders
- **Success**: Green checkmark bounce-in animation
- **Error**: Shake animation + red border pulse

### Transitions
- **Panel open/close**: `300ms` ease-in-out slide
- **Step completion**: `200ms` fade-in + scale
- **Toast notifications**: `150ms` slide-up from bottom

---

## Page-Specific Elements

### Page 2: Marketing Landing Page

#### Hero Section
- **Headline**: "Your AI Chief of Staff" (Display font, 48px)
- **Subheadline**: "Handle high-stakes communications with intelligence and judgment"
- **CTA Button**: "Start Free Trial" (Royal blue, prominent)
- **Hero Visual**: Abstract 3D illustration of connected nodes (orchestration concept)

#### Features Section
- **3-column grid** on desktop, stacked on mobile
- Each feature:
  - Icon (custom, line-style)
  - Title (H3)
  - Description (Body)
  - "Learn more" link (Sky blue, arrow icon)

#### How It Works
- **4-step visual flow** with numbered cards
- Each card: Icon + Title + Description
- Connecting arrows between cards

#### Pricing Section
- **3 pricing tiers** (Free, Quillo Team Starter, Professional)
- Glassmorphic cards, center tier highlighted with royal blue border
- Feature list with checkmarks
- "Choose Plan" buttons

#### Testimonials
- **2-column grid** of quote cards
- Avatar + Name + Title + Quote
- Glassmorphic cards with soft shadows

#### Footer
- **3-column layout**: Product, Company, Resources
- Social icons (Twitter, LinkedIn, GitHub)
- Newsletter signup (inline form)

---

## Responsive Behavior

### Desktop (≥1280px)
- Full layout with side panels
- 3-column grids for marketing page
- Spacious padding (`32px`)

### Tablet (768px - 1279px)
- Collapsible side panels (slide-in drawers)
- 2-column grids
- Reduced padding (`24px`)

### Mobile (≤767px)
- Single-column layout
- Bottom sheets instead of side panels
- Full-width Action Bar
- Reduced padding (`16px`)
- FAB for voice input

---

## Accessibility

- **WCAG AA compliance** minimum
- **Color contrast**: 4.5:1 for body text, 3:1 for large text
- **Focus indicators**: 2px royal blue outline
- **Keyboard navigation**: Tab order, Esc to close modals
- **Screen reader labels**: Descriptive aria-labels on all interactive elements
- **Reduced motion**: Respect `prefers-reduced-motion` media query

---

## Deliverables

### Design Files
1. **Figma Design System**
   - Color palette (variables)
   - Typography scale (text styles)
   - Component library (buttons, cards, inputs, etc.)
   - Icon set (custom line icons)

2. **Page Mockups**
   - Quillo App (desktop, tablet, mobile)
   - Marketing Landing Page (desktop, mobile)
   - Component variants (hover, active, disabled states)

3. **Interactive Prototype**
   - Click-through flow for primary user journey
   - Animated transitions and micro-interactions

4. **Design Tokens (JSON)**
   - Exportable for Tailwind CSS or CSS variables

---

## Figma AI Prompt Example

```
Create a premium, minimal UI design system for "Quillo," an AI Chief of Staff app. The design should feel executive-level: clean, glassmorphic, and trustworthy. Use a royal blue (#2563EB) and platinum (#F8FAFC) color palette with soft shadows and rounded-2xl corners. Include a conversation canvas, plan trace panel, toolchain timeline, profile drawer, and action bar. Typography should use Inter for body text and a display font for headlines. Deliver desktop and mobile mockups for the main app and a marketing landing page. Prioritize accessibility and thoughtful micro-interactions.
```

---

## Questions to Explore with Design
1. How can we visually distinguish "premium" tools vs. standard tools in the plan?
2. Should the profile drawer use a live markdown preview or a form-based editor?
3. What's the best way to show confidence levels without overwhelming the user?
4. How do we balance "AI intelligence" visuals without feeling overly techy?

---

## Next Steps
1. Generate initial mockups in Figma
2. Share with stakeholders for feedback
3. Iterate on component library
4. Prepare design tokens for Framer integration
5. Conduct usability testing with 5-10 beta users
