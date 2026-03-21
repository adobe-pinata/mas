#!/usr/bin/env bash
# Refresh the Anthropic OAuth token across all apps from the best available source.
# Run this whenever you see a 401 or 400 from the server.
#
# Sources tried in order:
#   1. CLAUDE_CODE_OAUTH_TOKEN env var (set by active Claude Code session)
#   2. macOS Keychain (Claude Code-credentials)
#   3. Prompts user to paste a token manually
#
# Updates:
#   - .env (CLAUDE_CODE_OAUTH_TOKEN line) in each app
#   - .tokens/auth-profiles.json in each app

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── Discover apps with .env files ─────────────────────────────────────────────

find_app_envs() {
  find "$REPO_ROOT/apps" -maxdepth 2 -name ".env" -type f 2>/dev/null | sort
}

# ── Token validation ─────────────────────────────────────────────────────────

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

# ── Write token to .env ──────────────────────────────────────────────────────

write_env_token() {
  local token="$1" env_file="$2"
  python3 - "$token" "$env_file" <<'PYEOF'
import re, sys
token, env_file = sys.argv[1], sys.argv[2]
with open(env_file) as f:
    content = f.read()
if re.search(r'^CLAUDE_CODE_OAUTH_TOKEN=', content, re.MULTILINE):
    content = re.sub(r'^CLAUDE_CODE_OAUTH_TOKEN=.*', f'CLAUDE_CODE_OAUTH_TOKEN={token}', content, flags=re.MULTILINE)
else:
    content += f'\nCLAUDE_CODE_OAUTH_TOKEN={token}\n'
with open(env_file, 'w') as f:
    f.write(content)
PYEOF
}

# ── Write token to auth-profiles.json ─────────────────────────────────────────

write_auth_profiles() {
  local token="$1" app_dir="$2"
  local tokens_dir="$app_dir/.tokens"
  mkdir -p "$tokens_dir"
  python3 - "$token" "$tokens_dir/auth-profiles.json" <<'PYEOF'
import json, sys, time
token, out_file = sys.argv[1], sys.argv[2]
now_ms = int(time.time() * 1000)
ttl_ms = 55 * 60 * 1000
data = {
    "anthropic": {
        "default": {
            "access_token": token,
            "expires": now_ms + ttl_ms,
            "storedAt": now_ms
        }
    }
}
with open(out_file, 'w') as f:
    json.dump(data, f, indent=2)
PYEOF
}

# ── Acquire token ─────────────────────────────────────────────────────────────

TOKEN=""

# 1. Active Claude Code session env var
if [[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
  echo "Trying CLAUDE_CODE_OAUTH_TOKEN env var..."
  if validate_token "$CLAUDE_CODE_OAUTH_TOKEN"; then
    TOKEN="$CLAUDE_CODE_OAUTH_TOKEN"
    echo "  ✓ Valid token from Claude Code session"
  else
    echo "  ✗ Env var token is invalid or expired"
  fi
fi

# 2. macOS Keychain
if [[ -z "$TOKEN" ]] && command -v security &>/dev/null; then
  echo "Trying macOS Keychain..."
  KEYCHAIN_JSON=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null || true)
  if [[ -n "$KEYCHAIN_JSON" ]]; then
    KEYCHAIN_TOKEN=$(echo "$KEYCHAIN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('claudeAiOauth',{}).get('accessToken',''))" 2>/dev/null || true)
    if [[ -n "$KEYCHAIN_TOKEN" ]] && validate_token "$KEYCHAIN_TOKEN"; then
      TOKEN="$KEYCHAIN_TOKEN"
      echo "  ✓ Valid token from macOS Keychain"
    else
      echo "  ✗ Keychain token is invalid or expired"
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
    echo "  ✗ Token is not valid (API returned non-200)"
    exit 1
  fi
  echo "  ✓ Token validated"
fi

# ── Apply to all apps ────────────────────────────────────────────────────────

APP_ENVS=$(find_app_envs)

if [[ -z "$APP_ENVS" ]]; then
  echo "No apps with .env found under $REPO_ROOT/apps/"
  exit 1
fi

echo ""
echo "Updating apps..."

while IFS= read -r env_file; do
  app_dir=$(dirname "$env_file")
  app_name=$(basename "$app_dir")

  # Only update if the .env has or should have CLAUDE_CODE_OAUTH_TOKEN
  if grep -q "CLAUDE_CODE_OAUTH_TOKEN" "$env_file" 2>/dev/null; then
    write_env_token "$TOKEN" "$env_file"
    write_auth_profiles "$TOKEN" "$app_dir"
    echo "  ✓ $app_name"
  else
    echo "  - $app_name (no CLAUDE_CODE_OAUTH_TOKEN in .env, skipped)"
  fi
done <<< "$APP_ENVS"

echo ""
echo "Done. Restart dev servers to pick up the new token."
