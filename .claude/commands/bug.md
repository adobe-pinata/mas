---
description: Create an implementation plan to fix a bug (ADW planning phase)
argument-hint: "<issue_number> <adw_id> <issue_json>"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Bug Fix Plan

You are the **planning agent** for the Adobe Experience QA Platform ADW pipeline.

Your job is to create a bug fix plan and save it as a spec file.
The build agent will implement from this plan using `/implement`.

## Inputs

ISSUE_NUMBER: $1
ADW_ID: $2
ISSUE_JSON: $3

## Output file

Save the plan to exactly this path:
`specs/issue-{ISSUE_NUMBER}-adw-{ADW_ID}-sdlc_planner-<slug>.md`

Where `<slug>` is a short kebab-case description of the fix (e.g. `fix-auth-token-expiry`).

## Workflow

1. Parse the issue title and body from ISSUE_JSON
2. Read `specs/DECISIONS.md` — check applicable gotchas (oat01 x-api-key, Promise returns, etc.)
3. Trace the error path in code to find root cause
4. Write a focused fix plan to the output file
5. Output **only** the relative file path on the last line

## Plan Format

```md
# Plan: Fix <bug title>

## Bug Description
<what is broken and how it manifests>

## Root Cause
<where in the code the bug originates>

## Relevant Files
<files to read and edit>

## Step by Step Tasks

### 1. <Task>
- <specific action>

## Acceptance Criteria
- <measurable criterion>

## Validation Commands
- `node --check <file>` for changed JS files
```

## Rules

- Fix minimum surface area — no refactoring beyond the bug
- Do NOT add TypeScript or change file extensions
- If bug is in `oauth.js`: verify `x-api-key` header (not `Authorization: Bearer`)
- If bug is storage-related: check async methods return Promises

## Final output

After saving the plan file, print **only** the relative path, e.g.:

```
specs/issue-2-adw-00b193f3-sdlc_planner-fix-auth-token-expiry.md
```
