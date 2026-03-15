---
allowed-tools: Agent, Bash, Read, Glob, Grep
description: Build-review-fix-commit loop for a single batch
argument-hint: x "[batch-number] [spec description]" [stage path (optional)]
model: sonnet
---

# Purpose

Orchestrates a single batch through a build → review → fix loop → commit cycle.
Dispatches sub-agents in sequence, routes on PASS/FAIL verdicts, and enforces a
max-fix-iteration cap before surfacing failures to the user. See `Instructions`
for behavioral rules and `Workflow` for the step-by-step sequence.

## Variables

BATCH_SPEC: $1
STAGE_PATH: $2 || apps/experience-qa/server/
MAX_FIX_ITERATIONS: 2

## Argument Parsing

`BATCH_SPEC` uses the format `"<batch-number> <spec description>"` — the batch number is the
first word/token, everything after it is the spec description. Parse them at the start of step 1:

- `BATCH_NUMBER` = first whitespace-delimited token of `BATCH_SPEC` (e.g. `9`, `8.1`, `10`)
- `SPEC_DESCRIPTION` = remainder of `BATCH_SPEC` after the first token

## Instructions

- Dispatch sub-agents **sequentially** — build must finish before Playwright, Playwright before review, review before fix
- Pass `SPEC_DESCRIPTION` verbatim to `build-agent`; do not paraphrase or summarize
- After each `batch-review`, capture the **full report verbatim** — do not summarize it
- On PASS verdict: proceed immediately to commit — no further agent calls
- On FAIL verdict: pass the **full verbatim report** + `QA_REPORT` to `batch-fix`, then re-review
- Track remaining fix iterations; start at `MAX_FIX_ITERATIONS` and decrement each fix dispatch
- If iterations reach 0 and verdict is still FAIL: stop, surface the report, do NOT commit
- Never commit when the latest verdict is FAIL
- Use `git add STAGE_PATH` then `git commit` — never use `git add -A` or `git add .`
- Commit message format: `batch <N>: <short description derived from SPEC_DESCRIPTION>`

## Client Layer Detection

A batch is **client layer** when STAGE_PATH contains `client/`. Server layer when it contains `server/`.
Only client layer batches get the Playwright visual smoke test (step 4a).

## Workflow

1. Parse `BATCH_SPEC`: split on first whitespace to extract `BATCH_NUMBER` (first token) and `SPEC_DESCRIPTION` (remainder). If `BATCH_SPEC` is empty or has no space, ask the user to re-invoke with the format `x "<batch-number> <spec description>" [stage-path]` — the leading `x` is required because the skill parser always drops the first argument
2. Set `remaining_iterations = MAX_FIX_ITERATIONS`
3. Dispatch `build-agent` with the full `SPEC_DESCRIPTION` for batch `BATCH_NUMBER`; wait for completion
4. **Client layer only — browser smoke test:**
   a. Start the Vite dev server in the background:
      ```bash
      cd /Users/rivero/ai/experience-qa/apps/experience-qa/client && npm run dev -- --port 5174 &
      sleep 6
      node -e "const h=require('http');h.get('http://localhost:5174',r=>{console.log(r.statusCode);r.resume()}).on('error',e=>console.log('ERR',e.message))"
      ```
   b. If server is up (200): dispatch the `agent-browser` subagent with this prompt:
      ```
      Navigate to http://localhost:5174 and take a snapshot. Then navigate to http://localhost:5174/history and take a snapshot. Then navigate to http://localhost:5174/settings and take a snapshot. For each route report: (1) did the page render without a blank white screen, (2) were there any visible JS error messages on screen, (3) brief description of what UI elements are visible (sidebar, nav, content areas). Return a structured PASS/FAIL report per route.
      ```
   c. Wait for agent-browser to complete; capture its full report as `QA_REPORT`
   d. Kill the dev server: `kill $(lsof -ti:5174) 2>/dev/null || true`
   e. If server never came up OR any route is FAIL in `QA_REPORT`: set `QA_STATUS=FAIL`; otherwise set `QA_STATUS=PASS`
   f. If `QA_STATUS=FAIL`: stop, surface `QA_REPORT` to the user, and dispatch `batch-fix` with the browser failures before proceeding to batch-review
5. Dispatch `batch-review` agent for batch `BATCH_NUMBER`, passing `QA_REPORT` (if available) as additional context; wait for completion and capture the full report and verdict
6. If verdict is PASS → go to step 9
7. If verdict is FAIL and `remaining_iterations > 0`:
   - Dispatch `batch-fix` agent with: the full verbatim review report, the `QA_REPORT` (if available), the CRITICAL/HIGH recommended fixes, and `BATCH_NUMBER`
   - Decrement `remaining_iterations`
   - Wait for `batch-fix` to complete → go to step 4
8. If verdict is FAIL and `remaining_iterations == 0`:
   - Stop all agent dispatches
   - Surface the latest full batch-review report to the user
   - Report: "Batch `BATCH_NUMBER` could not be auto-fixed after 2 attempts. Manual intervention required."
   - Do not proceed to commit
9. Run: `git add STAGE_PATH`
10. Run: `git commit -m "batch <BATCH_NUMBER>: <short description>"`

## Report

**On success:**
> Batch `<N>` complete. PASS. Committed.
> Commit: `<hash>`

**On failure after max iterations:**
> Batch `<N>` could not be auto-fixed after 2 attempts. Manual intervention required.
>
> --- Latest batch-review report ---
> `<full verbatim report>`
