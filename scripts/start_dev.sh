#!/usr/bin/env bash
# Start M@S dev servers for isolated worktree testing.
# Reads BACKEND_PORT (studio proxy) and FRONTEND_PORT (aem up) from env.
# Writes PIDs to .dev_server.pids for stop_dev_server() in adw_test_iso.py.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PIDS_FILE="$REPO_ROOT/.dev_server.pids"

BACKEND_PORT="${BACKEND_PORT:-8080}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

echo "Starting studio proxy on port $BACKEND_PORT..."
PORT="$BACKEND_PORT" node "$REPO_ROOT/studio/proxy-server.mjs" https://author-p22655-e59433.adobeaemcloud.com \
  > "$REPO_ROOT/.proxy.log" 2>&1 &
PROXY_PID=$!

echo "Starting aem up on port $FRONTEND_PORT..."
cd "$REPO_ROOT" && aem up --port "$FRONTEND_PORT" \
  > "$REPO_ROOT/.aem.log" 2>&1 &
AEM_PID=$!

echo "$PROXY_PID $AEM_PID" > "$PIDS_FILE"
echo "Started proxy (pid=$PROXY_PID) and aem up (pid=$AEM_PID)"
echo "Logs: .proxy.log, .aem.log"
