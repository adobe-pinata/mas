---
name: frontend-self-improve
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, TodoWrite
description: Validate and update the frontend expertise file against the actual codebase. Detects outdated file paths, missing functions, changed component props, new pages, and stale patterns. Run after any client page, component, or lib changes to keep expertise accurate.
argument-hint: [check_git_diff (true/false)] [focus_area (optional)]
---

# Purpose

Maintain the frontend expertise file's accuracy by comparing it against the actual codebase. The expertise file is the **mental model** for all frontend tasks — it must reflect reality, not aspirations.

## Variables

CHECK_GIT_DIFF: $1    # default: false
FOCUS_AREA: $2        # optional — specific area to prioritize (e.g. "components", "api", "pages")
EXPERTISE_FILE: .claude/commands/experts/frontend/expertise.yaml
MAX_LINES: 1000

## Instructions

- This is a self-improvement workflow to keep frontend expertise synchronized with the actual codebase
- Think of the expertise file as your **mental model** and memory reference for all client-related functionality
- Always validate expertise against real implementation, not assumptions
- Focus exclusively on frontend: pages, components, lib/api.js, lib/runObserver.js, main.jsx, App.jsx
- If FOCUS_AREA is provided, prioritize validation of that specific area
- Maintain YAML structure and enforce the 1000-line limit
- Write as a principal engineer — clearly and concisely for future engineers

## Workflow

1. **Check Git Diff (conditional)**
   - If CHECK_GIT_DIFF is "true": run `git diff apps/experience-qa/client/` to identify recent client changes
   - Note changed files for targeted validation in step 3

2. **Read Current Expertise**
   - Read EXPERTISE_FILE fully
   - Note sections that may be stale or incomplete

3. **Validate Against Codebase**
   - For each file listed in EXPERTISE_FILE under key_files and key_file_locations: verify it exists
   - Read those files and verify documented functions/props/patterns match actual code
   - Use Grep to verify:
     - All documented function names exist in their listed files
     - All documented prop names match component signatures
     - session storage key 'xqa_conversation_id' usage is consistent
     - TERMINAL_STATUSES set membership is accurate
     - api.js exports match documented function list
   - Check: data shapes, patterns, gotchas, integration points
   - If FOCUS_AREA is set, prioritize validation of that area

4. **Identify Discrepancies**
   - Missing files (new components/pages not documented)
   - Wrong file paths
   - Changed function signatures or prop shapes
   - Removed features still listed
   - Incorrect architectural descriptions
   - Outdated pattern examples

5. **Update Expertise File**
   - Fix all discrepancies
   - Add missing information
   - Remove obsolete information
   - Keep all file paths relative to project root (starting with apps/experience-qa/client/)
   - Maintain YAML structure and formatting

6. **Enforce Line Limit**
   - Run: `wc -l .claude/commands/experts/frontend/expertise.yaml`
   - If count > MAX_LINES: trim least-critical sections (verbose prose, redundant examples)
   - Repeat until count <= MAX_LINES

7. **Validate YAML**
   - Run: `python3 -c "import yaml; yaml.safe_load(open('.claude/commands/experts/frontend/expertise.yaml')); print('YAML valid')"`
   - Fix any syntax errors before reporting

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
