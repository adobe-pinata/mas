#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if ADW ID is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: ADW ID required${NC}"
    echo "Usage: $0 <ADW_ID> [--keep-branch]"
    echo "  APP=content-qa $0 ADW-123   # Purge from apps/content-qa/trees/"
    echo "  $0 ADW-123                  # Purge from trees/ (agentic harness)"
    echo "  $0 ADW-123 --keep-branch    # Keep the git branch"
    exit 1
fi

ADW_ID=$1
DELETE_BRANCH=true

# Check for --keep-branch flag
if [ "$2" == "--keep-branch" ]; then
    DELETE_BRANCH=false
fi

# Resolve worktree path — APP scopes to apps/{app}/trees/
if [ -n "$APP" ]; then
    WORKTREE_PATH="apps/${APP}/trees/${ADW_ID}"
    echo -e "${BLUE}Purging worktree for ${ADW_ID} (app: ${APP})...${NC}"
else
    WORKTREE_PATH="trees/${ADW_ID}"
    echo -e "${BLUE}Purging worktree for ${ADW_ID}...${NC}"
fi
echo ""

# Check if worktree exists
if [ ! -d "$WORKTREE_PATH" ]; then
    echo -e "${YELLOW}Warning: Worktree directory not found at $WORKTREE_PATH${NC}"
else
    echo -e "${GREEN}Found worktree at: $WORKTREE_PATH${NC}"
fi

# Determine if this is a standalone clone or a git worktree
IS_CLONE=false
if [ -d "$WORKTREE_PATH/.git" ]; then
    IS_CLONE=true
fi

# Get branch name
BRANCH_NAME=""
if [ "$IS_CLONE" == "true" ] && [ -d "$WORKTREE_PATH" ]; then
    # For clones, read the branch from git inside the clone
    BRANCH_NAME=$(git -C "$WORKTREE_PATH" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
    [ -n "$BRANCH_NAME" ] && echo -e "${GREEN}Associated branch: $BRANCH_NAME${NC}"
else
    # For worktrees, check git worktree list
    BRANCH_NAME=$(git worktree list --porcelain | grep -A1 "worktree.*${WORKTREE_PATH}" | grep "branch" | cut -d' ' -f2 | sed 's|refs/heads/||')
    if [ -z "$BRANCH_NAME" ]; then
        ADW_ID_LOWER=$(echo "$ADW_ID" | tr '[:upper:]' '[:lower:]')
        POSSIBLE_BRANCHES=$(git branch -a | grep -i "adw-${ADW_ID_LOWER}" | sed 's/^[* ]*//' | grep -v "remotes/")
        if [ ! -z "$POSSIBLE_BRANCHES" ]; then
            BRANCH_COUNT=$(echo "$POSSIBLE_BRANCHES" | wc -l | tr -d ' ')
            if [ "$BRANCH_COUNT" -eq "1" ]; then
                BRANCH_NAME=$(echo "$POSSIBLE_BRANCHES" | head -1)
                echo -e "${YELLOW}Inferred branch from ADW ID: $BRANCH_NAME${NC}"
            else
                echo -e "${YELLOW}Found multiple branches — will not delete (ambiguous)${NC}"
                DELETE_BRANCH=false
            fi
        else
            echo -e "${YELLOW}Warning: Could not determine branch name${NC}"
        fi
    else
        echo -e "${GREEN}Associated branch: $BRANCH_NAME${NC}"
    fi
fi

# Kill any processes using ports for this ADW
echo ""
echo -e "${GREEN}Checking for processes on ADW ports...${NC}"

hash_value=$(echo -n "$ADW_ID" | md5sum | cut -c1-8)
port_offset=$((0x${hash_value} % 15))
backend_port=$((9100 + port_offset))
frontend_port=$((9200 + port_offset))

backend_pid=$(lsof -ti:$backend_port 2>/dev/null)
if [ ! -z "$backend_pid" ]; then
    kill -9 $backend_pid 2>/dev/null
    echo -e "${YELLOW}  Killed process on backend port $backend_port${NC}"
else
    echo -e "${GREEN}  No process on backend port $backend_port${NC}"
fi

frontend_pid=$(lsof -ti:$frontend_port 2>/dev/null)
if [ ! -z "$frontend_pid" ]; then
    kill -9 $frontend_pid 2>/dev/null
    echo -e "${YELLOW}  Killed process on frontend port $frontend_port${NC}"
else
    echo -e "${GREEN}  No process on frontend port $frontend_port${NC}"
fi

# Remove worktree/clone
echo ""
echo -e "${GREEN}Removing worktree...${NC}"
if [ "$IS_CLONE" == "true" ]; then
    # Standalone clone — just remove the directory
    if [ -d "$WORKTREE_PATH" ]; then
        rm -rf "$WORKTREE_PATH"
        echo -e "${GREEN}  ✓ Clone directory removed${NC}"
    fi
else
    # Git worktree
    if git worktree list | grep -q "$WORKTREE_PATH"; then
        git worktree remove -f "$WORKTREE_PATH" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ Worktree removed from git${NC}"
        else
            echo -e "${RED}  Failed to remove worktree from git${NC}"
            git worktree prune
        fi
    else
        echo -e "${YELLOW}  Worktree not registered in git${NC}"
    fi
    # Remove directory if it still exists
    if [ -d "$WORKTREE_PATH" ]; then
        rm -rf "$WORKTREE_PATH"
        echo -e "${GREEN}  ✓ Worktree directory removed${NC}"
    fi
fi

# Remove agent state
if [ -d "agents/${ADW_ID}" ]; then
    rm -rf "agents/${ADW_ID}"
    echo -e "${GREEN}  ✓ Agent state removed${NC}"
fi

# Handle branch deletion
if [ "$DELETE_BRANCH" == "true" ] && [ ! -z "$BRANCH_NAME" ]; then
    echo ""
    echo -e "${GREEN}Deleting branch: $BRANCH_NAME${NC}"

    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" == "$BRANCH_NAME" ]; then
        echo -e "${YELLOW}  Switching to main branch first...${NC}"
        git checkout main
    fi

    git branch -D "$BRANCH_NAME" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Local branch deleted${NC}"
    else
        echo -e "${YELLOW}  Could not delete local branch (may not exist)${NC}"
    fi

    echo -e "${YELLOW}  Note: Remote branch not deleted. To delete it, run:${NC}"
    echo -e "${BLUE}    git push origin --delete $BRANCH_NAME${NC}"
fi

git worktree prune 2>/dev/null || true

echo ""
echo -e "${GREEN}✓ Purge complete for ${ADW_ID}${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  ADW ID: ${ADW_ID}"
[ -n "$APP" ] && echo -e "  App: ${APP}"
echo -e "  Worktree path: ${WORKTREE_PATH}"
[ ! -z "$BRANCH_NAME" ] && echo -e "  Branch: ${BRANCH_NAME}"
echo -e "  Backend port: ${backend_port}"
echo -e "  Frontend port: ${frontend_port}"
