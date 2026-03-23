---
name: build-mental-models
allowed-tools: Task, TaskOutput, Bash, TodoWrite
description: Generate all three experience domain mental model sets (experience-server, experience-frontend, experience-integrations) from the codebase. Runs experience-server first (defines contracts), then experience-frontend and experience-integrations in parallel (both read experience-server output). Use when setting up the mental model system for the first time or rebuilding all mental models.
---

# Build QA Domain Mental Models

Generates all three QA domain mental model sets by exploiting the dependency graph:
- `experience-server` first — it defines the API contracts and service patterns
- `experience-frontend` + `experience-integrations` in parallel — both read experience-server's output, independent of each other

**Plan reference:** `specs/qa-domain-experts-build.md`
**Pattern reference:** `.claude/commands/mental-model/adw/` (canonical ADW mental model)
**Templates:** `.claude/skills/meta-mental-model/templates/`

---

## Instructions

- Execute steps sequentially where dependencies exist, in parallel where they do not
- Each Task agent starts fresh — provide complete, self-contained instructions in every prompt
- Use TaskOutput to retrieve results before proceeding to dependent steps
- Do NOT stop between steps — complete the full workflow
- If a Task fails, surface the error and stop — do not proceed with downstream dependents

---

## Workflow

### Step 1 — Generate experience-server mental model (sequential, must complete first)

Spawn a Task agent with full context:

```
Task(
  subagent_type: "general-purpose",
  prompt: "
    You are generating the experience-server domain mental model for the Adobe Experience QA Platform.

    REFERENCE PATTERN — read all 5 files first:
    - .claude/commands/mental-model/adw/expertise.yaml
    - .claude/commands/mental-model/adw/plan.md
    - .claude/commands/mental-model/adw/question.md
    - .claude/commands/mental-model/adw/self-improve.md
    - .claude/commands/mental-model/adw/plan_build_improve.md

    TEMPLATES — read both:
    - .claude/skills/meta-mental-model/templates/expertise-template.yaml
    - .claude/skills/meta-mental-model/templates/commands-template.md

    SOURCE FILES — read all of these to extract real facts:
    - apps/experience-qa/server/actions/chat/index.js
    - apps/experience-qa/server/actions/runs/index.js
    - apps/experience-qa/server/actions/plans/index.js
    - apps/experience-qa/server/actions/schedules/index.js
    - apps/experience-qa/server/actions/settings/index.js
    - apps/experience-qa/server/actions/webhooks/index.js
    - apps/experience-qa/server/services/storage.js
    - apps/experience-qa/server/services/browser.js
    - apps/experience-qa/server/services/planner.js
    - apps/experience-qa/server/services/runner.js
    - apps/experience-qa/server/services/scheduler.js
    - apps/experience-qa/server/services/chat.js
    - apps/experience-qa/server/services/price-checker.js
    - apps/experience-qa/server/services/cta-validator.js
    - apps/experience-qa/server/services/language-detector.js
    - apps/experience-qa/server/services/vision.js
    - apps/experience-qa/server/services/geo-orchestrator.js
    - apps/experience-qa/server/services/k8s-runner.js
    - app.config.yaml

    GENERATE these 5 files:

    1. .claude/commands/mental-model/experience-server/expertise.yaml
       Sections required: overview, key_files (actions + services), patterns (action_handler,
       three_layer_storage, step_dispatch, geo_orchestration), data_shapes (TestPlan, TestRun,
       StepResult, RunCallback), integration_points, gotchas, best_practices, key_file_locations.
       RULES: every file path must exist, every function name must be verified via Grep.
       Max 1000 lines.

    2. .claude/commands/mental-model/experience-server/plan.md
       Frontmatter: name=experience-server-plan, allowed-tools=Read,SlashCommand,TodoWrite,Grep,Glob,Bash
       Variables: USER_REQUEST=$1, PRIOR_SPEC=$2, EXPERTISE_FILE=.claude/commands/mental-model/experience-server/expertise.yaml
       If PRIOR_SPEC is set, read it first as upstream contract context before planning.
       Then delegates to /plan with USER_REQUEST.

    3. .claude/commands/mental-model/experience-server/question.md
       Read-only Q&A. Validates expertise against codebase before answering.

    4. .claude/commands/mental-model/experience-server/self-improve.md
       Validates expertise.yaml vs real codebase. Enforces <=1000 line limit. Validates YAML syntax.

    5. .claude/commands/mental-model/experience-server/plan_build_improve.md
       Chains: /mental-model:experience-server:plan -> /implement -> /mental-model:experience-server:self-improve
       Uses Task + TaskOutput for sequential subagent execution.

    VALIDATE after writing:
    - python3 -c \"import yaml; yaml.safe_load(open('.claude/commands/mental-model/experience-server/expertise.yaml')); print('YAML valid')\"
    - wc -l .claude/commands/mental-model/experience-server/expertise.yaml

    Return: 'experience-server mental model complete. Files: [list]. Line count: N. YAML: valid/invalid.'
  "
)
```

Use TaskOutput to get `experience_server_result`. Confirm YAML valid before proceeding.

---

### Step 2 — Generate experience-frontend + experience-integrations in parallel

Both experts read experience-server's expertise.yaml as upstream context. They are independent of each other — spawn both simultaneously.

**Task A — experience-frontend mental model:**

```
Task(
  subagent_type: "general-purpose",
  prompt: "
    You are generating the experience-frontend domain mental model for the Adobe Experience QA Platform.

    UPSTREAM CONTEXT — read this first (server API contracts the client consumes):
    - .claude/commands/mental-model/experience-server/expertise.yaml

    REFERENCE PATTERN — read all 5 files:
    - .claude/commands/mental-model/adw/expertise.yaml
    - .claude/commands/mental-model/adw/plan.md
    - .claude/commands/mental-model/adw/question.md
    - .claude/commands/mental-model/adw/self-improve.md
    - .claude/commands/mental-model/adw/plan_build_improve.md

    TEMPLATES:
    - .claude/skills/meta-mental-model/templates/expertise-template.yaml
    - .claude/skills/meta-mental-model/templates/commands-template.md

    SOURCE FILES — read all:
    - apps/experience-qa/client/src/App.jsx
    - apps/experience-qa/client/src/main.jsx
    - apps/experience-qa/client/src/lib/api.js
    - apps/experience-qa/client/src/lib/runObserver.js
    - apps/experience-qa/client/src/pages/ChatPage.jsx
    - apps/experience-qa/client/src/pages/HistoryPage.jsx
    - apps/experience-qa/client/src/pages/SettingsPage.jsx
    - apps/experience-qa/client/src/pages/RunDetailPage.jsx
    - apps/experience-qa/client/src/components/Sidebar.jsx
    - apps/experience-qa/client/src/components/Toast.jsx
    - apps/experience-qa/client/src/components/ErrorBoundary.jsx
    - apps/experience-qa/client/src/components/Chat/MessageList.jsx
    - apps/experience-qa/client/src/components/Chat/MessageInput.jsx
    - apps/experience-qa/client/src/components/Chat/PlanCard.jsx
    - apps/experience-qa/client/src/components/Run/RunProgress.jsx
    - apps/experience-qa/client/src/components/Run/RunSummary.jsx
    - apps/experience-qa/client/src/components/Run/StepResult.jsx
    - apps/experience-qa/client/src/components/Run/BatchProgress.jsx

    GENERATE these 5 files:

    1. .claude/commands/mental-model/experience-frontend/expertise.yaml
       Sections required: overview, key_files (entry, api, pages, components by group),
       patterns (api_call, run_polling, spectrum_adoption, routing),
       data_shapes (sourced from experience-server expertise.yaml contracts),
       integration_points.server (api.js function -> server endpoint mapping),
       gotchas (no Redux, inline CSS, Spectrum partial adoption),
       best_practices, key_file_locations.
       RULES: every file path must exist, every function verified via Grep. Max 1000 lines.

    2. .claude/commands/mental-model/experience-frontend/plan.md
       Variables: USER_REQUEST=$1, PRIOR_SPEC=$2, EXPERTISE_FILE=.claude/commands/mental-model/experience-frontend/expertise.yaml
       If PRIOR_SPEC is set, read it first as upstream contract before planning.
       Delegates to /plan with USER_REQUEST.

    3. .claude/commands/mental-model/experience-frontend/question.md
    4. .claude/commands/mental-model/experience-frontend/self-improve.md
    5. .claude/commands/mental-model/experience-frontend/plan_build_improve.md

    VALIDATE after writing:
    - python3 -c \"import yaml; yaml.safe_load(open('.claude/commands/mental-model/experience-frontend/expertise.yaml')); print('YAML valid')\"
    - wc -l .claude/commands/mental-model/experience-frontend/expertise.yaml

    Return: 'experience-frontend mental model complete. Files: [list]. Line count: N. YAML: valid/invalid.'
  "
)
```

**Task B — experience-integrations mental model:**

```
Task(
  subagent_type: "general-purpose",
  prompt: "
    You are generating the experience-integrations domain mental model for the Adobe Experience QA Platform.

    UPSTREAM CONTEXT — read this first (which server services call each integration):
    - .claude/commands/mental-model/experience-server/expertise.yaml

    REFERENCE PATTERN — read all 5 files:
    - .claude/commands/mental-model/adw/expertise.yaml
    - .claude/commands/mental-model/adw/plan.md
    - .claude/commands/mental-model/adw/question.md
    - .claude/commands/mental-model/adw/self-improve.md
    - .claude/commands/mental-model/adw/plan_build_improve.md

    TEMPLATES:
    - .claude/skills/meta-mental-model/templates/expertise-template.yaml
    - .claude/skills/meta-mental-model/templates/commands-template.md

    SOURCE FILES — read all:
    - apps/experience-qa/server/services/wcs.js
    - apps/experience-qa/server/services/aos.js
    - apps/experience-qa/server/services/osi-mapping.js
    - apps/experience-qa/server/services/adobe-io.js
    - apps/experience-qa/server/services/jira.js
    - apps/experience-qa/server/services/slack.js
    - apps/experience-qa/server/actions/webhooks/index.js
    - app.config.yaml

    Also read specs/experience-qa-platform-build.md Steps 14-17 for integration intent.

    GENERATE these 5 files:

    1. .claude/commands/mental-model/experience-integrations/expertise.yaml
       Sections required: overview (all called only by server, never by client),
       key_files (adobe_commerce: wcs/aos/osi, adobe_platform: adobe-io/webhooks,
       notifications: jira/slack),
       patterns (price_validation_flow, geo_url_resolution, webhook_trigger,
       jira_on_failure, slack_alert),
       data_shapes (each service input/output contract),
       integration_points.caller (which server service invokes each integration),
       env_vars (required env var per integration),
       gotchas (AIO Runtime params not process.env, OSI is static data not API,
       webhook HMAC verification),
       best_practices, key_file_locations.
       RULES: every file path must exist, every function verified via Grep. Max 1000 lines.

    2. .claude/commands/mental-model/experience-integrations/plan.md
       Variables: USER_REQUEST=$1, PRIOR_SPEC=$2, EXPERTISE_FILE=.claude/commands/mental-model/experience-integrations/expertise.yaml
       If PRIOR_SPEC is set, read it first as upstream contract before planning.
       Delegates to /plan with USER_REQUEST.

    3. .claude/commands/mental-model/experience-integrations/question.md
    4. .claude/commands/mental-model/experience-integrations/self-improve.md
    5. .claude/commands/mental-model/experience-integrations/plan_build_improve.md

    VALIDATE after writing:
    - python3 -c \"import yaml; yaml.safe_load(open('.claude/commands/mental-model/experience-integrations/expertise.yaml')); print('YAML valid')\"
    - wc -l .claude/commands/mental-model/experience-integrations/expertise.yaml

    Return: 'experience-integrations mental model complete. Files: [list]. Line count: N. YAML: valid/invalid.'
  "
)
```

Spawn both Tasks simultaneously. Use TaskOutput on both before proceeding to Step 3.

---

### Step 3 — Validate all three

Run these commands directly (not via Task agent):

```bash
# Confirm all 15 files exist
find .claude/commands/mental-model/experience-server \
     .claude/commands/mental-model/experience-frontend \
     .claude/commands/mental-model/experience-integrations \
     -type f | sort

# Validate YAML syntax for all three
python3 -c "
import yaml
for d in ['experience-server', 'experience-frontend', 'experience-integrations']:
    yaml.safe_load(open(f'.claude/commands/mental-model/{d}/expertise.yaml'))
    print(f'{d}: OK')
"

# Line counts (all must be ≤ 1000)
wc -l .claude/commands/mental-model/experience-server/expertise.yaml \
       .claude/commands/mental-model/experience-frontend/expertise.yaml \
       .claude/commands/mental-model/experience-integrations/expertise.yaml
```

If any validation fails: fix the offending file inline (do not re-spawn the full Task).

---

### Step 4 — Commit

```bash
git add .claude/commands/mental-model/experience-server \
        .claude/commands/mental-model/experience-frontend \
        .claude/commands/mental-model/experience-integrations
git commit -m "feat: add experience-server, experience-frontend, experience-integrations domain mental models"
```

---

## Report

```
Experience Domain Mental Models Build Complete

Mental models created:
- /mental-model:experience-server:{plan,question,self-improve,plan_build_improve}
- /mental-model:experience-frontend:{plan,question,self-improve,plan_build_improve}
- /mental-model:experience-integrations:{plan,question,self-improve,plan_build_improve}

Line counts:
- experience-server/expertise.yaml:  N lines
- experience-frontend/expertise.yaml:  N lines
- experience-integrations/expertise.yaml: N lines

YAML validation: all valid

Next steps:
1. Smoke-test: /mental-model:experience-server:question "how does runner.js dispatch step types?"
2. Try the pipe: /mental-model:experience-server:plan "your feature" -> /mental-model:experience-frontend:plan "your feature" specs/experience-server-plan.md
3. After any codebase changes: run /mental-model:experience-{domain}:self-improve true
```
