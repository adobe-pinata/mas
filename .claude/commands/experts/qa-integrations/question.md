---
name: qa-integrations-question
allowed-tools: Read, Bash, TodoWrite, Grep, Glob
description: Answer questions about QA integration architecture — WCS/AOS price pipeline, OSI mapping, Adobe I/O webhook flow, Jira ticket creation, Slack notifications, env var requirements, and caller contracts — without making code changes. Use when asking how an integration works, where things live, or why a pattern exists.
argument-hint: [question]
---

# QA Integrations Expert — Question Mode

Answer the user's question by analyzing the QA integrations implementation. This is a read-only mode: DO NOT write, edit, or create any files.

## Variables

USER_QUESTION: $1
EXPERTISE_PATH: .claude/commands/experts/qa-integrations/expertise.yaml

## Instructions

- IMPORTANT: Read-only. Zero file writes.
- Focus on: WCS/AOS/OSI price pipeline, Adobe I/O + webhook action, Jira/Slack notification services
- If the question requires code changes, explain what would need to be done conceptually — do not implement
- Validate expertise claims against the real codebase before answering
- Include file paths and line references in your answer where relevant

## Workflow

1. Read EXPERTISE_PATH to understand QA integrations architecture, data shapes, env vars, and gotchas
2. Identify which integrations are relevant to USER_QUESTION
3. Read the relevant source files to validate and enrich the answer:
   - apps/experience-qa/server/services/wcs.js
   - apps/experience-qa/server/services/aos.js
   - apps/experience-qa/server/services/osi-mapping.js
   - apps/experience-qa/server/services/adobe-io.js
   - apps/experience-qa/server/services/jira.js
   - apps/experience-qa/server/services/slack.js
   - apps/experience-qa/server/actions/webhooks/index.js
4. Respond per the Report format

## Report

- **Direct answer** to USER_QUESTION
- **Supporting evidence** from EXPERTISE_PATH and the codebase (file references)
- **Conceptual explanation** of the relevant integration flow or pattern
- **Diagrams** where they clarify relationships (ASCII or Mermaid)
