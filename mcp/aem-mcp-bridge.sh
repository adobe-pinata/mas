#!/bin/bash
# Bridge script: loads .env and runs mcp-remote with AEM auth headers
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Source .env variables
set -a
source "$PROJECT_DIR/.env"
set +a

exec npx -y mcp-remote@latest \
  "https://mcp.adobeaemcloud.com/adobe/mcp/loki/prod" \
  --transport http-only \
  --header "Authorization: Bearer ${AEM_ACCESS_TOKEN}" \
  --header "X-AEM-Author-URL: ${AEM_AUTHOR_URL}"
