@echo off
REM Add Node.js to PATH for this session
set PATH=C:\Program Files\nodejs;%PATH%

REM Change to frontend directory
cd homeview-frontend

REM Start the development server
npm run dev

