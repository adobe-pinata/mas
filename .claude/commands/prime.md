---
description: Prime context for Adobe Experience QA Platform (Agentic Catch). Load this at the start of any session.
---

# Prime — Adobe Experience QA Platform

**Context Engineering:** Load the minimum needed. Expand only for your specific task.

## Step 1: Core context (always load)

- @CLAUDE.md
- @specs/PROGRESS.md
- @specs/DECISIONS.md

## Step 2: Load based on your task

**Starting a new session / orientation:**
- @docs/prd-experience-qa.md
- @NAMING.md

**Planning or building anything** — use the domain experts (UNIX pipe pattern):

| Task touches | Use expert(s) | Pipe pattern |
|---|---|---|
| Server only (actions, services, storage, browser, runner) | `qa-server` | `/experts:qa-server:plan "request"` |
| Client only (React, Spectrum, UI components) | `qa-client` | `/experts:qa-client:plan "request"` |
| Integrations only (AEM, Jira, Slack, WCS, AOS) | `qa-integrations` | `/experts:qa-integrations:plan "request"` |
| Server + Client (API + UI — most features) | `qa-server` → `qa-client` | server plan first, pass it as `$2` to client plan |
| Server + Integrations (new connector, webhook) | `qa-server` → `qa-integrations` | server plan first, pass it as `$2` to integrations plan |
| All three (new geo, new run type, full feature) | all three in order | server → client → integrations, each reading prior spec |

**Expert pipe pattern:**
```
/experts:qa-server:plan "add Peru geo"                                     → specs/qa-server-plan.md
/experts:qa-client:plan "add Peru geo" specs/qa-server-plan.md             → specs/qa-client-plan.md
/experts:qa-integrations:plan "add Peru geo" specs/qa-server-plan.md       → specs/qa-integrations-plan.md
/implement specs/qa-integrations-plan.md
```

**Answering a question without building:**
- Server architecture/patterns: `/experts:qa-server:question "your question"`
- Client architecture/patterns: `/experts:qa-client:question "your question"`
- Integration patterns: `/experts:qa-integrations:question "your question"`

**Auditing or reviewing the spec:**
- @specs/experience-qa-platform-build.md (full spec with current status annotations)
- @specs/PROGRESS.md (living status — open items, recommended next steps)

## Step 3: Report

Summarize:
1. **Project state** — all 25 spec steps code-complete; running locally; production deployment (Ethos/K8s) not started
2. **Architecture** — Express server for local dev; AIO Runtime actions mirror routes for production parity
3. **Key constraint** — `RUNNER_MODE=sequential` for local dev (no K8s needed); `RUNNER_MODE=k8s` for Ethos
4. **Storage** — local dev uses in-memory adapter; AIO prod adapter (aio-lib-state + aio-lib-files + aio-lib-db) untested
5. **Key decisions** — no TypeScript, no Redux, no SCSS (see DECISIONS.md); oauth auto-refreshes from macOS Keychain
6. **Open items** — schedule UI, AEM CF API, live E2E validation, Jira/Slack credentials — see PROGRESS.md
7. **Specific context** relevant to the current task
