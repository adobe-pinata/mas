---
name: adw-question
allowed-tools: Bash, Read, TodoWrite
description: Answer questions about Developer Workflows (ADW) architecture, workflow triggers, swimlane UI, WebSocket events, orchestrator integration, and step composition. Use when asking about workflow types, start_adw tool, ADW database schema, or multi-agent orchestration patterns without making code changes.
argument-hint: [question]
---

# ADW Mental Model - Question Mode

Answer the user's question by analyzing Developer Workflow implementation, architecture, and patterns in this multi-agent orchestration system. This prompt is designed to provide information about ADWs without making any code changes.

## Variables

USER_QUESTION: $1
EXPERTISE_PATH: .claude/commands/mental-model/adw/expertise.yaml

## Instructions

- IMPORTANT: This is a question-answering task only - DO NOT write, edit, or create any files
- Focus on ADW workflows, triggers, swimlane UI, WebSocket events, and orchestrator integration
- If the question requires code changes, explain what would need to be done conceptually without implementing
- With your expert knowledge, validate the information from `EXPERTISE_PATH` against the codebase before answering your question.

## Workflow

- Read the `EXPERTISE_PATH` file to understand ADW architecture and patterns
- Review, validate, and confirm information from `EXPERTISE_PATH` against the codebase
- Respond based on the `Report` section below.

## Report

- Direct answer to the `USER_QUESTION`
- Supporting evidence from `EXPERTISE_PATH` and the codebase
- References to the exact files and lines of code that support the answer
- High-mid level conceptual explanations of the ADW architecture and patterns
- Include diagrams where appropriate to streamline communication
