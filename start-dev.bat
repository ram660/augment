@echo off
REM HomeView AI - Development Environment Startup Script
REM This script starts both the backend and frontend servers

echo ========================================
echo HomeView AI - Starting Development Environment
echo ========================================
echo.

REM Load environment variables from .env file
if exist .env (
    echo Loading environment variables from .env...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
    echo Environment variables loaded.
    echo.
) else (
    echo WARNING: .env file not found!
    echo.
)

REM Check if virtual environment exists
if not exist .venv (
    echo ERROR: Python virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if frontend dependencies are installed
if not exist homeview-frontend\node_modules (
    echo Frontend dependencies not found. Installing...
    cd homeview-frontend
    call npm install
    cd ..
    echo.
)

echo ========================================
echo Starting Backend Server (Port 8000)
echo ========================================
echo.

REM Start backend in a new window
start "HomeView Backend" cmd /k ".venv\Scripts\python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 5 /nobreak >nul

echo ========================================
echo Starting Frontend Server (Port 3000)
echo ========================================
echo.

REM Create frontend .env.local if it doesn't exist
if not exist homeview-frontend\.env.local (
    echo Creating frontend .env.local...
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > homeview-frontend\.env.local
    echo.
)

REM Start frontend in a new window
start "HomeView Frontend" cmd /k "cd homeview-frontend && set PATH=C:\Program Files\nodejs;%PATH% && npm run dev"

echo.
echo ========================================
echo Development Environment Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Swagger:  http://localhost:8000/docs
echo.
echo Press any key to stop all servers...
pause >nul

REM Kill all related processes
echo.
echo Stopping servers...
taskkill /FI "WINDOWTITLE eq HomeView Backend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq HomeView Frontend*" /T /F >nul 2>nul
echo Servers stopped.

