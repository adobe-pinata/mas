---
name: frontend-plan-build-improve
allowed-tools: Task, TaskOutput, TodoWrite
description: End-to-end frontend implementation workflow. Chains expertise-informed planning → code build → expertise self-improvement. Use for complete feature development in client pages, components, api.js extensions, or routing changes.
argument-hint: [implementation_request] [human_in_the_loop (bool)]
---

# Purpose

Orchestrates a complete frontend implementation cycle by chaining three specialized commands: expertise-informed planning, building from the plan, and self-improving the expertise based on changes made.

## Variables

USER_PROMPT: $1
HUMAN_IN_THE_LOOP: $2    # default: true

## Instructions

- Execute steps 1–3 sequentially using the Task tool for each step
- Each subagent starts fresh — provide complete instructions in each Task prompt
- Use TaskOutput to retrieve results before proceeding to the next step
- DO NOT STOP between steps — complete the entire workflow

## Workflow

### Step 1: Create Plan

Spawn a subagent to run the planning command:

```
Task(
  subagent_type: "general-purpose",
  prompt: "Run SlashCommand('/experts:frontend:plan [USER_PROMPT]'). Return the path to the generated plan file."
)
```

Replace `[USER_PROMPT]` with the actual user request.

Use TaskOutput to get `path_to_plan` before proceeding.

### Step 2: Build

Spawn a subagent to run the build command:

```
Task(
  subagent_type: "general-purpose",
  prompt: "Run SlashCommand('/implement [path_to_plan]'). Implement the entire plan. Return a summary of files changed."
)
```

Replace `[path_to_plan]` with the path from Step 1.

Use TaskOutput to get `build_report` before proceeding.

### Step 3: Self-Improve

Spawn a subagent to run the self-improve command:

```
Task(
  subagent_type: "general-purpose",
  prompt: "Run SlashCommand('/experts:frontend:self-improve true'). Return the self-improvement report."
)
```

Use TaskOutput to get `self_improve_report`.

### Step 4: Report

Compile the final report from all three steps.

## Report

### Workflow Summary
- User request: [USER_PROMPT]
- Steps completed: 3/3

### Step 1: Planning
- Plan file: [path_to_plan]

### Step 2: Build
- [build_report summary]

### Step 3: Self-Improve
- [self_improve_report summary]

### Final Status
frontend implementation workflow complete.
