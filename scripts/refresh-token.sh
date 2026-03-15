#!/usr/bin/env bash
# Refresh the Anthropic OAuth token in .env from the best available source.
# Run this whenever you see a 401 from the server.
#
# Sources tried in order:
#   1. CLAUDE_CODE_OAUTH_TOKEN env var (set by active Claude Code session)
#   2. macOS Keychain (Claude Code-credentials)
#   3. Prompts user to paste a token manually

set -euo pipefail

ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"

validate_token() {
  local token="$1"
  local status
  status=$(curl -s -o /dev/null -w "%{http_code}" https://api.anthropic.com/v1/messages \
    -H "x-api-key: $token" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{"model":"claude-haiku-4-5-20251001","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}')
  [[ "$status" == "200" ]]
}

write_token() {
  local token="$1"
  python3 - "$token" "$ENV_FILE" <<'EOF'
import re, sys
token, env_file = sys.argv[1], sys.argv[2]
with open(env_file) as f:
    content = f.read()
content = re.sub(r'^SETUP_TOKEN=.*', f'SETUP_TOKEN={token}', content, flags=re.MULTILINE)
content = re.sub(r'^CLAUDE_CODE_OAUTH_TOKEN=.*', f'CLAUDE_CODE_OAUTH_TOKEN={token}', content, flags=re.MULTILINE)
with open(env_file, 'w') as f:
    f.write(content)
EOF
}

TOKEN=""

# 1. Active Claude Code session
if [[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
  echo "Trying CLAUDE_CODE_OAUTH_TOKEN..."
  if validate_token "$CLAUDE_CODE_OAUTH_TOKEN"; then
    TOKEN="$CLAUDE_CODE_OAUTH_TOKEN"
    echo "✓ Valid token from Claude Code session"
  fi
fi

# 2. macOS Keychain
if [[ -z "$TOKEN" ]] && command -v security &>/dev/null; then
  echo "Trying macOS Keychain..."
  KEYCHAIN_JSON=$(security find-generic-password -s "Claude Code-credentials" -a "${USER:-rivero}" -w 2>/dev/null || true)
  if [[ -n "$KEYCHAIN_JSON" ]]; then
    KEYCHAIN_TOKEN=$(echo "$KEYCHAIN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('claudeAiOauth',{}).get('accessToken',''))" 2>/dev/null || true)
    if [[ -n "$KEYCHAIN_TOKEN" ]] && validate_token "$KEYCHAIN_TOKEN"; then
      TOKEN="$KEYCHAIN_TOKEN"
      echo "✓ Valid token from macOS Keychain"
    else
      echo "✗ Keychain token is invalid or expired"
    fi
  fi
fi

# 3. Manual paste
if [[ -z "$TOKEN" ]]; then
  echo ""
  echo "No valid token found automatically."
  echo "Get one from an active Claude Code session: printenv CLAUDE_CODE_OAUTH_TOKEN"
  echo ""
  read -r -p "Paste your sk-ant-oat01-... token: " TOKEN
  if ! validate_token "$TOKEN"; then
    echo "✗ Token is not valid (API returned 401)"
    exit 1
  fi
  echo "✓ Token validated"
fi

write_token "$TOKEN"
echo "✓ Written to $ENV_FILE"
echo ""
echo "Restart the server to apply: lsof -ti:3001 | xargs kill -9 && node --env-file=../../../.env index.js &"
