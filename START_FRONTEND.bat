@echo off
echo ========================================
echo Starting HomeView Frontend
echo ========================================
echo.

cd /d "%~dp0homeview-frontend"

echo Current directory: %CD%
echo.

echo Starting Next.js development server...
echo.

"C:\Program Files\nodejs\npm.cmd" run dev

pause

