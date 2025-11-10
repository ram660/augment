# Journey UI Component Specifications

**Date:** 2025-11-10  
**Purpose:** Detailed specifications for React components in the journey-based UI

---

## 🧩 Component Hierarchy

```
JourneyPage
├── JourneyHeader
│   ├── HomeSelector
│   ├── JourneyTitle
│   └── ProgressIndicator
├── JourneyLayout
│   ├── JourneyTimeline (Left - 20%)
│   │   ├── TimelineHeader
│   │   ├── TimelineStep (repeated)
│   │   │   ├── StepIcon
│   │   │   ├── StepTitle
│   │   │   ├── StepProgress
│   │   │   └── SubStepList
│   │   └── TimelineFooter
│   ├── MainContentArea (Center - 60%)
│   │   ├── StepHeader
│   │   ├── ContentModeSelector
│   │   └── [Dynamic Content]
│   │       ├── ChatMode
│   │       │   ├── MessageList
│   │       │   │   └── MessageBubble (repeated)
│   │       │   ├── SuggestedActions
│   │       │   └── MessageInput
│   │       ├── GalleryMode
│   │       │   ├── GalleryToolbar
│   │       │   ├── ImageGrid
│   │       │   │   └── ImageCard (repeated)
│   │       │   └── ImageViewer
│   │       ├── FormMode
│   │       │   ├── FormSection (repeated)
│   │       │   └── FormActions
│   │       └── ReviewMode
│   │           ├── StepSummary (repeated)
│   │           └── ExportActions
│   └── ContextPanel (Right - 20%)
│       ├── CurrentStepSummary
│       ├── QuickStats
│       ├── QuickActions
│       └── RelatedInfo
```

---

## 📦 Component Specifications

### 1. JourneyPage (Container)

**File:** `homeview-frontend/app/(dashboard)/dashboard/journey/page.tsx`

**Purpose:** Main page container for journey-based interface

**Props:**
```typescript
interface JourneyPageProps {
  journeyId?: string; // Optional - load from URL or create new
}
```

**State:**
```typescript
interface JourneyPageState {
  journey: JourneyState | null;
  currentStepId: string;
  contentMode: 'chat' | 'gallery' | 'form' | 'review';
  isLoading: boolean;
  error: string | null;
}
```

**Responsibilities:**
- Load journey data from API
- Manage global journey state
- Handle navigation between steps
- Persist state changes
- Error handling

---

### 2. JourneyTimeline

**File:** `homeview-frontend/components/journey/JourneyTimeline.tsx`

**Purpose:** Left panel showing vertical timeline of all steps

**Props:**
```typescript
interface JourneyTimelineProps {
  journey: JourneyState;
  currentStepId: string;
  onStepClick: (stepId: string) => void;
  onStepEdit: (stepId: string) => void;
}
```

**Features:**
- Vertical scrollable timeline
- Step status indicators (icons + colors)
- Click to navigate to any step
- Expand/collapse sub-steps
- Progress bar at top
- Sticky header with journey name

**Visual States:**
```typescript
type StepStatus = 
  | 'not_started'    // ○ Gray
  | 'in_progress'    // → Purple
  | 'completed'      // ✓ Green
  | 'needs_attention' // ⚠️ Orange
  | 'blocked';       // 🔒 Red
```

**Example JSX:**
```tsx
<div className="journey-timeline">
  <TimelineHeader 
    title={journey.name}
    progress={journey.progress}
  />
  
  <div className="timeline-steps">
    {journey.steps.map(step => (
      <TimelineStep
        key={step.stepId}
        step={step}
        isActive={step.stepId === currentStepId}
        onClick={() => onStepClick(step.stepId)}
        onEdit={() => onStepEdit(step.stepId)}
      />
    ))}
  </div>
  
  <TimelineFooter
    estimatedCompletion={journey.estimatedCompletionDate}
  />
</div>
```

---

### 3. TimelineStep

**File:** `homeview-frontend/components/journey/TimelineStep.tsx`

**Purpose:** Individual step in timeline

**Props:**
```typescript
interface TimelineStepProps {
  step: JourneyStep;
  isActive: boolean;
  onClick: () => void;
  onEdit: () => void;
}
```

**Features:**
- Status icon with color coding
- Step number and title
- Progress indicator (if in progress)
- Sub-step list (expandable)
- Edit button on hover
- Tooltip with step details

**Example JSX:**
```tsx
<div 
  className={`timeline-step ${isActive ? 'active' : ''} ${step.status}`}
  onClick={onClick}
>
  <div className="step-indicator">
    <StepIcon status={step.status} />
    <div className="step-line" />
  </div>
  
  <div className="step-content">
    <div className="step-header">
      <span className="step-number">{step.stepNumber}</span>
      <span className="step-title">{step.name}</span>
      {step.status === 'in_progress' && (
        <span className="step-progress">{step.progress}%</span>
      )}
    </div>
    
    {step.subSteps && step.subSteps.length > 0 && (
      <SubStepList subSteps={step.subSteps} />
    )}
    
    <button 
      className="step-edit-btn"
      onClick={(e) => { e.stopPropagation(); onEdit(); }}
    >
      Edit
    </button>
  </div>
</div>
```

---

### 4. ChatMode

**File:** `homeview-frontend/components/journey/ChatMode.tsx`

**Purpose:** Chat interface with step context

**Props:**
```typescript
interface ChatModeProps {
  journeyId: string;
  stepId: string;
  conversationId: string;
  onImageUpload: (files: File[]) => void;
  onActionClick: (action: SuggestedAction) => void;
}
```

**Features:**
- Message history with step context
- Image attachments inline
- Suggested actions as buttons
- File upload (drag & drop)
- Voice input (optional)
- Auto-scroll to latest message
- Loading states for AI responses

**State:**
```typescript
interface ChatModeState {
  messages: Message[];
  isLoading: boolean;
  inputValue: string;
  attachments: File[];
}
```

**Example JSX:**
```tsx
<div className="chat-mode">
  <div className="chat-header">
    <h3>{stepTitle}</h3>
    <span className="step-context">Step {stepNumber} of {totalSteps}</span>
  </div>
  
  <MessageList 
    messages={messages}
    isLoading={isLoading}
  />
  
  {suggestedActions.length > 0 && (
    <SuggestedActions 
      actions={suggestedActions}
      onActionClick={onActionClick}
    />
  )}
  
  <MessageInput
    value={inputValue}
    onChange={setInputValue}
    onSend={handleSend}
    onFileUpload={onImageUpload}
    attachments={attachments}
  />
</div>
```

---

### 5. GalleryMode

**File:** `homeview-frontend/components/journey/GalleryMode.tsx`

**Purpose:** Image management and comparison

**Props:**
```typescript
interface GalleryModeProps {
  journeyId: string;
  stepId: string;
  images: ImageAttachment[];
  onImageUpload: (files: File[]) => void;
  onImageDelete: (imageId: string) => void;
  onImageReplace: (imageId: string, file: File) => void;
  onImageAnnotate: (imageId: string, annotation: Annotation) => void;
}
```

**Features:**
- Grid view of all images
- Lightbox for full-size viewing
- Before/after comparison slider
- Image annotations
- Replace/edit/delete actions
- Filter by step
- Download/export options
- Generate mockup button

**View Modes:**
- Grid (default)
- List with details
- Comparison (side-by-side)
- Timeline (chronological)

**Example JSX:**
```tsx
<div className="gallery-mode">
  <GalleryToolbar
    viewMode={viewMode}
    onViewModeChange={setViewMode}
    onUpload={onImageUpload}
    onGenerateMockup={handleGenerateMockup}
  />
  
  <ImageGrid viewMode={viewMode}>
    {images.map(image => (
      <ImageCard
        key={image.id}
        image={image}
        onView={() => setSelectedImage(image)}
        onDelete={() => onImageDelete(image.id)}
        onReplace={(file) => onImageReplace(image.id, file)}
        onAnnotate={(annotation) => onImageAnnotate(image.id, annotation)}
      />
    ))}
  </ImageGrid>
  
  {selectedImage && (
    <ImageViewer
      image={selectedImage}
      onClose={() => setSelectedImage(null)}
      onNext={handleNextImage}
      onPrevious={handlePreviousImage}
    />
  )}
</div>
```

---

### 6. ImageCard

**File:** `homeview-frontend/components/journey/ImageCard.tsx`

**Purpose:** Individual image card in gallery

**Props:**
```typescript
interface ImageCardProps {
  image: ImageAttachment;
  onView: () => void;
  onDelete: () => void;
  onReplace: (file: File) => void;
  onAnnotate: (annotation: Annotation) => void;
}
```

**Features:**
- Thumbnail with lazy loading
- Hover overlay with actions
- Status badges (AI-generated, edited, etc.)
- Quick annotations
- Drag to reorder
- Selection checkbox

**Example JSX:**
```tsx
<div className="image-card" onClick={onView}>
  <div className="image-thumbnail">
    <img 
      src={image.thumbnailUrl} 
      alt={image.filename}
      loading="lazy"
    />
    
    {image.analysis && (
      <div className="image-badges">
        <Badge>{image.analysis.style}</Badge>
        {image.isGenerated && <Badge variant="ai">AI Generated</Badge>}
      </div>
    )}
  </div>
  
  <div className="image-info">
    <span className="image-filename">{image.filename}</span>
    <span className="image-date">{formatDate(image.uploadedAt)}</span>
  </div>
  
  <div className="image-actions">
    <button onClick={(e) => { e.stopPropagation(); onDelete(); }}>
      🗑️ Delete
    </button>
    <button onClick={(e) => { e.stopPropagation(); /* open replace */ }}>
      🔄 Replace
    </button>
    <button onClick={(e) => { e.stopPropagation(); /* open annotate */ }}>
      ✏️ Annotate
    </button>
  </div>
</div>
```

---

### 7. ContextPanel

**File:** `homeview-frontend/components/journey/ContextPanel.tsx`

**Purpose:** Right panel with quick reference and actions

**Props:**
```typescript
interface ContextPanelProps {
  journey: JourneyState;
  currentStep: JourneyStep;
  onActionClick: (action: string) => void;
}
```

**Sections:**
1. Current Step Summary
2. Quick Stats
3. Quick Actions
4. Related Information

**Example JSX:**
```tsx
<div className="context-panel">
  <CurrentStepSummary
    step={currentStep}
    totalSteps={journey.steps.length}
  />
  
  <QuickStats
    images={currentStep.images.length}
    budget={journey.collectedData.budget}
    timeline={journey.collectedData.timeline}
    decisions={currentStep.decisions.length}
  />
  
  <QuickActions
    actions={[
      { id: 'upload', label: 'Upload Image', icon: '📷' },
      { id: 'generate', label: 'Generate Mockup', icon: '🎨' },
      { id: 'ask', label: 'Ask Question', icon: '💬' },
      { id: 'summary', label: 'View Summary', icon: '📊' },
    ]}
    onActionClick={onActionClick}
  />
  
  <RelatedInfo
    suggestions={currentStep.suggestions}
    relatedSteps={getRelatedSteps(currentStep)}
  />
</div>
```

---

## 🎨 Styling Guidelines

### Tailwind Classes

**Timeline:**
```css
.journey-timeline: bg-white border-r border-gray-200 h-full overflow-y-auto
.timeline-step: p-4 cursor-pointer hover:bg-gray-50 transition-colors
.timeline-step.active: bg-purple-50 border-l-4 border-purple-600
.step-indicator: flex items-center gap-2
```

**Chat Mode:**
```css
.chat-mode: flex flex-col h-full
.message-list: flex-1 overflow-y-auto p-4 space-y-4
.message-bubble: max-w-2xl rounded-lg p-4 shadow-sm
.message-bubble.user: bg-purple-100 ml-auto
.message-bubble.assistant: bg-white border border-gray-200
```

**Gallery Mode:**
```css
.gallery-mode: flex flex-col h-full
.image-grid: grid grid-cols-3 gap-4 p-4
.image-card: relative rounded-lg overflow-hidden shadow-md hover:shadow-lg
.image-thumbnail: aspect-square bg-gray-100
```

---

## 🔌 API Integration

### Required Endpoints

```typescript
// Journey Management
GET    /api/journey/{journeyId}
POST   /api/journey/start
PUT    /api/journey/{journeyId}/step/{stepId}
POST   /api/journey/{journeyId}/step/{stepId}/complete

// Image Management
POST   /api/journey/{journeyId}/step/{stepId}/images
DELETE /api/journey/{journeyId}/images/{imageId}
PUT    /api/journey/{journeyId}/images/{imageId}
GET    /api/journey/{journeyId}/images

// Chat Integration
POST   /api/chat/stream-multipart (existing)
GET    /api/chat/conversations/{conversationId}/history (existing)
```

---

## 📱 Responsive Design

### Breakpoints
```typescript
sm: 640px   // Mobile
md: 768px   // Tablet
lg: 1024px  // Desktop
xl: 1280px  // Large Desktop
```

### Layout Adaptations

**Mobile (< 768px):**
- Stack panels vertically
- Timeline becomes bottom sheet
- Context panel becomes modal
- Full-width main content

**Tablet (768px - 1024px):**
- Timeline: 25%
- Main: 75%
- Context panel: overlay on demand

**Desktop (> 1024px):**
- Timeline: 20%
- Main: 60%
- Context: 20%

---

**Status:** Specifications Complete - Ready for Implementation

