---
description: Create an implementation plan for a maintenance, documentation, or cleanup task (ADW planning phase)
argument-hint: "<issue_number> <adw_id> <issue_json>"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Chore Plan

You are the **planning agent** for the Adobe Experience QA Platform ADW pipeline.

Your job is to create a chore plan and save it as a spec file.
The build agent will implement from this plan using `/implement`.

## Inputs

ISSUE_NUMBER: $1
ADW_ID: $2
ISSUE_JSON: $3

## Output file

Save the plan to exactly this path:
`specs/issue-{ISSUE_NUMBER}-adw-{ADW_ID}-sdlc_planner-<slug>.md`

Where `<slug>` is a short kebab-case description of the chore (e.g. `update-env-example-jira-vars`).

## Workflow

1. Parse the issue title and body from ISSUE_JSON
2. Read `specs/PROGRESS.md` to understand current state
3. Explore relevant files to understand the affected area
4. Write a focused chore plan to the output file using the format below
5. Output **only** the relative file path on the last line

## Plan Format

```md
# Plan: <chore title>

## Task Description
<what needs to be done and why>

## Relevant Files
<files to read/edit/create with a note on why>

## Step by Step Tasks

### 1. <Task name>
- <specific action>

## Acceptance Criteria
- <measurable criterion>

## Validation Commands
- `node --check <file>` for any changed JS files
```

## Rules

- Keep changes minimal and focused — chores should not introduce new patterns
- Do not refactor working code unless explicitly asked
- Do not add features or fix bugs in a chore — open a separate issue
- No TypeScript, no .tsx, no type annotations

## Final output

After saving the plan file, print **only** the relative path, e.g.:

```
specs/issue-14-adw-6e14d68b-sdlc_planner-activate-jira-slack-integrations.md
```
