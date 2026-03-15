---
description: Gain understanding of this project's Claude Code configuration and skills
---

# Prime — Claude Code Config (Experience QA)

## Step 1: Load project prime first
Run `/prime` (or read @.claude/commands/prime.md) for project context.

## Step 2: Read Claude Code configuration

- @CLAUDE.md
- @.claude/settings.json (if it exists)

## Step 3: Load based on task

**If working on skills/commands:**
Use Glob to list: `.claude/commands/**/*.md`
Then read only the specific command files you need.

**If working on skills (`.claude/skills/`):**
Use Glob to list: `.claude/skills/**/*`
Then read the relevant `SKILL.md` first before any other files in that skill.

**Available skills in this project:**
- `fluffyjaws` — query FluffyJaws internal AI (`fj chat`)
- `aio` — Adobe I/O App Builder CLI operations
- `meta-skill` — create new skills

## Step 4: Report

Summarize:
1. Project Claude Code rules (from CLAUDE.md)
2. Available commands and skills
3. Specific configuration relevant to current task
