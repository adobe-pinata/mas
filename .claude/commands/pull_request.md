---
description: Create a GitHub pull request for the current branch
argument-hint: "<issue number> <summary of changes>"
allowed-tools: Bash
---

# Create Pull Request

Create a pull request for the current branch linking to the issue.

## Context

$1

## Steps

1. Get current branch: `git branch --show-current`
2. Get recent commits: `git log main..HEAD --oneline`
3. Create PR with `gh pr create`:

```bash
gh pr create \
  --title "<conventional commit style title>" \
  --body "$(cat <<'EOF'
## Summary
<2-3 bullet points of what changed>

## Issue
Closes #<issue-number>

## Test plan
- [ ] Server starts without errors (`npm run dev:server`)
- [ ] Client builds without errors (`npm run build --workspace=apps/experience-qa/client`)
- [ ] Manual smoke test of changed functionality
EOF
)" \
  --base main
```

Output the PR URL when done.
