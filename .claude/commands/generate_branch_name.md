---
description: Generate a git branch name from an issue title and type
argument-hint: "<issue-number> <issue-type> <issue-title>"
---

# Generate Branch Name

Generate a clean git branch name.

## Input

$1

## Rules

- Format: `{type}-{issue_number}-{slug}`
- Type mapping: `/feature` → `feat`, `/bug` → `fix`, `/chore` → `chore`
- Slug: lowercase, hyphens only, max 40 chars, no special characters
- Examples:
  - `feat-42-add-schedule-management-ui`
  - `fix-17-cancel-button-run-progress`
  - `chore-8-update-progress-docs`

## Output

Output ONLY the branch name string, nothing else. No quotes, no markdown, no explanation.
