---
name: meta-experts
description: Generates a complete expert set for a codebase domain. Creates expertise.yaml (living knowledge doc) plus four slash commands (plan, question, self-improve, plan_build_improve) under .claude/commands/experts/<domain>/. Use when the user says "create an expert for...", "add experts for...", or "use meta-experts to...".
allowed-tools: Read, Write, Glob, Grep, Bash, TodoWrite
---

# Meta-Experts

Generates a full 5-file expert system for a given codebase domain, following the ADW expert pattern.

**Reference example:** `.claude/commands/experts/adw/` — read all 5 files before generating anything.

**Templates:** `templates/` directory contains canonical skeletons for each file.

---

## Variables

DOMAIN: $1          # e.g., eqa-server, eqa-client, eqa-integrations
SCOPE: $2           # plain-English description of what the expert covers

---

## Workflow

### Step 1 — Load the ADW Expert Pattern

Read all 5 ADW expert files as the canonical reference:
- `.claude/commands/experts/adw/expertise.yaml`
- `.claude/commands/experts/adw/plan.md`
- `.claude/commands/experts/adw/question.md`
- `.claude/commands/experts/adw/self-improve.md`
- `.claude/commands/experts/adw/plan_build_improve.md`

Also read `templates/expertise-template.yaml` and `templates/commands-template.md` for the skeleton structures.

Internalize: what makes expertise.yaml useful is **accurate file paths, real function names, and architectural decisions** — not generic descriptions.

### Step 2 — Explore the Codebase for the Domain

Based on SCOPE, use Glob and Grep to find the real files, functions, and patterns for this domain. Do not invent — only document what exists.

Collect:
- Key file paths (absolute → store as relative from project root)
- Exported function names and signatures
- Data shapes / schemas
- Architectural patterns unique to this domain
- Integration points with other parts of the system
- Known gotchas (e.g., "NOT Express — AIO Runtime OpenWhisk")

> Aim for 150–400 lines in expertise.yaml. Prioritize actionable facts over prose.

### Step 3 — Generate expertise.yaml

Write `.claude/commands/experts/DOMAIN/expertise.yaml`.

Structure (adapt sections to the domain):
```yaml
# <DOMAIN> Implementation Expertise
# <One-line tagline>

overview:
  description: "..."
  core_insight: "..."
  architecture_pattern: "..."

key_files:
  <logical_group>:
    <name>:
      file: "<relative path>"
      purpose: "..."
      key_functions/key_classes: ...

patterns:
  <pattern_name>: |
    <how this domain implements X>

gotchas:
  - "..."

best_practices:
  - "..."
```

Validate: every file path listed must actually exist (verified in Step 2).

### Step 4 — Generate the 4 Command Files

Write these files, adapted from the ADW templates but referencing DOMAIN:

**`.claude/commands/experts/DOMAIN/plan.md`**
- Frontmatter: `name: DOMAIN-plan`, appropriate `allowed-tools`, `description`
- Body: loads expertise.yaml for DOMAIN, then delegates to `/plan`

**`.claude/commands/experts/DOMAIN/question.md`**
- Frontmatter: `name: DOMAIN-question`, `allowed-tools: Read, Bash, TodoWrite`
- Body: Q&A only — reads expertise, validates against codebase, answers without writing files

**`.claude/commands/experts/DOMAIN/self-improve.md`**
- Frontmatter: `name: DOMAIN-self-improve`, `allowed-tools: Read, Grep, Glob, Bash, Edit, Write, TodoWrite`
- Body: validates expertise.yaml against actual codebase, updates discrepancies, enforces ≤1000 line limit

**`.claude/commands/experts/DOMAIN/plan_build_improve.md`**
- Frontmatter: `name: DOMAIN-plan-build-improve`, `allowed-tools: Task, TaskOutput, TodoWrite`
- Body: chains plan → build → self-improve as sequential subagents

### Step 5 — Validate

- Confirm all 5 files exist under `.claude/commands/experts/DOMAIN/`
- Run: `python3 -c "import yaml; yaml.safe_load(open('.claude/commands/experts/DOMAIN/expertise.yaml'))"` to validate YAML
- Count lines: `wc -l .claude/commands/experts/DOMAIN/expertise.yaml` — must be ≤ 1000
- Print the skill registration block the user should add to their skills config

### Step 6 — Report

```
Meta-Expert Created: DOMAIN

Files written:
- .claude/commands/experts/DOMAIN/expertise.yaml  (N lines)
- .claude/commands/experts/DOMAIN/plan.md
- .claude/commands/experts/DOMAIN/question.md
- .claude/commands/experts/DOMAIN/self-improve.md
- .claude/commands/experts/DOMAIN/plan_build_improve.md

Expertise coverage:
- Key files documented: N
- Functions/classes captured: N
- Gotchas noted: N

Skills registered as:
- /experts:DOMAIN:plan
- /experts:DOMAIN:question
- /experts:DOMAIN:self-improve
- /experts:DOMAIN:plan_build_improve
- /experts:DOMAIN:plan_build_improve (end-to-end)

Next: run /experts:DOMAIN:self-improve to validate accuracy against live codebase.
```
