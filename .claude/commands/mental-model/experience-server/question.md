---
name: experience-server-question
allowed-tools: Read, Bash, TodoWrite, Grep, Glob
description: Answer questions about experience server architecture, patterns, key files, and implementation details — without making code changes. Use when asking how actions or services work, where things live, why a pattern exists, or what a data shape looks like.
argument-hint: [question]
---

# QA Server Mental Model — Question Mode

Answer the user's question by analyzing the qa-server implementation. This is a read-only mode: DO NOT write, edit, or create any files.

## Variables

USER_QUESTION: $1
EXPERTISE_PATH: .claude/commands/mental-model/experience-server/expertise.yaml

## Instructions

- IMPORTANT: Read-only. Zero file writes.
- If the question requires code changes, explain what would need to be done conceptually — do not implement
- Validate expertise claims against the real codebase before answering
- Include file paths and line numbers in your answer where relevant

## Workflow

1. Read EXPERTISE_PATH to understand experience-server architecture and patterns
2. Identify which parts of the expertise are relevant to USER_QUESTION
3. Read the relevant source files to validate and enrich the answer
4. Respond per the Report format

## Report

- **Direct answer** to USER_QUESTION
- **Supporting evidence** from EXPERTISE_PATH and the codebase (file:line references)
- **Conceptual explanation** of the relevant architecture or pattern
- **Diagrams** where they clarify relationships (ASCII or Mermaid)
