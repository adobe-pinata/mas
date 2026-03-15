---
description: Classify a GitHub issue as /feature, /bug, or /chore for ADW workflow routing
argument-hint: "<issue title and body>"
---

# Classify Issue

Analyze the issue text and classify it as one of three types. Output ONLY the classification, nothing else.

## Issue Content

$1

## Classification Rules

- `/feature` — New functionality, enhancement, new page, new component, new API endpoint, new integration
- `/bug` — Something broken, error, regression, unexpected behavior, fix for existing code
- `/chore` — Documentation, refactoring, dependency update, config change, testing, spec update, cleanup

## Output Format

Output ONLY one of these three strings on a single line:
```
/feature
```
or
```
/bug
```
or
```
/chore
```

No explanation. No markdown. Just the slash command.
