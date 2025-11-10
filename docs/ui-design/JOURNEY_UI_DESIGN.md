# Journey-Based UI/UX Design - HomeView AI

**Date:** 2025-11-10  
**Purpose:** Comprehensive UI/UX design for multimodal journey system with step navigation, image management, and progress tracking

---

## 🎯 Design Goals

### Core Principles
1. **Resume Anywhere** - Users can continue from where they left off
2. **Edit Previous Steps** - Full ability to go back and modify any step
3. **Multimodal First** - Images, videos, documents are first-class citizens
4. **Progress Visibility** - Always show where user is in their journey
5. **Non-Linear Navigation** - Jump to any step, not forced sequential
6. **Context Preservation** - All data from previous steps available

### User Needs (from Test Scenarios)
- Upload and manage multiple images per step
- See visual timeline of their journey
- Edit/replace images from previous steps
- Resume multi-week projects
- Compare before/after states
- Track decisions and changes
- Export journey data

---

## 🏗️ Architecture Overview

### Three-Panel Layout

```
┌─────────────────────────────────────────────────────────────┐
│                        Header                                │
│  🏠 Home Selector | Journey: Kitchen Renovation | Progress  │
└─────────────────────────────────────────────────────────────┘
┌──────────────┬──────────────────────────┬──────────────────┐
│              │                          │                  │
│   Journey    │    Main Content Area     │   Context Panel  │
│   Timeline   │                          │                  │
│   (Left)     │    (Center - 60%)        │   (Right - 20%)  │
│              │                          │                  │
│   (20%)      │  - Chat Interface        │  - Current Step  │
│              │  - Image Gallery         │  - Quick Actions │
│              │  - Step Content          │  - Related Info  │
│              │  - Forms/Inputs          │  - Suggestions   │
│              │                          │                  │
│  Step 1 ✓    │                          │  📸 Images: 3    │
│  Step 2 ✓    │                          │  💰 Budget: $45K │
│  Step 3 →    │                          │  ⏱️ Week 2/7     │
│  Step 4      │                          │                  │
│  Step 5      │                          │                  │
│              │                          │                  │
└──────────────┴──────────────────────────┴──────────────────┘
```

---

## 📱 Component Breakdown

### 1. Journey Timeline (Left Panel)

**Purpose:** Visual navigation through all journey steps

**Features:**
- Vertical timeline with step indicators
- Status icons (✓ complete, → in progress, ○ not started, ⚠️ needs attention)
- Click any step to jump to it
- Expandable sub-steps
- Progress percentage
- Estimated time remaining

**Visual Design:**
```
┌─────────────────────────┐
│ Kitchen Renovation      │
│ ━━━━━━━━━━━━━━━━ 40%   │
├─────────────────────────┤
│ ✓ 1. Initial Setup      │
│   └─ Photos uploaded    │
│   └─ Goals defined      │
│                         │
│ ✓ 2. Design Vision      │
│   └─ Style selected     │
│   └─ 3 mockups created  │
│                         │
│ → 3. Material Selection │ ← Current
│   └─ Cabinets chosen    │
│   └─ Countertops (todo) │
│                         │
│ ○ 4. Cost Estimation    │
│                         │
│ ○ 5. Contractor Search  │
│                         │
│ ○ 6. Project Planning   │
└─────────────────────────┘
```

**State Management:**
```typescript
interface JourneyStep {
  stepId: string;
  name: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'needs_attention';
  progress: number; // 0-100
  subSteps: SubStep[];
  data: Record<string, any>;
  images: ImageAttachment[];
  createdAt: string;
  completedAt?: string;
}
```

---

### 2. Main Content Area (Center Panel)

**Purpose:** Primary interaction area - adapts based on current step

**Modes:**
1. **Chat Mode** - Conversational interface (default)
2. **Gallery Mode** - Image management and comparison
3. **Form Mode** - Structured data entry
4. **Review Mode** - Summary and decision review

#### 2.1 Chat Mode (Default)

**Features:**
- Message history with step context
- Image attachments inline
- Suggested actions as buttons
- Quick jump to related steps
- AI responses with rich media

**Layout:**
```
┌──────────────────────────────────────┐
│  Step 3: Material Selection          │
├──────────────────────────────────────┤
│                                      │
│  💬 Chat History                     │
│  ┌────────────────────────────────┐ │
│  │ You: I love option 2! Can you  │ │
│  │ help me find actual products?  │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ AI: Perfect choice! I've       │ │
│  │ searched for current prices... │ │
│  │                                │ │
│  │ 🗄️ Cabinets - White Shaker    │ │
│  │ [Product Cards with Images]    │ │
│  │                                │ │
│  │ [Select Option] [Compare]      │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ 💬 Type your message...        │ │
│  │ 📎 📷 🎤                       │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

#### 2.2 Gallery Mode

**Features:**
- Grid view of all images for current step
- Before/after comparison slider
- Image annotations
- Replace/edit/delete images
- AI-generated mockups
- Download/export options

**Layout:**
```
┌──────────────────────────────────────┐
│  📸 Images - Step 2: Design Vision   │
├──────────────────────────────────────┤
│  [Grid View] [List View] [Compare]   │
│                                      │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │ 📷  │ │ 📷  │ │ 🎨  │ │ 🎨  │   │
│  │ Cur │ │ Cur │ │ Gen │ │ Gen │   │
│  │ rent│ │ rent│ │ erat│ │ erat│   │
│  │     │ │     │ │ ed  │ │ ed  │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│  Original  Original  Option A Option B│
│  Kitchen   Cabinets  Modern   Warm   │
│                                      │
│  [+ Upload More] [Generate Mockup]   │
│                                      │
│  Selected: Option B - Warm Farmhouse │
│  [Edit] [Replace] [Set as Primary]   │
└──────────────────────────────────────┘
```

#### 2.3 Form Mode

**Features:**
- Structured data entry
- Auto-save on change
- Validation feedback
- Pre-filled from previous steps
- Smart suggestions

**Example - Budget Form:**
```
┌──────────────────────────────────────┐
│  💰 Budget & Cost Estimation         │
├──────────────────────────────────────┤
│                                      │
│  Target Budget: [$50,000]            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                      │
│  Materials:                          │
│  ├─ Cabinets:      $10,000 ✓        │
│  ├─ Countertops:   $3,200  ✓        │
│  ├─ Backsplash:    $1,100  ✓        │
│  ├─ Flooring:      [Enter amount]    │
│  └─ Appliances:    [Enter amount]    │
│                                      │
│  Labor:                              │
│  ├─ Demolition:    $1,040  (auto)   │
│  ├─ Electrical:    $2,280  (auto)   │
│  └─ ...                              │
│                                      │
│  Total: $17,620 / $50,000 (35%)     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                      │
│  [Save & Continue] [Recalculate]     │
└──────────────────────────────────────┘
```

---

### 3. Context Panel (Right Panel)

**Purpose:** Quick reference and actions for current step

**Sections:**

#### 3.1 Current Step Summary
```
┌──────────────────────┐
│ Step 3 of 10         │
│ Material Selection   │
│ ━━━━━━━━━━━━━━ 60%  │
│                      │
│ Started: Nov 8       │
│ Est. Complete: Nov 10│
└──────────────────────┘
```

#### 3.2 Quick Stats
```
┌──────────────────────┐
│ 📸 Images: 7         │
│ 💰 Budget: $17K/50K  │
│ ⏱️ Time: Week 2/7    │
│ ✓ Decisions: 3       │
└──────────────────────┘
```

#### 3.3 Quick Actions
```
┌──────────────────────┐
│ [📷 Upload Image]    │
│ [🎨 Generate Mockup] │
│ [💬 Ask Question]    │
│ [📊 View Summary]    │
│ [⬅️ Previous Step]   │
│ [➡️ Next Step]       │
└──────────────────────┘
```

#### 3.4 Related Information
```
┌──────────────────────┐
│ 💡 Suggestions       │
│ • Consider quartz    │
│ • Check lead times   │
│ • Compare 3 quotes   │
│                      │
│ 🔗 Related Steps     │
│ • Step 2: Design     │
│ • Step 4: Costs      │
└──────────────────────┘
```

---

## 🎨 Visual Design System

### Color Palette
```
Primary:   #667eea (Purple) - Journey progress, CTAs
Secondary: #764ba2 (Deep Purple) - Accents
Success:   #10b981 (Green) - Completed steps
Warning:   #f59e0b (Orange) - Needs attention
Error:     #ef4444 (Red) - Errors
Info:      #3b82f6 (Blue) - Information
Neutral:   #6b7280 (Gray) - Text, borders
```

### Typography
```
Headings:  Inter, 600-700 weight
Body:      Inter, 400-500 weight
Code:      Fira Code, 400 weight
```

### Spacing
```
xs:  4px
sm:  8px
md:  16px
lg:  24px
xl:  32px
2xl: 48px
```

---

## 🔄 State Management

### Journey State Structure
```typescript
interface JourneyState {
  journeyId: string;
  userId: string;
  templateId: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'paused';
  
  // Progress
  currentStepId: string;
  completedSteps: string[];
  progress: number; // 0-100
  
  // Steps with full data
  steps: JourneyStep[];
  
  // Metadata
  startedAt: string;
  lastActivityAt: string;
  estimatedCompletionDate: string;
  
  // Collected data across all steps
  collectedData: {
    images: ImageAttachment[];
    decisions: Decision[];
    budget: BudgetData;
    timeline: TimelineData;
    contractors: ContractorData[];
  };
}
```

### Image Management
```typescript
interface ImageAttachment {
  id: string;
  stepId: string;
  url: string;
  thumbnailUrl: string;
  filename: string;
  contentType: string;
  size: number;
  uploadedAt: string;
  
  // AI Analysis
  analysis?: {
    description: string;
    detectedMaterials: string[];
    detectedFixtures: string[];
    style: string;
    condition: string;
  };
  
  // User annotations
  annotations?: {
    label: string;
    notes: string;
    tags: string[];
  };
  
  // Relationships
  relatedImages?: string[]; // IDs of related images (before/after)
  replacedBy?: string; // ID of image that replaced this one
}
```

---

## 📊 Key User Flows

### Flow 1: Resume Journey
```
1. User logs in
2. Dashboard shows "Continue Kitchen Renovation" card
3. Click → Opens journey at last active step
4. Timeline shows all previous steps completed
5. Context panel shows summary of decisions so far
6. User can continue or jump to any previous step
```

### Flow 2: Edit Previous Step
```
1. User is on Step 5
2. Realizes they want to change cabinet selection from Step 3
3. Clicks "Step 3" in timeline
4. Main area loads Step 3 content
5. Shows previous selections with [Edit] button
6. User changes selection
7. System asks: "Update dependent steps?" (Steps 4, 5)
8. User confirms → Steps 4-5 marked "needs attention"
9. User reviews and updates affected steps
```

### Flow 3: Image Management
```
1. User uploads kitchen photo in Step 1
2. AI analyzes: "1990s oak cabinets, laminate counters"
3. In Step 2, user generates 3 design mockups
4. In Step 3, user uploads product photos
5. Gallery mode shows all images organized by step
6. User can compare: Original vs Mockup vs Product
7. User annotates: "This is the one we want!"
8. Export journey → PDF with all images and decisions
```

---

## 🚀 Implementation Priority

### Phase 1: Core Journey UI (Week 1)
- [ ] Journey timeline component
- [ ] Step navigation
- [ ] Basic chat interface with step context
- [ ] Progress tracking
- [ ] State persistence

### Phase 2: Image Management (Week 2)
- [ ] Image upload/display in steps
- [ ] Gallery mode
- [ ] Before/after comparison
- [ ] Image annotations
- [ ] Replace/edit functionality

### Phase 3: Advanced Features (Week 3)
- [ ] Form mode for structured data
- [ ] Review mode with summaries
- [ ] Export journey data
- [ ] Dependency tracking between steps
- [ ] Smart suggestions based on journey state

### Phase 4: Polish & Testing (Week 4)
- [ ] Responsive design
- [ ] Animations and transitions
- [ ] Error handling
- [ ] Performance optimization
- [ ] User testing with test scenarios

---

## 📝 Next Steps

1. **Create React Components** - Build reusable components for timeline, steps, gallery
2. **Implement State Management** - Use Zustand for journey state
3. **Backend API Updates** - Ensure journey endpoints support all UI needs
4. **Test with Scenarios** - Use CUSTOMER_JOURNEY_TEST_SCENARIOS.md for testing

---

**Status:** Design Complete - Ready for Implementation

