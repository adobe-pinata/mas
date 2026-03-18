#!/bin/bash

# Cleanup script for ADW worktrees and branches
# Supports multi-app: APP=content-qa ./scripts/cleanup_worktrees.sh

set -e

echo "🧹 Starting worktree and branch cleanup..."
echo ""

# Get the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Resolve trees directory
if [ -n "$APP" ]; then
    TREES_DIR="apps/${APP}/trees"
    echo "📦 App: ${APP}"
else
    TREES_DIR="trees"
fi

# Clean git worktrees (only relevant when APP is not set)
if [ -z "$APP" ]; then
    WORKTREE_COUNT=$(git worktree list | grep -c "^" || true)
    WORKTREE_COUNT=$((WORKTREE_COUNT - 1))  # Exclude main worktree

    if [ "$WORKTREE_COUNT" -gt 0 ]; then
        echo "📊 Found $WORKTREE_COUNT git worktrees to remove"
        echo ""
        echo "🗑️  Removing worktrees..."
        git worktree list | grep -v "^\/" | awk '{print $1}' | while read -r worktree_path; do
            if [ -n "$worktree_path" ] && [ -d "$worktree_path" ]; then
                echo "  Removing: $worktree_path"
                git worktree remove "$worktree_path" --force 2>/dev/null || true
            fi
        done
        echo ""
        echo "🌿 Pruning worktree metadata..."
        git worktree prune
    fi
fi

# Clean trees directory (clones for app-layer, worktree dirs for agentic)
echo ""
if [ -d "$TREES_DIR" ]; then
    CLONE_COUNT=$(ls -d "$TREES_DIR"/*/ 2>/dev/null | wc -l | tr -d ' ')
    if [ "$CLONE_COUNT" -gt 0 ]; then
        echo "🗑️  Removing $CLONE_COUNT tree(s) from ${TREES_DIR}/..."
        for tree in "$TREES_DIR"/*/; do
            [ -d "$tree" ] || continue
            adw_id=$(basename "$tree")
            echo "  Removing: ${adw_id}"
            rm -rf "$tree"
            # Also remove agent state
            if [ -d "agents/${adw_id}" ]; then
                rm -rf "agents/${adw_id}"
                echo "    ✓ Agent state removed"
            fi
        done
    else
        echo "✨ No trees to clean up in ${TREES_DIR}/"
    fi
else
    echo "✨ No ${TREES_DIR}/ directory found"
fi

# Delete ADW-related branches (only when cleaning agentic harness)
if [ -z "$APP" ]; then
    echo ""
    echo "🗑️  Deleting branches..."
    git branch --list "adw-*" "bug-*" "feature-*" "feat-*" "chore-*" | while read -r branch; do
        branch=$(echo "$branch" | sed 's/^[* ]*//;s/ *$//')
        if [ -n "$branch" ]; then
            echo "  Deleting: $branch"
            git branch -D "$branch" 2>/dev/null || true
        fi
    done

    echo ""
    echo "🧹 Running git cleanup..."
    git gc --prune=now --aggressive 2>/dev/null || git gc --prune=now
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Final status:"
[ -n "$APP" ] && echo "  App: ${APP}"
echo "  Trees dir: ${TREES_DIR}"
REMAINING=$(ls -d "$TREES_DIR"/*/ 2>/dev/null | wc -l | tr -d ' ')
echo "  Remaining trees: ${REMAINING}"
if [ -z "$APP" ]; then
    echo "  Remaining worktrees: $(git worktree list | grep -c "^")"
    echo "  Remaining ADW branches: $(git branch --list "adw-*" "bug-*" "feature-*" "feat-*" "chore-*" | wc -l | tr -d ' ')"
fi
