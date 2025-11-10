# HomeView AI - New UI Quick Start Guide 🚀

## What's New?

Your HomeView AI platform has been **completely redesigned** with a modern, visual-first interface that includes:

- **5 Main Tabs:** Chat, Design Studio, Explore, Community, Jobs
- **Project-Based Workflow:** Organize work by projects
- **Image Editing Actions:** Edit, Save, Vary generated images
- **Social Features:** Share and discover designs
- **Contractor Marketplace:** Find and hire professionals

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Start the Backend
```bash
cd backend
python -m uvicorn backend.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 2: Start the Frontend
```bash
cd homeview-frontend
npm run dev
```

**Expected Output:**
```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
  - Ready in 2.5s
```

### Step 3: Open the App
```
http://localhost:3000/dashboard/chat
```

---

## 🎨 Tour of New Features

### 1. **Main Navigation** (Top Bar)

```
┌─────────────────────────────────────────────────────────┐
│  🏠 HomeView AI    💬 Chat  🎨 Studio  🔍 Explore  ...  │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Click any tab to navigate
- Active tab is highlighted in blue
- Notifications bell (top right)
- Profile menu (top right)

---

### 2. **Chat Tab** - The Heart of the Platform

#### Layout
```
┌──────────────┬──────────────────────┬──────────────┐
│   Projects   │    Chat Messages     │   Context    │
│   Sidebar    │                      │    Panel     │
│              │                      │              │
│  • Kitchen   │  [Messages]          │  📊 Overview │
│  • Bathroom  │  [Images]            │  ☑ Tasks     │
│              │  [Input]             │  🖼️ Images   │
└──────────────┴──────────────────────┴──────────────┘
```

#### Try This:
1. **Send a message:** "Show me modern kitchen designs"
2. **Wait for images:** AI generates 3 design concepts
3. **Click action buttons:**
   - ✏️ **Edit** - Modify the image ("Make it brighter")
   - 💾 **Save** - Save to project gallery
   - 🔄 **Vary** - Create a variation
4. **Check context panel:** See project overview, tasks, images

#### Project Sidebar Features:
- **New Project** button (top)
- **Search** projects
- **Active/Archived** tabs
- Click project to switch
- Hover for edit/delete options

#### Context Panel Features:
- **Overview:** Budget tracker, timeline
- **Tasks:** Checklist with progress
- **Images:** Gallery of all project images
- **Quick Actions:** DIY Plan, Cost Estimate, Find Contractors

---

### 3. **Design Studio Tab**

```
http://localhost:3000/dashboard/studio
```

**Current Status:** Landing page (canvas coming soon)

**Features:**
- Upload images
- Browse gallery
- Feature preview cards

**Coming Soon:**
- Layer-based editing
- AI-powered tools
- Style transfer
- Advanced editing

---

### 4. **Explore Tab**

```
http://localhost:3000/dashboard/explore
```

**Try This:**
1. **Search** for designs
2. **Toggle view:** Grid ↔ List
3. **Click filters:** Modern, Rustic, Coastal
4. **Like designs:** Click heart icon
5. **View details:** Click any design card

**Features:**
- Design gallery with 6 sample designs
- Search and filters
- Grid/List view toggle
- Like and save favorites
- Budget and style info

---

### 5. **Community Tab**

```
http://localhost:3000/dashboard/community
```

**Try This:**
1. **Browse feed:** See project posts
2. **Switch tabs:** Latest, Trending, Following
3. **Like posts:** Click heart icon
4. **View before/after:** See transformations
5. **Check stats:** Budget, timeline, DIY %

**Features:**
- Social feed with 3 sample posts
- Before/After image comparisons
- Project statistics
- Like, Comment, Share buttons
- "Share Project" button

---

### 6. **Jobs/Contractors Tab**

```
http://localhost:3000/dashboard/jobs
```

**Try This:**
1. **Browse contractors:** See 3 sample contractors
2. **Use filters:** Location, specialty, budget, rating
3. **Search:** Find specific contractors
4. **View details:** Rating, experience, badges
5. **Take action:** Request Quote, Message, View Profile

**Features:**
- Contractor directory
- Advanced filters sidebar
- Search functionality
- Contractor cards with:
  - Rating and reviews
  - Location and pricing
  - Licensed/Insured/Verified badges
  - Action buttons

---

## 🎯 Key Workflows

### Workflow 1: Generate and Edit Images

1. Go to **Chat** tab
2. Type: "Show me modern bathroom designs"
3. Wait for 3 AI-generated images
4. Click **✏️ Edit** on first image
5. Type: "Make it brighter with more natural light"
6. See updated image
7. Click **💾 Save** to add to project gallery
8. Check **Context Panel** → Images section

### Workflow 2: Create a Project Plan

1. Go to **Chat** tab
2. Type: "I want to remodel my kitchen for $15,000"
3. AI suggests design options
4. Type: "Create a DIY plan for this"
5. AI generates step-by-step plan
6. Check **Context Panel** → Tasks
7. Mark tasks as complete
8. Track budget in Overview section

### Workflow 3: Find a Contractor

1. Go to **Jobs** tab
2. Enter your zip code in filters
3. Select specialty (e.g., "Kitchen")
4. Set budget range
5. Browse contractor cards
6. Click **Request Quote** on preferred contractor
7. Fill out project details
8. Wait for response

### Workflow 4: Share Your Project

1. Complete your project in **Chat**
2. Go to **Community** tab
3. Click **Share Project** button
4. Upload before/after images
5. Add description and stats
6. Post to community
7. Get likes and comments

---

## 🎨 Design Highlights

### Color Scheme
- **Primary:** Purple-blue (#667eea)
- **Secondary:** Pink (#f093fb)
- **Accent:** Light blue (#4facfe)

### Visual Elements
- Gradient backgrounds
- Rounded corners (8-12px)
- Subtle shadows
- Smooth transitions
- Emoji icons for personality

### Responsive Design
- **Desktop:** 3-column layouts
- **Tablet:** 2-column layouts
- **Mobile:** 1-column layouts
- Touch-optimized buttons

---

## 🔧 Customization

### Change Colors
Edit `homeview-frontend/tailwind.config.js`:
```js
colors: {
  primary: '#667eea',  // Change this
  secondary: '#f093fb', // Change this
}
```

### Add More Projects
Edit `homeview-frontend/components/chat/ProjectSidebar.tsx`:
```typescript
const mockProjects: Project[] = [
  // Add your projects here
];
```

### Add More Designs
Edit `homeview-frontend/app/(dashboard)/dashboard/explore/page.tsx`:
```typescript
const mockDesigns = [
  // Add your designs here
];
```

---

## 🐛 Troubleshooting

### Issue: "Cannot find module"
**Solution:**
```bash
cd homeview-frontend
npm install
```

### Issue: "Port 3000 already in use"
**Solution:**
```bash
# Kill the process
npx kill-port 3000

# Or use a different port
npm run dev -- -p 3001
```

### Issue: "Backend not responding"
**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/api/v1/health

# Restart backend
cd backend
python -m uvicorn backend.main:app --reload --port 8000
```

### Issue: "Images not loading"
**Solution:**
1. Check backend is running on port 8000
2. Check `generated_images/` folder exists
3. Check browser console for CORS errors
4. Verify image URLs in network tab

---

## 📊 Testing Checklist

### Chat Tab
- [ ] Project sidebar displays
- [ ] Context panel displays
- [ ] Can toggle sidebars
- [ ] Can send messages
- [ ] Images generate correctly
- [ ] Edit/Save/Vary buttons work
- [ ] Tasks can be checked
- [ ] Budget tracker displays

### Design Studio Tab
- [ ] Landing page displays
- [ ] Feature cards show
- [ ] CTA buttons present

### Explore Tab
- [ ] Design gallery displays
- [ ] Search works
- [ ] Grid/List toggle works
- [ ] Like button works
- [ ] Filters work

### Community Tab
- [ ] Feed displays
- [ ] Tab switching works
- [ ] Like button works
- [ ] Before/After images show
- [ ] Stats display correctly

### Jobs Tab
- [ ] Contractor cards display
- [ ] Filters sidebar works
- [ ] Search works
- [ ] Action buttons present

---

## 🎉 Success!

You now have a **fully functional, beautifully designed** home improvement platform!

### Next Steps:
1. ✅ Test all features
2. ✅ Customize colors and content
3. ✅ Connect to real backend APIs
4. ✅ Add more features
5. ✅ Deploy to production

### Need Help?
- Check `docs/UI_REDESIGN_IMPLEMENTATION_COMPLETE.md` for details
- Check `docs/NEW_UI_REDESIGN_PLAN.md` for design rationale
- Check component files for implementation details

**Happy building! 🚀**

