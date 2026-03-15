#!/bin/bash

# Clear all comments from a GitHub issue
# Usage: ./scripts/clear_issue_comments.sh <issue-number>

set -e

# Check if issue number is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <issue-number>"
    echo "Example: $0 123"
    exit 1
fi

ISSUE_NUMBER=$1

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Get repository URL from git remote
GITHUB_REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$GITHUB_REPO_URL" ]; then
    echo "Error: Not in a git repository or no 'origin' remote found"
    exit 1
fi

# Extract repo path from URL (handle both HTTPS and SSH)
REPO_PATH=$(echo $GITHUB_REPO_URL | sed 's|https://github.com/||' | sed 's|git@github.com:||' | sed 's|.git$||')

# Set GitHub token for gh CLI if available
if [ -n "$GITHUB_PAT" ]; then
    export GH_TOKEN=$GITHUB_PAT
fi

echo "Fetching comments for issue #$ISSUE_NUMBER in $REPO_PATH..."

# Get all comment IDs for the issue
COMMENT_IDS=$(gh api \
    repos/$REPO_PATH/issues/$ISSUE_NUMBER/comments \
    --jq '.[].id' \
    2>&1)

# Check if the API call failed
if echo "$COMMENT_IDS" | grep -q "HTTP 404"; then
    echo "❌ Error: Issue #$ISSUE_NUMBER not found or no access to repository $REPO_PATH"
    exit 1
fi

if [ -z "$COMMENT_IDS" ]; then
    echo "No comments found on issue #$ISSUE_NUMBER"
    exit 0
fi

# Count comments
COMMENT_COUNT=$(echo "$COMMENT_IDS" | wc -l | tr -d ' ')
echo "Found $COMMENT_COUNT comment(s) to delete"

# Track deletion results
DELETED=0
FAILED=0

# Delete each comment
for COMMENT_ID in $COMMENT_IDS; do
    echo "Deleting comment $COMMENT_ID..."
    DELETE_RESULT=$(gh api \
        --method DELETE \
        repos/$REPO_PATH/issues/comments/$COMMENT_ID \
        2>&1)

    if [ $? -eq 0 ]; then
        DELETED=$((DELETED + 1))
    else
        FAILED=$((FAILED + 1))
        echo "❌ Failed to delete comment $COMMENT_ID: $DELETE_RESULT"
    fi
done

echo ""
echo "Deletion Summary:"
echo "  ✅ Deleted: $DELETED"
echo "  ❌ Failed: $FAILED"

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "⚠️  Some comments could not be deleted. This may be due to:"
    echo "   - Insufficient permissions (need 'repo' scope in GitHub token)"
    echo "   - Comments were already deleted"
    echo "   - Network or API issues"
    exit 1
fi

echo ""
echo "✅ Successfully deleted all $DELETED comments from issue #$ISSUE_NUMBER"
