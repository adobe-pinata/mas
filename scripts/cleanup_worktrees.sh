#!/bin/bash

# Cleanup script for ADW worktrees and branches
# This script removes all worktrees except the main one and deletes associated branches

set -e

echo "🧹 Starting worktree and branch cleanup..."
echo ""

# Get the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Count worktrees
WORKTREE_COUNT=$(git worktree list | grep -c "^" || true)
WORKTREE_COUNT=$((WORKTREE_COUNT - 1))  # Exclude main worktree

if [ "$WORKTREE_COUNT" -eq 0 ]; then
    echo "✨ No worktrees to clean up!"
    exit 0
fi

echo "📊 Found $WORKTREE_COUNT worktrees to remove"
echo ""

# Remove all worktrees except main
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

echo ""
echo "🗑️  Deleting branches..."
# Delete all ADW-related branches
git branch --list "adw-*" "bug-*" "feature-*" "feat-*" "chore-*" | while read -r branch; do
    # Remove leading whitespace and markers
    branch=$(echo "$branch" | sed 's/^[* ]*//;s/ *$//')
    if [ -n "$branch" ]; then
        echo "  Deleting: $branch"
        git branch -D "$branch" 2>/dev/null || true
    fi
done

echo ""
echo "📁 Cleaning up trees directory..."
if [ -d "trees" ]; then
    rm -rf trees/*
    echo "  ✓ trees/ directory cleaned"
fi

echo ""
echo "🧹 Running git cleanup..."
git gc --prune=now --aggressive 2>/dev/null || git gc --prune=now

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Final status:"
echo "  Remaining worktrees: $(git worktree list | grep -c "^")"
echo "  Remaining ADW branches: $(git branch --list "adw-*" "bug-*" "feature-*" "feat-*" "chore-*" | wc -l | tr -d ' ')"
