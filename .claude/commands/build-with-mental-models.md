---
name: build-with-mental-models
allowed-tools: Task, TaskOutput, TodoWrite, Glob, Read, Grep
description: End-to-end implementation workflow using mental models. Auto-detects which domains the request touches via file-based classification (falls back to loading all domains if ambiguous), chains expertise-informed plans in dependency order, implements, then self-improves all touched expertise files. No confirmation step.
argument-hint: [implementation_request]
---

# Build With Mental Models

Orchestrates a complete implementation cycle by auto-detecting which mental model domains are relevant, chaining domain-informed plans, building, then self-improving expertise files.

## Variables

USER_REQUEST: $1

## Instructions

- Do NOT stop between steps — complete the full workflow
- Over-inclusion of domains is always safe; under-inclusion is the failure mode
- Each Task subagent starts fresh — provide complete context in every prompt
- Use TaskOutput to retrieve results before proceeding to dependent steps

---

## Workflow

### Step 1 — Discover Available Domains

Glob `.claude/commands/mental-model/*/expertise.yaml` to find all available domains.

For each domain found, read only the first ~20 lines (the `overview` section) to understand its scope.

### Step 2 — Classify Domains (file-based, with load-all fallback)

**Attempt file-based classification:**
- Use Grep and Glob to identify which source files in the codebase are relevant to USER_REQUEST
- For each candidate file, check which domain's `key_file_locations` section lists it
- Build the set of matched domains

**If file classification is inconclusive or ambiguous** (no clear file matches, or request is too high-level):
- Load all available domains — proceed with all of them
- Over-inclusion is always safe

**Determine dependency order:**
- Server-layer domains (actions, services, storage) before client-layer domains (UI, components)
- Client-layer domains before integration-layer domains (external APIs, webhooks, notifications)
- ADW domain is independent — include only if the request explicitly touches orchestration

### Step 3 — Chain Domain Plans

For each domain in dependency order, spawn a sequential Task:

```
Task(
  subagent_type: "general-purpose",
  prompt: "Run SlashCommand('/mental-model:DOMAIN:plan [USER_REQUEST] [prior_spec_path]').
           prior_spec_path is the plan file output from the previous domain (empty for the first domain).
           Return the path to the generated plan file."
)
```

Use TaskOutput after each to get `path_to_plan` before spawning the next domain's Task.
The final domain's plan file is `last_spec_path`.

### Step 4 — Implement

```
Task(
  subagent_type: "general-purpose",
  prompt: "Run SlashCommand('/implement [last_spec_path]'). Implement the entire plan. Return a summary of files changed."
)
```

Use TaskOutput to get `build_report`.

### Step 5 — Self-Improve All Touched Domains

Spawn parallel Tasks, one per touched domain:

```
Task(
  subagent_type: "general-purpose",
  prompt: "Run SlashCommand('/mental-model:DOMAIN:self-improve true'). Return the self-improvement report."
)
```

Use TaskOutput on all before proceeding.

### Step 6 — Report

## Report

### Domain Detection
- Domains detected: [list]
- Detection method: file-based / load-all fallback
- Dependency order: [chain]

### Planning
- Plan files generated: [list with paths]

### Build
- [build_report summary]

### Self-Improve
- [per-domain self-improve summary]

### Final Status
Build-with-mental-models workflow complete.
