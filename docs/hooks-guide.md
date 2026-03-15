# Hooks Guide

## Overview

Claude Code hooks are shell commands that run automatically at specific points in the agent lifecycle. Each hook receives a JSON payload on stdin describing the current event and can influence agent behavior through its exit code and stdout output.

### Event Lifecycle

The hooks in this project fire in the following order during a typical session:

```
SessionStart          - once, when the session is created or resumed
  └─ UserPromptSubmit - each time the user sends a prompt
       └─ PreToolUse  - before every tool call
       └─ PostToolUse - after every tool call (and again for Write/Edit/MultiEdit)
       └─ Notification - when Claude is waiting for user input
  └─ PreCompact       - before the context window is compacted
Stop                  - when the top-level agent finishes
SubagentStop          - when a sub-agent finishes
```

### Exit Code Contract

| Exit code | Meaning |
|-----------|---------|
| `0`       | Success; the agent continues normally |
| `2`       | Block the action; the error message written to stderr is shown to Claude |
| Any other | Non-zero exits are treated as errors but do not block the action |

All hooks in this codebase exit `0` except `pre_tool_use.py`, which exits `2` to block dangerous commands.

---

## Hook Configuration

Hooks are registered in `.claude/settings.json` under the `"hooks"` key. The project also sets two environment variables that every hook command can read:

```json
{
  "env": {
    "CLAUDE_PROJECT_DIR": "/Users/rivero/ai/experience-qa",
    "SOURCE_APP": "experience-qa"
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/session_start.py --load-context"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/pre_tool_use.py"
          },
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/send_event.py --source-app $SOURCE_APP --event-type PreToolUse --summarize"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/post_tool_use.py"
          },
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/send_event.py --source-app $SOURCE_APP --event-type PostToolUse --summarize"
          }
        ]
      },
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/prettier_on_write.py"
          },
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/eslint_on_write.py"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/notification.py"
          },
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/send_event.py --source-app $SOURCE_APP --event-type Notification --summarize"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/stop.py"
          },
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/send_event.py --source-app $SOURCE_APP --event-type Stop --add-chat --summarize"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/subagent_stop.py"
          },
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/send_event.py --source-app $SOURCE_APP --event-type SubagentStop --summarize"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/send_event.py --source-app $SOURCE_APP --event-type PreCompact --summarize"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/user_prompt_submit.py --log-only --store-last-prompt --name-agent"
          },
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/send_event.py --source-app $SOURCE_APP --event-type UserPromptSubmit --summarize"
          }
        ]
      }
    ]
  }
}
```

### How hooks are wired up

- Every hook entry has a `"type": "command"` field and a `"command"` string that Claude Code runs as a shell command.
- The `"matcher"` field is an optional regex applied to the tool name for `PreToolUse`/`PostToolUse` events. An empty string (`""`) matches every tool. The `Write|Edit|MultiEdit` matcher on the second `PostToolUse` block restricts the prettier and eslint hooks to file-writing tools only.
- Multiple hook entries under the same event key run sequentially in array order.
- All scripts are invoked with `uv run`, which auto-installs inline-declared dependencies (the `# dependencies = [...]` block at the top of each file) without requiring a virtual environment.
- `$CLAUDE_PROJECT_DIR` resolves to the configured project directory; hook scripts therefore always run against the correct project regardless of the current working directory.
- The `permissions` block grants `defaultMode: bypassPermissions` but hard-denies `git push --force`, `git push -f`, and `rm -rf` at the permission level; `pre_tool_use.py` adds a second, more thorough layer of `rm -rf` blocking.

---

## Available Hooks

### session_start.py

**Event:** `SessionStart`
**CLI flags registered:** `--load-context`, `--announce` (only `--load-context` is active in settings)
**Purpose:** Runs once when Claude Code creates, resumes, or clears a session. Logs the raw event payload to `logs/session_start.json` and, when `--load-context` is passed, injects development context into the session as `hookSpecificOutput.additionalContext`.

**Key behavior:**

- `load_development_context()` assembles context from:
  - Current timestamp and session source (`startup`, `resume`, or `clear`)
  - `git rev-parse --abbrev-ref HEAD` for branch name
  - `git status --porcelain` for uncommitted file count
  - Contents (first 1 000 characters each) of any of these files that exist: `specs/PROGRESS.md`, `specs/DECISIONS.md`, `.claude/CONTEXT.md`, `.claude/TODO.md`, `TODO.md`, `.github/ISSUE_TEMPLATE.md`
  - Output of `gh issue list --limit 5 --state open` if the `gh` CLI is available
- The assembled context is returned via a JSON `hookSpecificOutput` block that Claude Code injects into the model's context window.
- When `--announce` is passed (not currently active in settings), it calls the pyttsx3 TTS script with a source-specific message ("Claude Code session started", "Resuming previous session", or "Starting fresh session").
- All errors are silently swallowed; the hook always exits `0`.

---

### pre_tool_use.py

**Event:** `PreToolUse`
**Purpose:** Guards against destructive shell commands and logs every tool invocation to `logs/pre_tool_use.json`.

**Key behavior — dangerous command blocking:**

The hook exits `2` (blocking the tool call) when the `Bash` tool is used and the command matches any of the following patterns:

- `rm` with combined recursive+force flags in any order: `-rf`, `-fr`, `-Rf`, `--recursive --force`, `--force --recursive`, `-r ... -f`, `-f ... -r`
- `rm` with any recursive flag (`-r`) targeting paths that include: `/`, `/*`, `~`, `~/`, `$HOME`, `..`, `*`, `.`

The message written to stderr is: `BLOCKED: Dangerous rm command detected and prevented`

There is also a commented-out `.env` file access check (`is_env_file_access`) that can be enabled to block reads and writes to `.env` files (while allowing `.env.sample`). It covers the `Read`, `Edit`, `MultiEdit`, `Write`, and `Bash` tools.

When no block fires, the full event payload is appended to `logs/pre_tool_use.json`.

---

### post_tool_use.py

**Event:** `PostToolUse` (first, matcher-less entry — runs for every tool)
**Purpose:** Appends every tool result event to `logs/post_tool_use.json` for observability and debugging.

**Key behavior:** Minimal; reads JSON from stdin and appends it to the log file. No blocking, no side effects. Always exits `0`.

---

### prettier_on_write.py

**Event:** `PostToolUse` (second entry, matcher `Write|Edit|MultiEdit`)
**Purpose:** Auto-formats JavaScript, ES module, and CSS files that Claude writes inside the `apps/mas/web-components/` or `apps/mas/studio/` subdirectories using the project's own Prettier binary.

**Key behavior:**

- Only acts on files with extensions `.js`, `.mjs`, or `.css`.
- Resolves the MAS root as `$CLAUDE_PROJECT_DIR/apps/mas`.
- Checks that the written file is under `mas/web-components/` or `mas/studio/` (any other path is skipped).
- Requires `apps/mas/node_modules/.bin/prettier` to exist; silently skips if not found.
- Runs `prettier --write <file>` with `cwd` set to the MAS root.
- Always exits `0`; formatting failures are swallowed.

---

### eslint_on_write.py

**Event:** `PostToolUse` (second entry, matcher `Write|Edit|MultiEdit`)
**Purpose:** Auto-fixes ESLint violations in JavaScript files that Claude writes inside `apps/experience-qa/`.

**Key behavior:**

- Only acts on files with extensions `.js`, `.mjs`, or `.cjs`.
- Restricts to files under `$CLAUDE_PROJECT_DIR/apps/experience-qa`.
- Requires `$CLAUDE_PROJECT_DIR/node_modules/.bin/eslint` to exist; silently skips if not found.
- Runs `eslint --fix <file>` with `cwd` set to `$CLAUDE_PROJECT_DIR` (picks up the root-level ESLint 9 flat config).
- Always exits `0`; lint failures are swallowed.

---

### notification.py

**Event:** `Notification`
**CLI flags registered:** `--notify` (not active in current settings)
**Purpose:** Logs every notification event to `logs/notification.json` and optionally speaks an alert via TTS.

**Key behavior:**

- Appends the raw event payload to the log file unconditionally.
- TTS announcement only fires when `--notify` is passed **and** the notification message is not the generic `"Claude is waiting for your input"` string.
- When TTS is triggered, `get_tts_script_path()` selects an engine by priority: ElevenLabs (if `ELEVENLABS_API_KEY` is set) > OpenAI (if `OPENAI_API_KEY` is set) > pyttsx3 (offline fallback).
- The spoken message is `"Your agent needs your input"`, with a 30% chance of prepending the engineer's name when `ENGINEER_NAME` is set in the environment.

---

### stop.py

**Event:** `Stop`
**CLI flags registered:** `--chat`, `--notify` (neither is active in current settings — the `send_event.py` companion uses `--add-chat` separately)
**Purpose:** Logs the session-end event to `logs/stop.json` and optionally copies the session transcript and announces completion via TTS.

**Key behavior:**

- Appends the raw event payload to the log file.
- `--chat`: reads the `.jsonl` transcript at `input_data["transcript_path"]`, converts it to a JSON array, and writes it to `logs/chat.json`.
- `--notify`: generates an LLM completion message and speaks it. LLM priority is OpenAI > Anthropic > Ollama; if all fail, a random phrase from a hardcoded list is used (`"Work complete!"`, `"All done!"`, `"Task finished!"`, `"Job complete!"`, `"Ready for next task!"`). The spoken message may include the engineer's name (30% chance when `ENGINEER_NAME` is set).

---

### subagent_stop.py

**Event:** `SubagentStop`
**CLI flags registered:** `--chat`, `--notify` (neither active in current settings)
**Purpose:** Identical in structure to `stop.py` but fires when a sub-agent finishes rather than the top-level agent.

**Key behavior:**

- Same log-append and `--chat` transcript logic as `stop.py`.
- TTS message is a fixed `"Subagent Complete"` (no LLM generation, no engineer name).
- TTS engine selection follows the same ElevenLabs > OpenAI > pyttsx3 priority.

---

### send_event.py

**Event:** All events (registered alongside every other hook via the settings)
**Purpose:** Ships a structured observability event to a local server at `http://localhost:4000/events`. Acts as the telemetry layer for the multi-agent harness.

**Required CLI flags:**

| Flag | Description |
|------|-------------|
| `--source-app` | Application name, injected from `$SOURCE_APP` |
| `--event-type` | The hook event name (e.g., `PreToolUse`) |

**Optional CLI flags:**

| Flag | Description |
|------|-------------|
| `--server-url` | Override default server URL |
| `--add-chat` | Read the session transcript and attach the full conversation as `chat` |
| `--summarize` | Call `utils/summarizer.py` to generate a one-sentence AI summary and attach it as `summary` |

**Key behavior:**

- Reads the model name from the session transcript via `utils/model_extractor.py` (with per-session file caching).
- Constructs an event payload with fields: `source_app`, `session_id`, `hook_event_type`, `payload`, `timestamp` (Unix milliseconds), `model_name`.
- `--add-chat` is only used on the `Stop` event (per settings), which appends the entire transcript to the payload.
- `--summarize` is used on all events; it calls `generate_event_summary()` from `utils/summarizer.py` which requires `ANTHROPIC_API_KEY`. If the key is absent or the API call fails, the event is sent without a summary.
- The HTTP POST uses Python's built-in `urllib.request` — no third-party HTTP client dependency.
- Always exits `0` regardless of server availability, so a down observability server never blocks Claude.

---

### user_prompt_submit.py

**Event:** `UserPromptSubmit`
**CLI flags registered (all active in settings):** `--log-only`, `--store-last-prompt`, `--name-agent`
**Purpose:** Logs every user prompt, maintains a per-session prompt history in `.claude/data/sessions/`, and optionally generates a unique name for the session's agent.

**Key behavior:**

- `--log-only`: Appends the full event payload to `logs/user_prompt_submit.json`. With this flag set, `--validate` is bypassed even if also passed.
- `--store-last-prompt`: Writes (or updates) `.claude/data/sessions/<session_id>.json` with the new prompt appended to a `prompts` array. This file is read by the status line to display the last prompt.
- `--name-agent`: On the first prompt of a new session, generates a one-word agent name and stores it as `agent_name` in the session JSON. Name generation tries Anthropic first (`utils/llm/anth.py --agent-name`), then Ollama as fallback. The name is validated: it must be a single alphanumeric word. If both LLM calls fail, the session proceeds without a name.
- `--validate` (not active): Checks prompts against a `blocked_patterns` list (empty by default) and exits `2` to block prompts that match.
- A prompt can also inject additional context by printing to stdout (the printed text is appended to the user's prompt).

---

### pre_compact.py

**Event:** `PreCompact` (note: `send_event.py` handles this event in settings; `pre_compact.py` itself is not currently registered but is present for optional use)
**CLI flags registered:** `--backup`, `--verbose`
**Purpose:** Logs pre-compaction events and optionally backs up the full transcript before it is summarized.

**Key behavior:**

- Appends the raw event to `logs/pre_compact.json`.
- `trigger` field in the payload is either `"manual"` (user-initiated compact) or `"auto"` (context window full).
- `--backup`: copies the transcript file to `logs/transcript_backups/<session>_pre_compact_<trigger>_<timestamp>.jsonl`.
- `--verbose`: prints a human-readable description of the compaction event to stdout, including the backup path if one was created.

---

## Utility Modules

All utilities live under `.claude/hooks/utils/`.

### utils/constants.py

Provides shared path helpers for the log directory.

- `LOG_BASE_DIR`: resolves to the `CLAUDE_HOOKS_LOG_DIR` environment variable, defaulting to `"logs"`.
- `get_session_log_dir(session_id)`: returns `Path(LOG_BASE_DIR) / session_id`.
- `ensure_session_log_dir(session_id)`: calls `mkdir(parents=True, exist_ok=True)` on the session log directory and returns the path.

Note: The main hook scripts currently construct their log paths directly rather than calling these helpers; `constants.py` is available for future refactoring.

---

### utils/summarizer.py — `generate_event_summary(event_data)`

Generates a one-sentence natural language summary of a hook event using the Anthropic API.

- Requires `ANTHROPIC_API_KEY` in the environment; returns `None` if absent.
- Uses `claude-haiku-4-5-20251001` with `max_tokens=50` and `temperature=0.3`.
- Extracts tool name and file/command context for `PreToolUse`/`PostToolUse`, the prompt text for `UserPromptSubmit`, and the notification message for `Notification`.
- Returns `None` on any error; callers are expected to handle the absent summary gracefully.
- Has a standalone CLI: pass a JSON file path as argv[1] or pipe JSON on stdin.

---

### utils/model_extractor.py — `get_model_from_transcript(session_id, transcript_path, ttl=60)`

Reads the session `.jsonl` transcript to find the model name used by the most recent assistant turn.

- Uses file-based caching at `.claude/data/claude-model-cache/<session_id>.json` with a configurable TTL (default 60 seconds).
- Scans the transcript in reverse order, looking for entries with `type == "assistant"` that have a `message.model` field.
- Returns an empty string if the transcript does not exist, is unreadable, or contains no assistant turns with a model field.
- Cache entries store `model`, `timestamp`, and `ttl`; stale or corrupted cache entries trigger a fresh scan.

---

### utils/llm/anth.py

Anthropic Claude integration. Uses `claude-haiku-4-5-20251001` for all calls (fastest model).

**Functions:**

- `prompt_llm(prompt_text)`: Base method. Sends a single user message with `max_tokens=100`, `temperature=0.3`. Returns the response text or `None` on error.
- `generate_completion_message()`: Prompts the model for a short (under 10 words), positive task-completion phrase. Optionally includes the engineer's name (~30% of the time) when `ENGINEER_NAME` is set. Returns the cleaned first line of the response.
- `generate_agent_name()`: Generates a single alphanumeric word as an agent identity. Uses `max_tokens=20`. Falls back to a random name from a 20-item example list if the API is unavailable or the generated name fails validation (must be 3–20 characters).

**CLI:** `anth.py --completion` | `anth.py --agent-name` | `anth.py 'arbitrary prompt'`

---

### utils/llm/oai.py

OpenAI integration. Mirrors the same interface as `anth.py`.

- `prompt_llm()`: Uses `gpt-4.1-nano` with `max_tokens=100`, `temperature=0.7`.
- `generate_completion_message()`: Same prompt template as the Anthropic version.
- `generate_agent_name()`: Uses `gpt-4o-mini` with `max_tokens=20`, `temperature=0.7`. Same validation logic and fallback names as `anth.py`.

**CLI:** `oai.py --completion` | `oai.py --agent-name` | `oai.py 'arbitrary prompt'`

---

### utils/llm/ollama.py

Local Ollama integration using the OpenAI-compatible API at `http://localhost:11434/v1`.

- `prompt_llm()`: Uses the model specified by `OLLAMA_MODEL` env var, defaulting to `gpt-oss:20b`. `max_tokens=1000`. Does not require an API key (`api_key='ollama'` is a placeholder).
- `generate_completion_message()`: Same prompt template as the other LLM modules.
- `generate_agent_name()`: Same validation and fallback logic. No API key check since Ollama is local.

**CLI:** `ollama.py --completion` | `ollama.py --agent-name` | `ollama.py 'arbitrary prompt'`

---

### utils/tts/elevenlabs_tts.py

ElevenLabs Flash v2.5 TTS engine (~75 ms latency).

- Requires `ELEVENLABS_API_KEY`.
- Uses voice ID `WejK3H1m7MI9CHnIjW9K` and model `eleven_flash_v2_5` with `mp3_44100_128` output.
- Accepts the text to speak as CLI arguments: `elevenlabs_tts.py "text to speak"`.
- Exits `1` if the API key is missing or the `elevenlabs` package is unavailable.

---

### utils/tts/openai_tts.py

OpenAI streaming TTS engine.

- Requires `OPENAI_API_KEY`.
- Uses model `gpt-4o-mini-tts` with the `nova` voice and the instruction `"Speak in a cheerful, positive yet professional tone."`.
- Streams audio through `openai.helpers.LocalAudioPlayer` (async).
- Accepts the text to speak as CLI arguments: `openai_tts.py "text to speak"`.
- Exits `1` if the API key is missing or required packages are unavailable.

---

### utils/tts/pyttsx3_tts.py

Offline TTS fallback using `pyttsx3`.

- No API key required; uses the platform's native speech engine.
- Configured at 180 WPM, 0.8 volume.
- Accepts the text to speak as CLI arguments: `pyttsx3_tts.py "text to speak"`.
- When invoked with no arguments, picks a random phrase from the default completion message list.
- Exits `1` on import failure or engine error.

---

### TTS engine selection

Several hooks share a `get_tts_script_path()` helper that selects an engine at runtime:

1. **ElevenLabs** — if `ELEVENLABS_API_KEY` is set and `elevenlabs_tts.py` exists.
2. **OpenAI** — if `OPENAI_API_KEY` is set and `openai_tts.py` exists.
3. **pyttsx3** — offline fallback, no API key required.
4. `None` — if no script file is found; caller skips TTS silently.

---

## Adding New Hooks

### 1. Create the script

Place a new Python script in `.claude/hooks/`. Use the standard `uv` inline script header to declare dependencies:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "some-package",
# ]
# ///

import json
import sys

def main():
    try:
        input_data = json.load(sys.stdin)

        # Your logic here.

        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)

if __name__ == "__main__":
    main()
```

Key conventions observed by every hook in this codebase:

- Read event data with `json.load(sys.stdin)` or `json.loads(sys.stdin.read())`.
- Always exit `0` unless you intend to block — exit `2` to block and write a reason to stderr.
- Swallow all exceptions silently (`except Exception: sys.exit(0)`) so a buggy hook never interrupts Claude.
- Write logs to `logs/<hook_name>.json` as a JSON array (append, not overwrite).

### 2. Register the hook in settings.json

Open `.claude/settings.json` and add an entry under the appropriate event key:

```json
"PreToolUse": [
  {
    "matcher": "",
    "hooks": [
      {
        "type": "command",
        "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/my_new_hook.py --my-flag"
      }
    ]
  }
]
```

Use `"matcher": ""` to match all tools, or a regex such as `"Bash"` or `"Write|Edit|MultiEdit"` to restrict to specific tools.

### 3. Available event fields by event type

| Event | Notable fields in stdin payload |
|-------|---------------------------------|
| `SessionStart` | `session_id`, `source` (`"startup"` / `"resume"` / `"clear"`) |
| `UserPromptSubmit` | `session_id`, `prompt` |
| `PreToolUse` | `session_id`, `tool_name`, `tool_input` |
| `PostToolUse` | `session_id`, `tool_name`, `tool_input`, `tool_response` |
| `Notification` | `session_id`, `message` |
| `Stop` | `session_id`, `stop_hook_active`, `transcript_path` |
| `SubagentStop` | `session_id`, `stop_hook_active`, `transcript_path` |
| `PreCompact` | `session_id`, `transcript_path`, `trigger` (`"manual"` / `"auto"`), `custom_instructions` |

### 4. Environment variables available to hooks

| Variable | Set in | Purpose |
|----------|--------|---------|
| `CLAUDE_PROJECT_DIR` | `settings.json` env block | Absolute path to the project root |
| `SOURCE_APP` | `settings.json` env block | Application identifier sent with observability events |
| `ANTHROPIC_API_KEY` | `.env` / shell | Used by `anth.py` and `summarizer.py` |
| `OPENAI_API_KEY` | `.env` / shell | Used by `oai.py` and `openai_tts.py` |
| `ELEVENLABS_API_KEY` | `.env` / shell | Used by `elevenlabs_tts.py` |
| `ENGINEER_NAME` | `.env` / shell | Personalizes TTS messages (optional) |
| `OLLAMA_MODEL` | `.env` / shell | Ollama model override, defaults to `gpt-oss:20b` |
| `CLAUDE_HOOKS_LOG_DIR` | `.env` / shell | Log directory override, defaults to `logs` |
