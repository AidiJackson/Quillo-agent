#!/bin/bash
# start-dev.sh - Start backend and frontend for Quillo/Uboolia
# Usage: bash start-dev.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Quillo development servers...${NC}"

# Track child PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""
CLEANUP_DONE=false

cleanup() {
    if [ "$CLEANUP_DONE" = true ]; then
        return
    fi
    CLEANUP_DONE=true
    
    # Clear traps to prevent re-entry
    trap - SIGINT SIGTERM EXIT
    
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "Stopping backend (PID $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
    
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "Stopping frontend (PID $FRONTEND_PID)..."
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}All servers stopped.${NC}"
}

# Trap signals
trap cleanup SIGINT SIGTERM EXIT

# Start backend (FastAPI on port 8000)
echo -e "${GREEN}Starting backend on port 8000...${NC}"
python -m uvicorn app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}Backend started (PID $BACKEND_PID)${NC}"

# Wait a moment for backend to initialize
sleep 2

# Start frontend (Vite on port 5000) in a subshell
echo -e "${GREEN}Starting frontend on port 5000...${NC}"
(cd frontend && npm run dev) &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started (PID $FRONTEND_PID)${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Quillo development servers running${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "  Backend:  ${YELLOW}http://0.0.0.0:8000${NC}"
echo -e "  Frontend: ${YELLOW}http://0.0.0.0:5000${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Wait for either process to exit
wait -n $BACKEND_PID $FRONTEND_PID

# If we get here, one process died
echo -e "${RED}A server process exited unexpectedly${NC}"
