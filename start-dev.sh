#!/bin/bash
# start-dev.sh - Startup script for Replit Run button
# Usage: bash start-dev.sh
#
# This script:
# - Stops any existing processes
# - Starts both the backend (port 8000) and frontend (port 5000)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Quillo (backend + frontend)...${NC}"

# STEP 1: Kill any existing processes on ports 5000 and 8000
echo -e "${YELLOW}Checking for existing processes...${NC}"

EXISTING_PIDS=$(pgrep -f "uvicorn app:app" 2>/dev/null || true)

if command -v lsof &> /dev/null; then
    PORT_PIDS=$(lsof -ti :8000 -ti :5000 2>/dev/null || true)
    EXISTING_PIDS="$EXISTING_PIDS $PORT_PIDS"
fi

EXISTING_PIDS=$(echo "$EXISTING_PIDS" | tr ' ' '\n' | sort -u | grep -v '^$' || true)

if [ -n "$EXISTING_PIDS" ]; then
    echo -e "${YELLOW}Stopping existing processes: $EXISTING_PIDS${NC}"
    for PID in $EXISTING_PIDS; do
        kill "$PID" 2>/dev/null || true
    done
    sleep 1
    for PID in $EXISTING_PIDS; do
        kill -9 "$PID" 2>/dev/null || true
    done
    echo -e "${GREEN}Existing processes stopped.${NC}"
else
    echo -e "${GREEN}No existing processes found.${NC}"
fi

# STEP 2: Start backend in background
echo -e "${GREEN}Starting backend on port 8000...${NC}"
make run &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 2

# STEP 3: Start frontend (this runs in foreground so Replit can manage it)
echo -e "${GREEN}Starting frontend on port 5000...${NC}"
cd frontend && npm run dev
