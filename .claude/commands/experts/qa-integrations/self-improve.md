---
name: qa-integrations-self-improve
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, TodoWrite
description: Validate and update the QA integrations expertise file against the actual codebase. Detects outdated env var names, missing functions, changed data shapes, new integration files, and stale caller contracts. Run after any change to wcs.js, aos.js, osi-mapping.js, adobe-io.js, jira.js, slack.js, or the webhooks action.
argument-hint: [check_git_diff (true/false)] [focus_area (optional)]
---

# Purpose

Maintain the QA integrations expertise file's accuracy by comparing it against the actual codebase. The expertise file is the **mental model** for all integration tasks — it must reflect reality: correct env var names, accurate function signatures, current data shapes, and verified caller contracts.

## Variables

CHECK_GIT_DIFF: $1    # default: false
FOCUS_AREA: $2        # optional — e.g. 'jira', 'webhooks', 'wcs'
EXPERTISE_FILE: .claude/commands/experts/qa-integrations/expertise.yaml
MAX_LINES: 1000

## Workflow

1. **Check Git Diff (conditional)**
   - If CHECK_GIT_DIFF is "true": run `git diff` to identify recent integration-related changes
   - Note changed files for targeted validation in step 3

2. **Read Current Expertise**
   - Read EXPERTISE_FILE fully
   - Note any sections that seem potentially stale or incomplete

3. **Validate Against Codebase**
   - For each file listed in EXPERTISE_FILE: verify it exists and read current content
   - Use Grep to verify all documented function names actually exist in the listed files:
     - wcs.getExpectedPrice, aos.getCanonicalPrice
     - osi-mapping.lookupOSI, osi-mapping.upsertMappings
     - adobe-io.verifySignature, adobe-io.mapAEMPathToURL
     - jira.createIssue
     - slack.postRunStarted, slack.postRunSummary
     - webhooks: main, extractSubPath, parseBody, verifyJiraSignature, verifySlackSignature, verifyAdobeSignature, handleJiraWebhook, handleSlackWebhook, handleAEMWebhook
   - Verify env var names against actual process.env reads in each file
   - Verify data shapes (return values, function params) against actual implementation
   - Check integration_points.caller section is accurate — confirm which server services call each integration
   - Verify app.config.yaml for webhooks web:'raw' and require-adobe-auth:false
   - If FOCUS_AREA is set, prioritize validation of that specific integration

4. **Identify Discrepancies**
   - Missing functions or new exports not documented
   - Wrong env var names
   - Changed function signatures or return shapes
   - Removed functions still listed
   - Incorrect caller relationships
   - Stale gotchas or best practices

5. **Update Expertise File**
   - Fix all discrepancies
   - Add missing information
   - Remove obsolete information
   - Keep all file paths relative to project root
   - Maintain YAML structure and formatting

6. **Enforce Line Limit**
   - Run: `wc -l .claude/commands/experts/qa-integrations/expertise.yaml`
   - If count > MAX_LINES: trim least-critical sections (verbose prose, redundant examples)
   - Repeat until <= MAX_LINES

7. **Validate YAML**
   - Run: `python3 -c "import yaml; yaml.safe_load(open('.claude/commands/experts/qa-integrations/expertise.yaml')); print('YAML valid')"`
   - Fix any syntax errors and re-validate

## Report

### Summary
- Git diff checked: yes/no
- Focus area: [value or none]
- Discrepancies found: N / remedied: N
- Final line count: N/1000

### Discrepancies Found
[List each: what was wrong → where correct info was found → how fixed]

### Updates Made
[Added / Updated / Removed sections]

### Line Limit
- Initial: N / Final: N / Trimming needed: yes/no

### Validation
- All key files verified: yes/no
- YAML syntax valid: yes/no
- Areas needing future attention: [list or none]
