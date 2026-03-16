---
name: ux-walkthrough
description: Walk through any app in apps/ as a real user — navigate the UI with browser automation, explore every page and interaction, and produce a structured UX findings report. Use this skill whenever someone wants to audit an app's UX, catch missing features, validate a user flow end-to-end, or see what a real user would experience. Triggers on: "walk through the app", "act as a user", "ux audit", "test the flow", "what's missing in the UI", "check the user experience".
argument-hint: [app-name] [app-url]
model: sonnet
disable-model-invocation: false
allowed-tools: Read, Glob, Grep, Write, Edit, Agent, Bash
hooks:
  Stop:
    - matcher: ""
      hooks:
        - type: command
          command: "osascript -e 'display notification \"UX walkthrough complete. Check .reports/ux/ for the report.\" with title \"ux-walkthrough\"'"
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "echo \"$CLAUDE_TOOL_INPUT\" | python3 -c \"import sys,json,os,subprocess; d=json.load(sys.stdin); p=d.get('file_path',''); subprocess.run(['open',p]) if 'ux-walkthrough-report' in p and os.path.exists(p) else None\""
---

# UX Walkthrough

Act as a first-time user of an app in `apps/`. Discover everything through the UI — do not read source code to understand expected behavior. Delegate all browser interactions to the `agent-browser` subagent, then synthesize its raw output into a structured findings report.

## Variables

APP: $0
APP_URL: $1

## Step 1 — Resolve inputs

**APP**: If empty, list `apps/` and use the first directory found.

**APP_URL**: If empty, check `apps/APP/client/vite.config.ts` (or `.js`) for the configured dev port. Verify it is alive with `lsof -ti :<port>`. Fall back to ports 5173, 5174, 3000 in order.

**Report directory**: Set `REPORT_DIR=$CLAUDE_PROJECT_DIR/apps/APP/.reports/ux/agent-browser/$(date +%Y-%m-%d)_APP` — all screenshots and the final report live inside the app directory, not the agentic layer root.

## Step 2 — Prepare report

Read `${CLAUDE_SKILL_DIR}/report-template.md`. Copy it to `$REPORT_DIR/ux-walkthrough-report.md`. Fill in header fields (App, Date, App URL, Report Dir) before starting.

## Step 3 — Dispatch agent-browser subagent

Spawn `Agent(subagent_type: "agent-browser")` with a detailed prompt that includes:

- `APP_URL` and `REPORT_DIR` (absolute path)
- Session name: `ux-APP` (e.g. `ux-content-qa`)
- Screenshot naming: `01-landing.png`, `02-<action>.png` (zero-padded, semantic slugs)
- Instructions to use `--annotate` on key screenshots to label interactive elements
- Instructions to run `agent-browser console` and `agent-browser errors` after each major interaction
- Instructions to test `set device "iPhone 14"` after the desktop flow
- The full walkthrough tasks below

**What to tell the subagent to do:**

### Discovery pass (desktop)
1. Open `APP_URL` → annotated screenshot → note: is the purpose clear? what's the first CTA?
2. Explore every visible nav item / sidebar entry → screenshot each route
3. Perform the app's primary action (submit a form, start a task, send a message — whatever the UI presents first)
4. Wait for and observe the response/result → screenshot
5. Explore secondary flows visible from the result (detail views, history, settings, etc.)
6. Check console errors and page errors after each route

### Edge cases
7. Submit empty/invalid input — observe validation feedback
8. Resize to mobile (375px wide) → screenshot
9. Switch device to `"iPhone 14"` → screenshot
10. Try keyboard navigation (Tab through form, Enter to submit)
11. Open any Settings or preferences panel

### Return from subagent
The subagent should return: list of findings per step (what confused/delighted/blocked), console errors found, screenshot paths, and pass/fail per route.

## Step 4 — Synthesize report

Using the subagent's findings, fill in every section of `$REPORT_DIR/ux-walkthrough-report.md`:
- Screenshots table (with file paths and captions)
- Findings table — categorize each by severity:
  - **CRITICAL** — blocks completing the flow entirely
  - **HIGH** — significant pain; a real user would likely give up
  - **MEDIUM** — noticeable friction; workaround exists
  - **LOW** — polish opportunity
- Flow gaps — flows a user would expect that don't exist
- Recommendations — top 5 by user impact

## Step 5 — Finish

- Save final report to `$REPORT_DIR/ux-walkthrough-report.md`
- Print a 3-bullet summary to the conversation (top findings only)
- The Stop hook sends a desktop notification; the Write hook opens the report automatically
