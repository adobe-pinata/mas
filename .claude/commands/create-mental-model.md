---
name: create-mental-model
allowed-tools: Read, Write, Glob, Grep, Bash, TodoWrite, Agent
description: Generate a complete mental model set (expertise.yaml + 4 commands) for a single codebase domain. Single-domain and composable — chain multiple invocations for multi-domain setups, passing the prior domain as $3 for upstream context.
argument-hint: [domain] [scope] [upstream_domain (optional)]
---

# Create Mental Model

Generates a full 5-file mental model system for a given codebase domain.

**Reference pattern:** `.claude/commands/mental-model/adw/` — read all 5 files before generating anything.
**Templates:** `.claude/skills/meta-mental-model/templates/`

---

## Variables

DOMAIN: $1          # e.g., experience-server, experience-frontend
SCOPE: $2           # plain-English description of what this domain covers
UPSTREAM_DOMAIN: $3 # optional — if set, read its expertise.yaml first as upstream contract context

---

## Workflow

### Step 1 — Load Upstream Context (conditional)

If UPSTREAM_DOMAIN is set:
- Read `.claude/commands/mental-model/UPSTREAM_DOMAIN/expertise.yaml`
- Note the upstream API contracts, data shapes, and integration points this domain depends on
- These are binding constraints the new domain's expertise must respect

### Step 2 — Load the ADW Mental Model Pattern

Read all 5 ADW mental model files as the canonical reference:
- `.claude/commands/mental-model/adw/expertise.yaml`
- `.claude/commands/mental-model/adw/plan.md`
- `.claude/commands/mental-model/adw/question.md`
- `.claude/commands/mental-model/adw/self-improve.md`
- `.claude/commands/mental-model/adw/plan_build_improve.md`

Also read both templates:
- `.claude/skills/meta-mental-model/templates/expertise-template.yaml`
- `.claude/skills/meta-mental-model/templates/commands-template.md`

Internalize: what makes expertise.yaml useful is **accurate file paths, real function names, and architectural decisions** — not generic descriptions.

### Step 3 — Explore the Codebase for the Domain

Based on SCOPE, use Glob and Grep to find the real files, functions, and patterns. Do not invent — only document what exists.

Collect:
- Key file paths (store as relative from project root)
- Exported function names and signatures
- Data shapes and schemas
- Architectural patterns unique to this domain
- Integration points with other parts of the system
- Known gotchas (non-obvious facts that trip up engineers)

> Aim for 150–400 lines in expertise.yaml. Prioritize actionable facts over prose.

### Step 4 — Generate expertise.yaml

Write `.claude/commands/mental-model/DOMAIN/expertise.yaml`.

Every file path listed must actually exist (verified in Step 3). Max 1000 lines.

### Step 5 — Generate the 4 Command Files

Write these files under `.claude/commands/mental-model/DOMAIN/`:

**`plan.md`** — `name: DOMAIN-plan`; loads expertise.yaml, reads relevant source files, delegates to `/plan`

**`question.md`** — `name: DOMAIN-question`; read-only Q&A, validates expertise against codebase before answering

**`self-improve.md`** — `name: DOMAIN-self-improve`; validates expertise.yaml against actual codebase, enforces ≤1000 line limit, validates YAML syntax

**`plan_build_improve.md`** — `name: DOMAIN-plan-build-improve`; chains `/mental-model:DOMAIN:plan` → `/implement` → `/mental-model:DOMAIN:self-improve true`

### Step 6 — Validate

```bash
python3 -c "import yaml; yaml.safe_load(open('.claude/commands/mental-model/DOMAIN/expertise.yaml')); print('YAML valid')"
wc -l .claude/commands/mental-model/DOMAIN/expertise.yaml
```

Fix any YAML errors. If line count > 1000, trim least-critical prose until ≤ 1000.

### Step 7 — Report

```
Mental Model Created: DOMAIN

Files written:
- .claude/commands/mental-model/DOMAIN/expertise.yaml  (N lines)
- .claude/commands/mental-model/DOMAIN/plan.md
- .claude/commands/mental-model/DOMAIN/question.md
- .claude/commands/mental-model/DOMAIN/self-improve.md
- .claude/commands/mental-model/DOMAIN/plan_build_improve.md

Upstream context used: UPSTREAM_DOMAIN (or none)
Key files documented: N
Functions/classes captured: N
Gotchas noted: N

Skills registered as:
- /mental-model:DOMAIN:plan
- /mental-model:DOMAIN:question
- /mental-model:DOMAIN:self-improve
- /mental-model:DOMAIN:plan_build_improve

Next: run /mental-model:DOMAIN:self-improve to validate accuracy against live codebase.
```

---

## Composable Multi-Domain Pattern

To create a full set with dependency ordering, chain invocations:

```
/create-mental-model experience-server "AIO Runtime serverless backend..."
/create-mental-model experience-frontend "React 18 SPA..." experience-server
/create-mental-model experience-integrations "External service integrations..." experience-server
```

Each domain reads the prior domain's expertise as upstream contract context before generating its own.
