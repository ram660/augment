#!/bin/bash
# HomeView AI - Development Environment Startup Script
# This script starts both the backend and frontend servers

set -e

echo "========================================"
echo "HomeView AI - Starting Development Environment"
echo "========================================"
echo ""

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "Environment variables loaded."
    echo ""
else
    echo "WARNING: .env file not found!"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "ERROR: Python virtual environment not found!"
    echo "Please run: python -m venv .venv"
    echo "Then run: .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "homeview-frontend/node_modules" ]; then
    echo "Frontend dependencies not found. Installing..."
    cd homeview-frontend
    npm install
    cd ..
    echo ""
fi

# Create frontend .env.local if it doesn't exist
if [ ! -f "homeview-frontend/.env.local" ]; then
    echo "Creating frontend .env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > homeview-frontend/.env.local
    echo ""
fi

# Create log directory
mkdir -p logs

echo "========================================"
echo "Starting Backend Server (Port 8000)"
echo "========================================"
echo ""

# Start backend in background
.venv/bin/python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "ERROR: Backend failed to start. Check logs/backend.log"
    exit 1
fi

echo "Backend started successfully!"
echo ""

echo "========================================"
echo "Starting Frontend Server (Port 3000)"
echo "========================================"
echo ""

# Start frontend in background
cd homeview-frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 5

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "ERROR: Frontend failed to start. Check logs/frontend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "Frontend started successfully!"
echo ""

echo "========================================"
echo "Development Environment Started!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Swagger:  http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  Backend:  logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo "To view logs in real-time:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "Servers stopped."
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Wait for user to press Ctrl+C
wait

