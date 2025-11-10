# HomeView AI - Quick Start Guide

## 🚀 Start Development Environment

### PowerShell (Windows - Recommended)
```powershell
.\start-dev.ps1
```

### Command Prompt (Windows)
```cmd
start-dev.bat
```

### Bash (Linux/Mac/Git Bash)
```bash
./start-dev.sh
```

## 🌐 Access Points

Once started, access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs

## ⚙️ First Time Setup

If this is your first time running the project:

1. **Create Python virtual environment**:
   ```bash
   python -m venv .venv
   ```

2. **Install Python dependencies**:
   ```bash
   # Windows PowerShell
   .\.venv\Scripts\pip install -r requirements.txt
   
   # Windows Command Prompt
   .venv\Scripts\pip install -r requirements.txt
   
   # Linux/Mac
   .venv/bin/pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**:
   ```bash
   cd homeview-frontend
   npm install
   cd ..
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env` (if exists)
   - Or ensure `.env` file exists with required variables
   - The startup scripts will create `homeview-frontend/.env.local` automatically

5. **Run the startup script** (see above)

## 🔧 PowerShell Execution Policy

If you get an error like "cannot be loaded because running scripts is disabled", run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try running `.\start-dev.ps1` again.

## 📝 What the Startup Scripts Do

1. ✅ Load environment variables from `.env`
2. ✅ Check for Python virtual environment
3. ✅ Check for Node.js installation
4. ✅ Install frontend dependencies (if needed)
5. ✅ Create frontend `.env.local` (if needed)
6. ✅ Start backend server on port 8000
7. ✅ Start frontend server on port 3000
8. ✅ Open separate windows for each server

## 🛑 Stopping Servers

### PowerShell Script
- Press any key in the main PowerShell window
- Or close the backend/frontend PowerShell windows

### Batch Script
- Press any key in the main Command Prompt window
- Or close the backend/frontend Command Prompt windows

### Bash Script
- Press `Ctrl+C` in the terminal

### Manual
```powershell
# PowerShell - Find and kill processes
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"}
Stop-Process -Name python,node -Force

# Or by port
netstat -ano | findstr :8000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Reinstall dependencies
.\.venv\Scripts\pip install -r requirements.txt

# Check if port 8000 is in use
netstat -ano | findstr :8000
```

### Frontend won't start
```bash
# Reinstall dependencies
cd homeview-frontend
rm -rf node_modules package-lock.json
npm install

# Check if port 3000 is in use
netstat -ano | findstr :3000
```

### "Module not found" errors
```bash
# Backend
.\.venv\Scripts\pip install -r requirements.txt

# Frontend
cd homeview-frontend
npm install
```

### Frontend can't connect to backend
1. Verify backend is running: http://localhost:8000/docs
2. Check `homeview-frontend/.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Clear browser cache and reload
4. Check browser console for errors

## 📚 More Information

For detailed documentation, see:
- **Full Setup Guide**: `docs/DEVELOPMENT_SETUP.md`
- **API Documentation**: http://localhost:8000/docs (when running)
- **Journey System**: `docs/JOURNEY_UI_DESIGN.md`
- **Phase 2.2 Features**: `docs/PHASE_2_2_COMPLETION_SUMMARY.md`

## 🧪 Testing

### Backend Tests
```bash
.\.venv\Scripts\python -m pytest
```

### Frontend Tests
```bash
cd homeview-frontend
npm test
```

## 💡 Tips

- **View Backend Logs**: Check the backend PowerShell/Command Prompt window
- **View Frontend Logs**: Check the frontend PowerShell/Command Prompt window
- **Hot Reload**: Both servers support hot reload - changes are applied automatically
- **API Testing**: Use Swagger UI at http://localhost:8000/docs for interactive API testing
- **Database**: SQLite database is at `./homevision.db` - use SQLite browser to inspect

## 🎯 Development Workflow

1. Start servers with startup script
2. Make changes to code
3. Changes auto-reload in browser/server
4. Test in browser at http://localhost:3000
5. Test APIs at http://localhost:8000/docs
6. Stop servers when done

## 🔑 Test User (Development)

The backend automatically creates a test user for development:

- **User ID**: `550e8400-e29b-41d4-a716-446655440000`
- **Email**: `test@homeview.ai`
- **Username**: `test_user`

No authentication required in development mode!

## 📞 Need Help?

Check the full documentation in `docs/DEVELOPMENT_SETUP.md` for:
- Detailed troubleshooting
- Database management
- Production deployment
- Testing strategies

