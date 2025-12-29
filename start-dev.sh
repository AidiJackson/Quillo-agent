#!/bin/bash
# start-dev.sh - Canonical backend startup for Replit Run button
# Usage: bash start-dev.sh
#
# This script:
# - Stops any existing uvicorn processes
# - Starts the backend via `make run`
# - Exits non-zero if startup fails

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Quillo backend (canonical workflow)...${NC}"

# STEP 1: Kill any existing uvicorn processes on port 8000
echo -e "${YELLOW}Checking for existing uvicorn processes...${NC}"

# Try multiple methods to find existing processes
EXISTING_PIDS=$(pgrep -f "uvicorn app:app" 2>/dev/null || true)

# Also check port 8000 using lsof if available
if command -v lsof &> /dev/null; then
    PORT_PIDS=$(lsof -ti :8000 2>/dev/null || true)
    EXISTING_PIDS="$EXISTING_PIDS $PORT_PIDS"
fi

# Remove duplicates and empty entries
EXISTING_PIDS=$(echo "$EXISTING_PIDS" | tr ' ' '\n' | sort -u | grep -v '^$' || true)

if [ -n "$EXISTING_PIDS" ]; then
    echo -e "${YELLOW}Found existing uvicorn processes: $EXISTING_PIDS${NC}"
    echo -e "${YELLOW}Stopping them gracefully...${NC}"

    for PID in $EXISTING_PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            echo "  Stopping PID $PID..."
            kill "$PID" 2>/dev/null || true
        fi
    done

    # Wait up to 3 seconds for graceful shutdown
    sleep 1

    # Force kill if still alive
    for PID in $EXISTING_PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            echo "  Force killing PID $PID..."
            kill -9 "$PID" 2>/dev/null || true
        fi
    done

    echo -e "${GREEN}Existing processes stopped.${NC}"
else
    echo -e "${GREEN}No existing uvicorn processes found.${NC}"
fi

# STEP 2: Start backend using the official command
echo -e "${GREEN}Starting backend via 'make run'...${NC}"

# Run in foreground so Replit can manage it
exec make run

# If we get here, exec failed
echo -e "${RED}Failed to start backend!${NC}"
exit 1
