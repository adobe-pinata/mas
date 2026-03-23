# Mental Model — Naming Refactor + New Commands

## Problem Statement

The mental model system has three issues:
1. **Inconsistent domain naming** — `qa-server`, `frontend`, `qa-integrations` mix prefixes and lack a consistent convention
2. **Missing bootstrap command** — no single-domain, composable command to generate mental models
3. **Missing smart build command** — `plan_build_improve` exists per-domain but there is no cross-domain orchestrator that auto-detects which domains a request touches

## Decisions

| Current | Final |
|---|---|
| `qa-server` domain | `experience-server` |
| `frontend` domain | `experience-frontend` |
| `qa-integrations` domain | `experience-integrations` |
| `adw` domain | unchanged |
| `build-qa-mental-models.md` | `build-mental-models.md` (generalized orchestrator) |
| _(new)_ | `create-mental-model.md` — single-domain bootstrap |
| _(new)_ | `build-with-mental-models.md` — smart cross-domain workflow |

---

## Phase 1 — Rename Domains

### 1.1 Rename directories

```
.claude/commands/mental-model/qa-server/         → experience-server/
.claude/commands/mental-model/frontend/          → experience-frontend/
.claude/commands/mental-model/qa-integrations/   → experience-integrations/
```

### 1.2 Update frontmatter `name` fields inside each command file

For each domain, update the `name:` field in all 4 command files:

| File | Old name | New name |
|---|---|---|
| `experience-server/plan.md` | `qa-server-plan` | `experience-server-plan` |
| `experience-server/question.md` | `qa-server-question` | `experience-server-question` |
| `experience-server/self-improve.md` | `qa-server-self-improve` | `experience-server-self-improve` |
| `experience-server/plan_build_improve.md` | `qa-server-plan-build-improve` | `experience-server-plan-build-improve` |
| `experience-frontend/plan.md` | `frontend-plan` | `experience-frontend-plan` |
| `experience-frontend/question.md` | `frontend-question` | `experience-frontend-question` |
| `experience-frontend/self-improve.md` | `frontend-self-improve` | `experience-frontend-self-improve` |
| `experience-frontend/plan_build_improve.md` | `frontend-plan-build-improve` | `experience-frontend-plan-build-improve` |
| `experience-integrations/plan.md` | `qa-integrations-plan` | `experience-integrations-plan` |
| `experience-integrations/question.md` | `qa-integrations-question` | `experience-integrations-question` |
| `experience-integrations/self-improve.md` | `qa-integrations-self-improve` | `experience-integrations-self-improve` |
| `experience-integrations/plan_build_improve.md` | `qa-integrations-plan-build-improve` | `experience-integrations-plan-build-improve` |

### 1.3 Update all internal cross-references inside command files

Any `SlashCommand('/mental-model:qa-server:*')`, `SlashCommand('/mental-model:frontend:*')`, or `SlashCommand('/mental-model:qa-integrations:*')` references inside the command files themselves (especially `plan_build_improve.md` files) must be updated to use the new domain names.

Also update expertise file path references:
- `.claude/commands/mental-model/qa-server/expertise.yaml` → `experience-server/expertise.yaml`
- `.claude/commands/mental-model/frontend/expertise.yaml` → `experience-frontend/expertise.yaml`
- `.claude/commands/mental-model/qa-integrations/expertise.yaml` → `experience-integrations/expertise.yaml`

---

## Phase 2 — Rename `build-qa-mental-models` → `build-mental-models`

### 2.1 Rename the file

```
.claude/commands/build-qa-mental-models.md → .claude/commands/build-mental-models.md
```

### 2.2 Update internal content

- Frontmatter `name:` → `build-mental-models`
- Frontmatter `description:` — remove `QA` qualifier, make general
- All domain references: `qa-server` → `experience-server`, `frontend` → `experience-frontend`, `qa-integrations` → `experience-integrations`
- All directory paths in bash validation blocks
- All SlashCommand invocations in Task prompts
- Commit message at Step 4

---

## Phase 3 — Create `create-mental-model.md`

New single-domain bootstrap command. Replaces the ad-hoc use of the `meta-mental-model` skill for creating new domains.

### Spec

**File:** `.claude/commands/create-mental-model.md`

**Frontmatter:**
```yaml
name: create-mental-model
allowed-tools: Read, Write, Glob, Grep, Bash, TodoWrite, Agent
description: Generate a complete mental model set (expertise.yaml + 4 commands) for a single codebase domain. Single-domain and composable — chain multiple invocations for multi-domain setups, passing the prior domain's output as $3.
argument-hint: [domain] [scope] [upstream_domain (optional)]
```

**Variables:**
- `DOMAIN: $1` — domain identifier (e.g., `experience-server`)
- `SCOPE: $2` — plain-English description of what this domain covers
- `UPSTREAM_DOMAIN: $3` — optional; if set, read `.claude/commands/mental-model/$3/expertise.yaml` first as upstream contract context before generating this domain's expertise

**Workflow:**
1. If `UPSTREAM_DOMAIN` is set, read its `expertise.yaml` to understand the upstream contracts this domain depends on
2. Read the ADW mental model (canonical reference pattern): all 5 files under `.claude/commands/mental-model/adw/`
3. Read templates: `expertise-template.yaml` and `commands-template.md`
4. Explore the codebase for DOMAIN based on SCOPE — Glob and Grep for real files, function names, data shapes, patterns, gotchas
5. Generate `.claude/commands/mental-model/DOMAIN/expertise.yaml` (150–400 lines, hard cap 1000)
6. Generate the 4 command files: `plan.md`, `question.md`, `self-improve.md`, `plan_build_improve.md`
7. Validate: YAML syntax check + line count
8. Report files written, line count, and skill registration block

**Dependency pattern (multi-domain example):**
```
/create-mental-model experience-server "AIO Runtime serverless backend..."
/create-mental-model experience-frontend "React 18 SPA..." experience-server
/create-mental-model experience-integrations "External service integrations..." experience-server
```

---

## Phase 4 — Create `build-with-mental-models.md`

New cross-domain smart workflow command. Detects which domains a request touches, chains domain plans in dependency order, implements, and self-improves.

### Spec

**File:** `.claude/commands/build-with-mental-models.md`

**Frontmatter:**
```yaml
name: build-with-mental-models
allowed-tools: Task, TaskOutput, TodoWrite, Glob, Read, Grep
description: End-to-end implementation workflow. Auto-detects which mental model domains the request touches, chains expertise-informed plans in dependency order, implements, then self-improves all touched expertise files.
argument-hint: [implementation_request]
```

**Variables:**
- `USER_REQUEST: $1`

**Workflow:**

**Step 1 — Discover available domains**
- Glob `.claude/commands/mental-model/*/expertise.yaml`
- For each found domain, read only the `overview` section (first ~20 lines) to understand its scope

**Step 2 — Classify domains**
- Attempt file-based classification: grep/glob the codebase for files relevant to USER_REQUEST, map touched files to domains using `key_file_locations` from each expertise.yaml
- If file classification is inconclusive or ambiguous: load all available domains (over-inclusion is always safe; under-inclusion is the failure mode)
- Determine dependency order: server-layer domains before client-layer domains before integration-layer domains
- No confirmation step — proceed directly

**Step 3 — Chain domain plans**

For each domain in dependency order, spawn a sequential Task:
```
Task: Run /mental-model:DOMAIN:plan USER_REQUEST [prior_spec_path]
```
Each plan feeds its output spec as `$2` (prior_spec_path) to the next domain's plan.

**Step 4 — Implement**
```
Task: Run /implement [last_spec_path]
```

**Step 5 — Self-improve all touched domains**

Spawn parallel Tasks, one per touched domain:
```
Task: Run /mental-model:DOMAIN:self-improve true
```

**Step 6 — Report**
- Domains detected and why
- Plan files generated (one per domain)
- Build summary
- Self-improve results per domain

---

## Phase 5 — Update Cross-References

### Files to update

| File | What changes |
|---|---|
| `.claude/commands/prime.md` | Domain names in pipe pattern table + all invocation examples |
| `.claude/commands/scaffold.md` | `mental-model:frontend:plan` → `mental-model:experience-frontend:plan` |
| `.claude/commands/done.md` | Any domain name references |
| `.claude/skills/meta-mental-model/SKILL.md` | Stale examples `eqa-*` → `experience-*`; clarify relationship with `create-mental-model` |
| `docs/commands-reference.md` | 3 section headers + 12 command invocations + `build-qa-mental-models` entry → `build-mental-models`; add entries for `create-mental-model` and `build-with-mental-models` |
| `docs/experts-guide.md` | All domain names, invocation examples, pipe pattern examples, `build-qa-mental-models` references |
| `README.md` | Line 18 domain list |

---

## Acceptance Criteria

- [ ] All 3 domain directories renamed; old paths no longer exist
- [ ] All frontmatter `name` fields updated in 12 command files
- [ ] All internal cross-references updated (no remaining `qa-server`, `qa-integrations`, or bare `frontend` references in mental-model files)
- [ ] `build-mental-models.md` replaces `build-qa-mental-models.md`; old file gone
- [ ] `create-mental-model.md` exists and follows single-domain + optional upstream arg pattern
- [ ] `build-with-mental-models.md` exists with file-based domain detection + load-all fallback; no confirmation step
- [ ] `prime.md` pipe table uses new domain names
- [ ] `docs/commands-reference.md` fully updated including new command entries
- [ ] `docs/experts-guide.md` fully updated
- [ ] `README.md` updated
- [ ] `meta-mental-model/SKILL.md` stale examples fixed
- [ ] No broken slash command references anywhere in `.claude/`

## Validation

```bash
# No old domain names remain in mental-model command files
grep -r "qa-server\|qa-integrations\|mental-model:frontend" .claude/commands/mental-model/

# No old build command referenced anywhere
grep -r "build-qa-mental-models" .claude/ docs/ README.md

# All 5 files exist for each renamed domain
ls .claude/commands/mental-model/experience-server/
ls .claude/commands/mental-model/experience-frontend/
ls .claude/commands/mental-model/experience-integrations/

# New commands exist
ls .claude/commands/create-mental-model.md
ls .claude/commands/build-with-mental-models.md
ls .claude/commands/build-mental-models.md
```
