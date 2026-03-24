---
description: Mark a feature or task as complete — updates PROGRESS.md, archives the plan spec if one exists, and suggests mental model self-improve.
argument-hint: "<what you just finished>"
---

# Done — Complete a Feature

## Variables

WORK_DESCRIPTION: $1       # what was just finished (required)
SPEC_FILE: $2              # optional: path to the plan spec to archive (e.g. specs/schedule-ui-plan.md)

## Instructions

If WORK_DESCRIPTION is empty, stop and ask the user what was finished.

### Step 1 — Update PROGRESS.md

Read `specs/PROGRESS.md`.

Find the row or bullet that matches WORK_DESCRIPTION (fuzzy match on keywords).

- If found in **Open Items**: move it to the appropriate completed table, change 🔲 → ✅, add today's date as a note.
- If found in a spec table with 🚧: change 🚧 → ✅, add note.
- If it's a new item not yet tracked: add a new ✅ row to the most relevant section.

Update the `_Last updated_` date at the top of PROGRESS.md.

### Step 2 — Archive spec (if provided)

If SPEC_FILE is set and the file exists at that path:
- Move it to `specs/archive/` using `mv`
- Confirm the move succeeded

If SPEC_FILE is not set, check if any file matching `specs/*plan*.md` or `specs/*spec*.md` was recently created (use `git log --diff-filter=A --name-only -5` to find recently added spec files).
- If exactly one candidate is found, ask the user: "Archive `<filename>`?"
- If multiple candidates or none, skip and note it.

### Step 3 — Suggest mental model self-improve

Based on what WORK_DESCRIPTION touched, suggest which mental model(s) to sync so expertise stays accurate:

| Changed | Suggest |
|---------|---------|
| Server actions, services, storage, runner | `/mental-model:experience-server:self-improve` |
| Client pages, components, api.js | `/mental-model:experience-frontend:self-improve` |
| Jira, Slack, WCS, AOS, webhooks | `/mental-model:experience-integrations:self-improve` |

Print the suggestion — do not run it automatically.

### Step 4 — Report

Print a brief summary:
```
✅ Marked complete: <WORK_DESCRIPTION>
📦 Archived: <spec file or "none">
🔁 Run next: <mental model self-improve command or "none needed">
```
