---
description: Create an implementation plan for a new feature (ADW planning phase)
argument-hint: "<issue_number> <adw_id> <issue_json>"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Feature Plan

You are the **planning agent** for the Adobe Experience QA Platform ADW pipeline.

Your job is to create a detailed implementation plan and save it as a spec file.
The build agent will implement from this plan using `/implement`.

## Inputs

ISSUE_NUMBER: $1
ADW_ID: $2
ISSUE_JSON: $3

## Output file

Save the plan to exactly this path:
`specs/issue-{ISSUE_NUMBER}-adw-{ADW_ID}-sdlc_planner-<slug>.md`

Where `<slug>` is a short kebab-case description of the feature (e.g. `cancel-button-run-progress`).

## Workflow

1. Parse the issue title and body from ISSUE_JSON
2. Read `specs/DECISIONS.md` — check for applicable constraints (no TypeScript, no Redux, inline CSS)
3. Explore relevant files in the codebase to understand the affected area
4. Write a complete implementation plan to the output file using the format below
5. Output **only** the relative file path on the last line (nothing else after it)

## Plan Format

```md
# Plan: <feature title>

## Task Description
<what needs to be built, based on the issue>

## Relevant Files
<list files to read/edit/create with a note on why>

## Step by Step Tasks

### 1. <Task name>
- <specific action>

### 2. <Task name>
- <specific action>

## Acceptance Criteria
- <measurable criterion>

## Validation Commands
- `node --check <file>` for any new JS files
```

## Stack constraints (from DECISIONS.md)

- No TypeScript, no .tsx, no type annotations
- Client: React JSX, inline CSS objects, useState only (no Redux)
- `@adobe/react-spectrum` Provider + Toast only — no other Spectrum components
- Server: Node.js ESM, Express routes + AIO actions mirror pattern
- Run `node --check <file>` to validate JS syntax

## Final output

After saving the plan file, print **only** the relative path, e.g.:

```
specs/issue-1-adw-00b193f3-sdlc_planner-cancel-button-run-progress.md
```
