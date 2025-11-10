# HomeView AI - Development Setup Guide

## Quick Start

### Option 1: Using Startup Scripts (Recommended)

#### Windows - PowerShell (Recommended)
```powershell
.\start-dev.ps1
```

**Note**: If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Windows - Command Prompt
Double-click `start-dev.bat` or run:
```cmd
start-dev.bat
```

#### Linux/Mac/Git Bash
```bash
./start-dev.sh
```

The scripts will:
1. Load environment variables from `.env`
2. Check for required dependencies
3. Install frontend dependencies if needed
4. Start the backend server on port 8000
5. Start the frontend server on port 3000
6. Open separate windows/terminals for each server

### Option 2: Manual Startup

#### Backend
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Start backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd homeview-frontend
npm run dev
```

## Prerequisites

### Required Software
- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **npm** - Node package manager (comes with Node.js)

### Installation

#### 1. Python Virtual Environment
```bash
python -m venv .venv
```

#### 2. Install Python Dependencies
```bash
# Windows
.venv\Scripts\pip install -r requirements.txt

# Linux/Mac
.venv/bin/pip install -r requirements.txt
```

#### 3. Install Frontend Dependencies
```bash
cd homeview-frontend
npm install
cd ..
```

## Environment Configuration

### Backend (.env)
Located in the root directory. Key variables:

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=your_google_api_key

# Database
USE_SQLITE=true
DATABASE_URL=sqlite:///./homevision.db
DATABASE_URL_ASYNC=sqlite+aiosqlite:///./homevision.db

# Storage
USE_GCS=true
GCS_BUCKET_NAME=your_bucket_name
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### Frontend (.env.local)
Located in `homeview-frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

This file is automatically created by the startup scripts if it doesn't exist.

## Accessing the Application

Once both servers are running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc

## Development Workflow

### Making Changes

#### Backend Changes
- The backend uses `--reload` flag, so changes are automatically detected
- Server will restart automatically when you save Python files
- Check the backend terminal for any errors

#### Frontend Changes
- Next.js has hot module replacement (HMR)
- Changes appear instantly in the browser
- Check the frontend terminal and browser console for errors

### Viewing Logs

#### Windows (start-dev.bat)
- Backend and frontend run in separate Command Prompt windows
- Logs are visible in each window

#### Linux/Mac/Git Bash (start-dev.sh)
- Logs are saved to `logs/` directory
- View in real-time:
  ```bash
  tail -f logs/backend.log
  tail -f logs/frontend.log
  ```

## Troubleshooting

### Backend Won't Start

**Issue**: `ModuleNotFoundError` or import errors
**Solution**: Reinstall dependencies
```bash
.venv\Scripts\pip install -r requirements.txt
```

**Issue**: Port 8000 already in use
**Solution**: Kill the process using port 8000
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Issue**: Database errors
**Solution**: Delete and recreate the database
```bash
rm homevision.db
# Database will be recreated on next startup
```

### Frontend Won't Start

**Issue**: `npm` command not found
**Solution**: Add Node.js to PATH
```bash
# Windows - Add to PATH:
C:\Program Files\nodejs

# Or use full path:
"C:\Program Files\nodejs\npm.cmd" run dev
```

**Issue**: Port 3000 already in use
**Solution**: Kill the process or use a different port
```bash
# Kill process on port 3000
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

**Issue**: Module not found errors
**Solution**: Reinstall dependencies
```bash
cd homeview-frontend
rm -rf node_modules package-lock.json
npm install
```

### Frontend Can't Connect to Backend

**Issue**: 403 Forbidden or CORS errors
**Solution**: 
1. Check that backend is running on port 8000
2. Verify `.env.local` has correct API URL
3. Clear browser cache and reload
4. Check browser console for detailed errors

**Issue**: No response from chat
**Solution**: 
1. Backend is running but authentication is required
2. The fix has been applied to allow unauthenticated requests in development
3. Restart the backend server to apply changes

### Authentication Issues

**Development Mode**: The backend automatically creates a test user if no authentication is provided.

**Test User**:
- ID: `550e8400-e29b-41d4-a716-446655440000`
- Email: `test@homeview.ai`
- Username: `test_user`

## Database Management

### View Database
```bash
# Install SQLite browser or use command line
sqlite3 homevision.db

# List tables
.tables

# View users
SELECT * FROM users;

# View conversations
SELECT * FROM conversations;

# View journeys
SELECT * FROM journeys;
```

### Reset Database
```bash
# Backup first (optional)
cp homevision.db homevision.db.backup

# Delete database
rm homevision.db

# Restart backend - database will be recreated
```

### Run Migrations
```bash
# Run specific migration
.venv\Scripts\python backend/migrations/run_add_display_order.py
```

## Testing

### Backend Tests
```bash
# Run all tests
.venv\Scripts\python -m pytest

# Run specific test file
.venv\Scripts\python -m pytest backend/tests/test_chat_journey_integration.py

# Run with verbose output
.venv\Scripts\python -m pytest -v

# Run with coverage
.venv\Scripts\python -m pytest --cov=backend
```

### Frontend Tests
```bash
cd homeview-frontend
npm test
```

## Production Deployment

### Backend
```bash
# Install production dependencies
pip install -r requirements.txt

# Run with production server
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
cd homeview-frontend

# Build for production
npm run build

# Start production server
npm start
```

## Additional Resources

- **API Documentation**: See `docs/API_DOCUMENTATION.md`
- **Journey System**: See `docs/JOURNEY_UI_DESIGN.md`
- **Phase 2.2 Features**: See `docs/PHASE_2_2_COMPLETION_SUMMARY.md`
- **Testing Guide**: See `docs/PHASE_2_2_TESTING_GUIDE.md`

## Support

If you encounter issues not covered in this guide:

1. Check the logs for detailed error messages
2. Review the relevant documentation in the `docs/` directory
3. Check GitHub issues for similar problems
4. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version, Node version)

