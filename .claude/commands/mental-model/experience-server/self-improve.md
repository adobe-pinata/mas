---
name: experience-server-self-improve
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, TodoWrite
description: Validate and update the experience-server expertise file against the actual codebase. Detects outdated file paths, missing functions, changed patterns, and new files. Run after any server action or service changes to keep expertise accurate.
argument-hint: [check_git_diff (true/false)] [focus_area (optional)]
---

# Purpose

Maintain the experience-server expertise file's accuracy by comparing it against the actual codebase. The expertise file is the **mental model** for all qa-server tasks — it must reflect reality, not aspirations.

## Variables

CHECK_GIT_DIFF: $1    # default: false
FOCUS_AREA: $2        # optional — specific area to prioritize
EXPERTISE_FILE: .claude/commands/mental-model/experience-server/expertise.yaml
MAX_LINES: 1000

## Workflow

1. **Check Git Diff (conditional)**
   - If CHECK_GIT_DIFF is "true": run `git diff` to identify recent changes to server-related files
   - Note changed files under apps/experience-qa/server/ for targeted validation in step 3

2. **Read Current Expertise**
   - Read EXPERTISE_FILE fully
   - Note any sections that seem potentially stale or incomplete

3. **Validate Against Codebase**
   - For each file listed in EXPERTISE_FILE: verify it exists and read its current content
   - Use Grep to verify all documented function names actually exist in the files listed:
     - Action handlers: main, extractId, extractSubResource, handleAEMWebhook, verifyJiraSignature, verifySlackSignature, verifyAdobeSignature
     - Storage: init, seedGeos, getDoc, findDocs, upsertDoc, deleteDoc, getState, setState, deleteState, uploadFile, downloadFile, generatePresignURL
     - Browser: createContext, navigateTo, waitForCommerceReady, extractDOM, screenshot, clickElement, close
     - Runner: executeRun, _executeStep, _fireJiraTickets
     - Planner: parse
     - Scheduler: init, addSchedule, removeSchedule, updateSchedule
     - Chat: process
     - Price checker: extractPrices, validateDiscount, compareToExpected
     - CTA validator: validateCTA
     - Language detector: detect
     - Vision: validate
     - Geo orchestrator: runMultiGeo, getGeoStatus, cancelMultiGeo
     - K8s runner: createRunJob, dispatchJob, watchJob, cancelJob, isK8sAvailable
   - Check: data shapes, patterns, integration points, gotchas
   - If FOCUS_AREA is set, prioritize validation of that area

4. **Identify Discrepancies**
   - Missing files/functions in expertise (new code not documented)
   - Wrong paths or stale information
   - Changed function signatures
   - Removed features still listed
   - Incorrect architectural descriptions
   - New environment variables not documented
   - New KV key patterns not documented

5. **Update Expertise File**
   - Fix all discrepancies
   - Add missing information
   - Remove obsolete information
   - Keep all file paths relative to project root
   - Maintain YAML structure

6. **Enforce Line Limit**
   - Run: `wc -l .claude/commands/mental-model/experience-server/expertise.yaml`
   - If count > MAX_LINES: trim least-critical sections (verbose prose, redundant examples)
   - Repeat until ≤ MAX_LINES

7. **Validate YAML**
   - Run: `python3 -c "import yaml; yaml.safe_load(open('.claude/commands/mental-model/experience-server/expertise.yaml')); print('YAML valid')"`
   - Fix any syntax errors

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
