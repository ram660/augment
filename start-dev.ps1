# HomeView AI - Development Environment Startup Script (PowerShell)
# This script starts both the backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HomeView AI - Starting Development Environment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Load environment variables from .env file
if (Test-Path .env) {
    Write-Host "Loading environment variables from .env..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Verbose "Set $name"
        }
    }
    Write-Host "Environment variables loaded." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host ""
}

# Check if virtual environment exists
if (-not (Test-Path .venv)) {
    Write-Host "ERROR: Python virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    Write-Host "Then run: .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Node.js is installed
$nodeExists = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeExists) {
    Write-Host "ERROR: Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if frontend dependencies are installed
if (-not (Test-Path homeview-frontend\node_modules)) {
    Write-Host "Frontend dependencies not found. Installing..." -ForegroundColor Yellow
    Push-Location homeview-frontend
    npm install
    Pop-Location
    Write-Host ""
}

# Create frontend .env.local if it doesn't exist
if (-not (Test-Path homeview-frontend\.env.local)) {
    Write-Host "Creating frontend .env.local..." -ForegroundColor Yellow
    "NEXT_PUBLIC_API_URL=http://localhost:8000" | Out-File -FilePath homeview-frontend\.env.local -Encoding utf8
    Write-Host ""
}

# Create logs directory
if (-not (Test-Path logs)) {
    New-Item -ItemType Directory -Path logs | Out-Null
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Backend Server (Port 8000)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start backend in a new PowerShell window
$backendScript = @"
Set-Location '$PWD'
Write-Host 'Starting Backend Server...' -ForegroundColor Green
.\.venv\Scripts\python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"@

$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript -PassThru
Write-Host "Backend started in new window (PID: $($backendJob.Id))" -ForegroundColor Green

# Wait for backend to start
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if backend is running
if ($backendJob.HasExited) {
    Write-Host "ERROR: Backend failed to start!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Backend started successfully!" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Frontend Server (Port 3000)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start frontend in a new PowerShell window
$frontendScript = @"
Set-Location '$PWD\homeview-frontend'
Write-Host 'Starting Frontend Server...' -ForegroundColor Green
`$env:PATH = 'C:\Program Files\nodejs;' + `$env:PATH
npm run dev
"@

$frontendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript -PassThru
Write-Host "Frontend started in new window (PID: $($frontendJob.Id))" -ForegroundColor Green

# Wait for frontend to start
Write-Host "Waiting for frontend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if frontend is running
if ($frontendJob.HasExited) {
    Write-Host "ERROR: Frontend failed to start!" -ForegroundColor Red
    Write-Host "Stopping backend..." -ForegroundColor Yellow
    Stop-Process -Id $backendJob.Id -Force -ErrorAction SilentlyContinue
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Frontend started successfully!" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Development Environment Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Swagger:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Process IDs:" -ForegroundColor Yellow
Write-Host "  Backend:  $($backendJob.Id)" -ForegroundColor Yellow
Write-Host "  Frontend: $($frontendJob.Id)" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop servers, close the PowerShell windows or run:" -ForegroundColor Yellow
Write-Host "  Stop-Process -Id $($backendJob.Id)" -ForegroundColor Gray
Write-Host "  Stop-Process -Id $($frontendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to stop all servers and exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup
Write-Host ""
Write-Host "Stopping servers..." -ForegroundColor Yellow
Stop-Process -Id $backendJob.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontendJob.Id -Force -ErrorAction SilentlyContinue
Write-Host "Servers stopped." -ForegroundColor Green

