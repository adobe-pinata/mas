---
description: Extract ADW workflow command and configuration from issue/comment text
argument-hint: "<issue or comment text>"
---

# Classify ADW

Extract ADW workflow configuration from the provided text.

## Text to Analyze

$1

## Rules

Look for:
- An ADW workflow name (e.g., `adw_plan_build_iso`, `adw_sdlc_iso`, `adw_plan_build_review_iso`)
- An ADW ID (8-char hex string)
- A model set (`model_set base` or `model_set heavy`)

Defaults if not found:
- workflow: `adw_plan_build_iso`
- adw_id: null
- model_set: `base`

## Output Format

Output ONLY valid JSON, nothing else:

```json
{
  "adw_slash_command": "adw_plan_build_iso",
  "adw_id": null,
  "model_set": "base"
}
```
