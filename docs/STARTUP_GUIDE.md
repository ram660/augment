# HomeView AI - Startup Guide

## 🎉 Current Status

### ✅ Backend API - RUNNING
- **URL**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **Status**: ✅ Running on Terminal 19
- **Database**: ✅ All tables created (including journey tables)
- **Tests**: ✅ 12/12 Journey API tests passing

### ⚠️ Frontend - MANUAL STARTUP REQUIRED
- **Target URL**: http://localhost:3000
- **Status**: ⏳ Needs manual startup (see instructions below)
- **Issue**: npm/node not in PATH for Git Bash environment

---

## 🚀 Quick Start

### Option 1: Test Backend APIs (Ready Now!)

1. **Open Swagger UI** (already opened for you):
   - URL: http://localhost:8000/docs

2. **Test Journey Creation**:
   ```json
   POST /api/v1/journey/start
   {
     "user_id": "test-user-123",
     "template_id": "kitchen_renovation",
     "home_id": null,
     "conversation_id": null
   }
   ```

3. **Available Templates**:
   - `kitchen_renovation` - 7 steps, kitchen remodel journey
   - `bathroom_upgrade` - Bathroom renovation journey
   - `diy_project` - DIY home improvement journey

4. **Test Other Endpoints**:
   - GET `/api/v1/journey/{journey_id}` - Get journey details
   - GET `/api/v1/journey/user/{user_id}` - List user journeys
   - PUT `/api/v1/journey/{journey_id}/steps/{step_id}` - Update step
   - POST `/api/v1/journey/{journey_id}/steps/{step_id}/images` - Upload image

---

### Option 2: Start Frontend Manually

#### Method A: Using Windows Command Prompt (Recommended)

1. **Open a NEW Command Prompt** (not Git Bash):
   - Press `Win + R`
   - Type `cmd` and press Enter

2. **Navigate to frontend directory**:
   ```cmd
   cd C:\Users\ramma\augment\homeview-frontend
   ```

3. **Add Node.js to PATH** (if needed):
   ```cmd
   set PATH=C:\Program Files\nodejs;%PATH%
   ```

4. **Start the development server**:
   ```cmd
   npm run dev
   ```

5. **Access the frontend**:
   - Open browser to http://localhost:3000

#### Method B: Using PowerShell

1. **Open PowerShell**:
   - Press `Win + X`
   - Select "Windows PowerShell"

2. **Navigate and start**:
   ```powershell
   cd C:\Users\ramma\augment\homeview-frontend
   $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
   npm run dev
   ```

3. **Access the frontend**:
   - Open browser to http://localhost:3000

#### Method C: Using the Batch File

1. **Double-click** `start-frontend.bat` in the project root
2. A command window will open and start the frontend
3. Access at http://localhost:3000

---

### Option 3: Backend Development (In Progress)

See `docs/BACKEND_DEVELOPMENT_PLAN.md` for the complete roadmap.

**Current Phase**: Journey Persistence Integration

**Next Steps**:
1. Integrate `JourneyPersistenceService` into `ChatWorkflow`
2. Update `_manage_journey()` to use database persistence
3. Link conversations to journeys
4. Add image upload to journey steps

---

## 📊 Journey API Test Results

All 12 tests passing! ✅

### Test Coverage:
1. ✅ `test_create_journey` - Create new journey
2. ✅ `test_get_journey` - Retrieve journey details
3. ✅ `test_get_journey_with_images` - Get journey with images
4. ✅ `test_get_user_journeys` - List all user journeys
5. ✅ `test_filter_user_journeys_by_status` - Filter by status
6. ✅ `test_update_step_status` - Update step status
7. ✅ `test_complete_step_advances_journey` - Step completion logic
8. ✅ `test_update_step_with_data` - Update step data
9. ✅ `test_upload_step_image` - Upload image to step
10. ✅ `test_get_journey_images` - Get all journey images
11. ✅ `test_journey_not_found` - Error handling
12. ✅ `test_invalid_template_id` - Validation

---

## 🔧 Issues Fixed Today

### 1. Step ID Mismatch (UUID vs String)
**Problem**: Tests passing UUID but service expecting string identifier.

**Solution**: Updated service to accept both UUID and string identifiers.

### 2. Journey Completing Prematurely
**Problem**: Journey marked as "completed" after first step.

**Solution**: Fixed step index lookup to support both identifier types.

### 3. Missing Label in Image Upload
**Problem**: Image `label` parameter not being saved.

**Solution**: Added `label` parameter throughout the chain (API → Service → Model).

### 4. UNIQUE Constraint Error
**Problem**: Multiple journeys generating same ID.

**Solution**: Let SQLAlchemy generate unique UUIDs automatically.

---

## 📁 Project Structure

```
augment/
├── backend/
│   ├── api/
│   │   └── journey.py          # Journey API endpoints
│   ├── models/
│   │   └── journey.py          # Journey database models
│   ├── services/
│   │   ├── journey_manager.py  # In-memory journey management
│   │   └── journey_persistence_service.py  # Database persistence
│   ├── tests/
│   │   └── test_journey_api.py # Journey API tests (12/12 passing)
│   ├── workflows/
│   │   └── chat_workflow.py    # Chat orchestration (needs integration)
│   └── main.py                 # FastAPI application
├── homeview-frontend/
│   ├── app/                    # Next.js 15 app directory
│   ├── components/             # React components
│   └── package.json            # Frontend dependencies
├── docs/
│   ├── BACKEND_DEVELOPMENT_PLAN.md  # Development roadmap
│   ├── STARTUP_GUIDE.md             # This file
│   └── ui-design/
│       ├── JOURNEY_UI_DESIGN.md     # UI/UX design
│       └── COMPONENT_SPECIFICATIONS.md  # Component specs
└── start-frontend.bat          # Frontend startup script
```

---

## 🎯 Available Journey Templates

### Kitchen Renovation (7 steps)
1. **Initial Consultation** - Share photos and discuss vision
2. **Vision Analysis** - AI analyzes space and provides insights
3. **Design Options** - Explore design transformations
4. **Product Selection** - Choose materials and fixtures
5. **Cost Estimate** - Get detailed cost breakdown
6. **Find Contractors** - Connect with local contractors
7. **Finalize Plan** - Export project plan and timeline

### Bathroom Upgrade
- Similar structure to kitchen renovation
- Focused on bathroom-specific features

### DIY Project
- Flexible template for various DIY projects
- Customizable steps

---

## 🔍 Testing the Journey APIs

### Example 1: Create a Kitchen Renovation Journey

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/journey/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "template_id": "kitchen_renovation"
  }'
```

**Response**:
```json
{
  "id": "538f169b-dc0a-410e-b58b-fe82915b37e5",
  "user_id": "test-user-123",
  "template_id": "kitchen_renovation",
  "title": "Kitchen Renovation",
  "status": "in_progress",
  "completed_steps": 0,
  "total_steps": 7,
  "progress_percentage": 0.0,
  "steps": [
    {
      "id": "25e9bf64-cd60-40c0-814a-96e9f93efa75",
      "step_id": "initial_consultation",
      "name": "Initial Consultation",
      "status": "in_progress",
      "progress_percentage": 0.0
    },
    ...
  ]
}
```

### Example 2: Update Step Status

**Request**:
```bash
curl -X PUT "http://localhost:8000/api/v1/journey/{journey_id}/steps/{step_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "progress": 100.0
  }'
```

### Example 3: Upload Image to Step

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/journey/{journey_id}/steps/{step_id}/images" \
  -F "file=@kitchen_before.jpg" \
  -F "label=Current kitchen state" \
  -F "image_type=before"
```

---

## 🐛 Troubleshooting

### Backend Not Running
```bash
cd C:\Users\ramma\augment
.venv\Scripts\python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Won't Start
1. Check if Node.js is installed: `node --version`
2. Check if npm is installed: `npm --version`
3. Try reinstalling dependencies: `npm install`
4. Use Command Prompt instead of Git Bash

### Database Issues
```bash
# Reset database (WARNING: Deletes all data)
rm homeview.db
# Restart backend to recreate tables
```

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000
# Kill process (replace PID)
taskkill /PID <PID> /F
```

---

## 📞 Next Actions

1. **Test the Journey APIs** in Swagger UI (http://localhost:8000/docs)
2. **Start the Frontend** using one of the methods above
3. **Review the Development Plan** in `docs/BACKEND_DEVELOPMENT_PLAN.md`
4. **Continue Backend Integration** - Integrate persistence into chat workflow

---

## 🎉 Success!

You now have:
- ✅ Backend API running with all journey endpoints
- ✅ All 12 journey API tests passing
- ✅ Database with journey tables created
- ✅ Comprehensive documentation
- ✅ Clear development roadmap

**Ready to test and develop!** 🚀

