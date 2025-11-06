# HomeView AI - UI/UX Vision Part 2
## Technical Implementation & Frontend Architecture

---

## 🛠️ Technology Stack

### Frontend Framework
**Next.js 14+ (App Router)**

**Why Next.js?**
- ✅ Server-side rendering for SEO
- ✅ API routes for backend integration
- ✅ Image optimization built-in
- ✅ File-based routing
- ✅ React Server Components
- ✅ Streaming and Suspense support

**Alternative:** Vite + React (faster dev, simpler)

### UI Framework
**Tailwind CSS + shadcn/ui**

**Why?**
- ✅ Rapid prototyping
- ✅ Consistent design system
- ✅ Accessible components
- ✅ Customizable
- ✅ Production-ready

### State Management
**Zustand + React Query**

**Why?**
- ✅ Simple and lightweight
- ✅ Server state management (React Query)
- ✅ Client state management (Zustand)
- ✅ Automatic caching and refetching

### Real-Time Features
**Socket.io or Supabase Realtime**

**Why?**
- ✅ Real-time collaboration
- ✅ Live updates
- ✅ Presence indicators
- ✅ Chat functionality

### AI Integration
**Vercel AI SDK**

**Why?**
- ✅ Streaming responses
- ✅ Function calling
- ✅ Multi-modal support
- ✅ Built for Next.js

### Image Handling
**Next/Image + Cloudinary/GCS**

**Why?**
- ✅ Automatic optimization
- ✅ Lazy loading
- ✅ Responsive images
- ✅ CDN delivery

---

## 📁 Frontend Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth routes
│   │   ├── login/
│   │   ├── register/
│   │   └── layout.tsx
│   ├── (dashboard)/              # Main app routes
│   │   ├── homes/
│   │   │   ├── [homeId]/
│   │   │   │   ├── page.tsx      # Home overview
│   │   │   │   ├── chat/         # Chat interface
│   │   │   │   ├── design/       # Design studio
│   │   │   │   ├── projects/     # Project management
│   │   │   │   └── rooms/
│   │   │   │       └── [roomId]/
│   │   │   └── page.tsx          # Homes list
│   │   ├── community/            # Social feed
│   │   ├── marketplace/          # Agent marketplace
│   │   ├── products/             # Product catalog
│   │   └── layout.tsx            # Dashboard layout
│   ├── api/                      # API routes (proxy to backend)
│   │   ├── chat/
│   │   ├── design/
│   │   └── upload/
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Landing page
│
├── components/                   # React components
│   ├── ui/                       # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── chat/                     # Chat components
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageInput.tsx
│   │   ├── AudioOverview.tsx
│   │   └── SuggestionsPanel.tsx
│   ├── design/                   # Design studio components
│   │   ├── DesignCanvas.tsx
│   │   ├── StyleSelector.tsx
│   │   ├── BeforeAfter.tsx
│   │   ├── TransformControls.tsx
│   │   └── VariationGrid.tsx
│   ├── home/                     # Home management
│   │   ├── HomeContextPanel.tsx
│   │   ├── RoomCard.tsx
│   │   ├── FloorPlanViewer.tsx
│   │   └── DigitalTwinView.tsx
│   ├── projects/                 # Project components
│   │   ├── DIYPlanner.tsx
│   │   ├── ContractorMatcher.tsx
│   │   ├── CostEstimator.tsx
│   │   ├── MaterialsList.tsx
│   │   └── ProgressTracker.tsx
│   ├── products/                 # Product components
│   │   ├── ProductCard.tsx
│   │   ├── ProductFinder.tsx
│   │   ├── FitValidator.tsx
│   │   └── ShoppingList.tsx
│   ├── community/                # Community components
│   │   ├── Feed.tsx
│   │   ├── PostCard.tsx
│   │   ├── AgentCard.tsx
│   │   └── UserProfile.tsx
│   └── shared/                   # Shared components
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       ├── LoadingStates.tsx
│       └── ErrorBoundary.tsx
│
├── lib/                          # Utilities and helpers
│   ├── api/                      # API client
│   │   ├── client.ts             # Axios/Fetch wrapper
│   │   ├── chat.ts               # Chat API
│   │   ├── design.ts             # Design API
│   │   ├── homes.ts              # Homes API
│   │   └── products.ts           # Products API
│   ├── hooks/                    # Custom React hooks
│   │   ├── useChat.ts
│   │   ├── useDesign.ts
│   │   ├── useHome.ts
│   │   ├── useAuth.ts
│   │   └── useRealtime.ts
│   ├── stores/                   # Zustand stores
│   │   ├── authStore.ts
│   │   ├── homeStore.ts
│   │   ├── chatStore.ts
│   │   └── designStore.ts
│   ├── utils/                    # Utility functions
│   │   ├── formatting.ts
│   │   ├── validation.ts
│   │   └── constants.ts
│   └── types/                    # TypeScript types
│       ├── api.ts
│       ├── home.ts
│       ├── chat.ts
│       └── design.ts
│
├── public/                       # Static assets
│   ├── images/
│   ├── icons/
│   └── fonts/
│
├── styles/                       # Global styles
│   └── globals.css
│
├── .env.local                    # Environment variables
├── next.config.js                # Next.js configuration
├── tailwind.config.js            # Tailwind configuration
├── tsconfig.json                 # TypeScript configuration
└── package.json                  # Dependencies
```

---

## 🎯 Key Component Implementations

### 1. Unified Chat Interface

```typescript
// components/chat/ChatInterface.tsx
'use client';

import { useState } from 'react';
import { useChat } from '@/lib/hooks/useChat';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import SuggestionsPanel from './SuggestionsPanel';
import AudioOverview from './AudioOverview';

export default function ChatInterface({ homeId }: { homeId: string }) {
  const { messages, sendMessage, isLoading, suggestions } = useChat(homeId);
  const [mode, setMode] = useState<'text' | 'audio'>('text');

  return (
    <div className="flex flex-col h-full">
      {/* Mode Switcher */}
      <div className="flex gap-2 p-4 border-b">
        <button
          onClick={() => setMode('text')}
          className={mode === 'text' ? 'active' : ''}
        >
          💬 Text Chat
        </button>
        <button
          onClick={() => setMode('audio')}
          className={mode === 'audio' ? 'active' : ''}
        >
          🎙️ Audio Overview
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {mode === 'text' ? (
          <>
            <MessageList messages={messages} />
            <MessageInput onSend={sendMessage} isLoading={isLoading} />
          </>
        ) : (
          <AudioOverview homeId={homeId} />
        )}
      </div>

      {/* AI Suggestions */}
      <SuggestionsPanel suggestions={suggestions} />
    </div>
  );
}
```

### 2. Design Studio Canvas

```typescript
// components/design/DesignCanvas.tsx
'use client';

import { useState } from 'react';
import { useDesign } from '@/lib/hooks/useDesign';
import BeforeAfter from './BeforeAfter';
import StyleSelector from './StyleSelector';
import TransformControls from './TransformControls';
import VariationGrid from './VariationGrid';

export default function DesignCanvas({ roomId, imageUrl }: Props) {
  const {
    variations,
    generateVariations,
    isGenerating,
    selectedStyle
  } = useDesign(roomId);

  const [transformParams, setTransformParams] = useState({
    style: 'modern',
    keep: ['layout', 'windows'],
    change: ['flooring', 'paint', 'furniture'],
    budget: { min: 5000, max: 10000 }
  });

  return (
    <div className="grid grid-cols-12 gap-4 h-full">
      {/* Left Panel - Controls */}
      <div className="col-span-3 space-y-4">
        <StyleSelector
          selected={transformParams.style}
          onChange={(style) => setTransformParams({ ...transformParams, style })}
        />
        <TransformControls
          params={transformParams}
          onChange={setTransformParams}
        />
        <button
          onClick={() => generateVariations(imageUrl, transformParams)}
          disabled={isGenerating}
        >
          {isGenerating ? 'Generating...' : 'Generate Variations'}
        </button>
      </div>

      {/* Center Panel - Main View */}
      <div className="col-span-6">
        <BeforeAfter
          before={imageUrl}
          after={variations[0]?.url}
        />
      </div>

      {/* Right Panel - Variations */}
      <div className="col-span-3">
        <VariationGrid
          variations={variations}
          onSelect={(variation) => {/* ... */}}
        />
      </div>
    </div>
  );
}
```

### 3. Home Context Panel

```typescript
// components/home/HomeContextPanel.tsx
'use client';

import { useHome } from '@/lib/hooks/useHome';
import RoomCard from './RoomCard';
import FloorPlanViewer from './FloorPlanViewer';

export default function HomeContextPanel({ homeId }: { homeId: string }) {
  const { home, rooms, projects, isLoading } = useHome(homeId);

  if (isLoading) return <LoadingSkeleton />;

  return (
    <div className="w-80 border-r bg-gray-50 overflow-y-auto">
      {/* Home Overview */}
      <div className="p-4 border-b">
        <h2 className="text-xl font-bold">{home.name}</h2>
        <p className="text-sm text-gray-600">
          {home.total_rooms} rooms • {home.total_sqft} sq ft
        </p>
      </div>

      {/* Floor Plan */}
      <div className="p-4 border-b">
        <h3 className="font-semibold mb-2">Floor Plan</h3>
        <FloorPlanViewer floorPlanUrl={home.floor_plan_url} />
      </div>

      {/* Rooms */}
      <div className="p-4 border-b">
        <h3 className="font-semibold mb-2">Rooms</h3>
        <div className="space-y-2">
          {rooms.map((room) => (
            <RoomCard key={room.id} room={room} />
          ))}
        </div>
      </div>

      {/* Active Projects */}
      <div className="p-4">
        <h3 className="font-semibold mb-2">Active Projects</h3>
        <div className="space-y-2">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-4 border-t">
        <button className="w-full btn-primary">
          + Add Room
        </button>
      </div>
    </div>
  );
}
```

### 4. DIY Planner

```typescript
// components/projects/DIYPlanner.tsx
'use client';

import { useState } from 'react';
import { useDIYPlan } from '@/lib/hooks/useDIYPlan';
import MaterialsList from './MaterialsList';
import ProgressTracker from './ProgressTracker';

export default function DIYPlanner({ projectId }: { projectId: string }) {
  const { plan, updateProgress, isLoading } = useDIYPlan(projectId);
  const [activeTab, setActiveTab] = useState<'materials' | 'steps' | 'progress'>('materials');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">{plan.title}</h1>
          <p className="text-gray-600">
            💰 ${plan.total_cost} • ⏱️ {plan.estimated_days} days
          </p>
        </div>
        <div className="flex gap-2">
          <button>📥 Export PDF</button>
          <button>🔗 Share</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('materials')}
            className={activeTab === 'materials' ? 'active' : ''}
          >
            📦 Materials
          </button>
          <button
            onClick={() => setActiveTab('steps')}
            className={activeTab === 'steps' ? 'active' : ''}
          >
            🛠️ Steps
          </button>
          <button
            onClick={() => setActiveTab('progress')}
            className={activeTab === 'progress' ? 'active' : ''}
          >
            📊 Progress
          </button>
        </nav>
      </div>

      {/* Content */}
      <div>
        {activeTab === 'materials' && (
          <MaterialsList materials={plan.materials} />
        )}
        {activeTab === 'steps' && (
          <StepsList steps={plan.steps} onComplete={updateProgress} />
        )}
        {activeTab === 'progress' && (
          <ProgressTracker progress={plan.progress} />
        )}
      </div>
    </div>
  );
}
```

---

## 🔌 API Integration Layer

### API Client Setup

```typescript
// lib/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', data.access_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return apiClient(error.config);
        } catch {
          // Redirect to login
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Chat API

```typescript
// lib/api/chat.ts
import apiClient from './client';

export const chatAPI = {
  sendMessage: async (homeId: string, message: string) => {
    const { data } = await apiClient.post('/api/v1/chat/message', {
      home_id: homeId,
      message,
    });
    return data;
  },

  getConversations: async (homeId: string) => {
    const { data } = await apiClient.get(`/api/v1/chat/conversations`, {
      params: { home_id: homeId },
    });
    return data;
  },

  generateAudioOverview: async (homeId: string, topic: string) => {
    const { data } = await apiClient.post('/api/v1/chat/audio-overview', {
      home_id: homeId,
      topic,
    });
    return data;
  },
};
```

---

*Continued in FRONTEND_IMPLEMENTATION_PLAN.md...*

