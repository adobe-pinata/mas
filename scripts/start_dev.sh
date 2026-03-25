#!/usr/bin/env bash
# Start MAS dev servers for isolated ADW execution.
# Reads BACKEND_PORT and FRONTEND_PORT from environment (set by adw_test_iso.py).
# Writes PIDs to .dev_server.pids for clean shutdown.

set -euo pipefail

WORKTREE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS_FILE="$WORKTREE_DIR/.dev_server.pids"
BACKEND_PORT="${BACKEND_PORT:-8080}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

echo "Starting MAS dev servers: backend=$BACKEND_PORT frontend=$FRONTEND_PORT"

# Start backend (studio / AEM content server)
aem up --port "$BACKEND_PORT" --no-open &
BACKEND_PID=$!

# Start frontend (web-components dev server)
aem up --port "$FRONTEND_PORT" --no-open &
FRONTEND_PID=$!

# Write PIDs for later cleanup
echo "$BACKEND_PID $FRONTEND_PID" > "$PIDS_FILE"
echo "PIDs written: backend=$BACKEND_PID frontend=$FRONTEND_PID"

# Wait for servers to be ready (up to 30s each)
for PORT in "$BACKEND_PORT" "$FRONTEND_PORT"; do
  echo "Waiting for port $PORT..."
  for i in $(seq 1 30); do
    if curl -s --max-time 1 "http://localhost:$PORT" >/dev/null 2>&1; then
      echo "  Port $PORT ready"
      break
    fi
    sleep 1
    if [ "$i" -eq 30 ]; then
      echo "  WARNING: Port $PORT not ready after 30s, continuing anyway"
    fi
  done
done

echo "Dev servers started successfully"
