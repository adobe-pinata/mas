# Output Styles Reference

## What are Output Styles?

Output styles are configuration files stored in `.claude/output-styles/` that instruct Claude on how to format and structure its responses. Each style is a Markdown file with a YAML frontmatter block (providing a `name` and `description`) followed by detailed formatting rules that override Claude's default response behavior.

By applying a style, you shape the entire structure of Claude's output — from how information is visually organized, to whether responses include audio announcements, tool call logs, or git diffs. Styles are composable in spirit: some styles (like `observable-tools-diffs-tts`) combine behaviors from simpler styles (tool logging, diff reporting, TTS) into a single configuration.

---

## Available Styles

### bullet-points

**Purpose:** Forces all response content into a strict hierarchical bullet-point structure, replacing prose paragraphs with nested lists.

**Best for:** Quickly scannable summaries, task completion reports, technical breakdowns, and any situation where a reader needs to locate specific information at a glance rather than reading sequentially.

**Key characteristics:**
- Dashes (`-`) for unordered information at all nesting levels; numbers for ordered sequences
- Never mixes ordered and unordered markers at the same indentation level
- Maximum of four nesting levels; each child bullet must directly support its parent
- Each bullet is limited to 1-2 lines
- Action items are prefixed with `ACTION:` or `TODO:`
- Code snippets appear as separate fenced blocks after their relevant bullet
- Consistent 2-space indentation per nesting level
- Task completion responses follow a fixed pattern: summary bullets, issues/considerations, then action items

---

### genui

**Purpose:** Generates complete, self-contained HTML5 documents with embedded modern CSS after every request, then automatically opens them in the default browser.

**Best for:** Visualizing data, creating shareable reports, producing browser-ready output, or any situation where a rendered visual result is more useful than plain text.

**Key characteristics:**
- Every response produces a full `<!DOCTYPE html>` document — no partial snippets
- All CSS is embedded in a `<style>` block; zero external dependencies
- Consistent visual theme: primary blue `#3498db`, dark blue `#2c3e50` for headings, system font stack, 900px max-width layout
- Styled section types: info (light blue), success (light green), warning (light orange), error (light red) — each with a colored left border
- Code blocks use a `#007acc` left-border accent and support language class names for syntax highlighting
- Interactive elements (buttons, collapsible sections, copy-to-clipboard) added when appropriate
- Files saved to `/tmp/` with the naming convention `cc_genui_<description>_YYYYMMDD_HHMMSS.html`
- The `open` command is executed automatically after file creation
- Response ends with a brief summary and the file path

---

### html-structured

**Purpose:** Formats all responses as clean, semantic HTML5 using proper document structure elements — without a full page shell or embedded styles.

**Best for:** Responses that will be consumed by a downstream renderer, injected into an existing web page, or parsed programmatically while still needing human-readable markup.

**Key characteristics:**
- Entire response wrapped in `<article>`; sections use `<header>`, `<main>`, `<section>`, `<aside>`, `<nav>`
- Heading hierarchy: `<h2>` for main sections, `<h3>` for subsections, `<h4>` and below as needed
- Code blocks use `<pre><code class="language-{lang}">` with optional `data-file` and `data-line` attributes
- Lists use `<ul>`/`<ol>` with `<li>`; tables include `<thead>`, `<tbody>`, `scope` attributes, and optional `<caption>`
- `data-type="info|warning|error|success"` attribute marks status sections
- `data-action="create|edit|delete"` attribute marks file operation elements
- Minimal inline styles only (monospace background for code, left-border accent for code blocks)
- Emphasis via `<strong>` and `<em>`; no Markdown syntax

---

### markdown-focused

**Purpose:** Applies the full breadth of Markdown formatting features strategically to maximize readability and information architecture.

**Best for:** General-purpose responses where the output will render as Markdown (GitHub, documentation sites, Markdown editors), especially when content spans multiple types — prose, code, comparisons, and action items.

**Key characteristics:**
- Header hierarchy (`##`, `###`, `####`) creates clear document sections; `---` horizontal rules separate major topics
- Inline code for commands, file names, function names, and variables
- Fenced code blocks always include a language identifier
- **Bold** for important concepts and warnings; *italics* for technical terms and names
- Blockquotes (`>`) for callouts, warnings, and key insights
- Tables for comparisons, configuration options, and structured data
- Task lists (`- [ ]` / `- [x]`) for actionable items
- Numbered lists for sequential steps; bulleted lists for non-ordered related items
- Optimized for both terminal and web rendering

---

### observable-tools-diffs

**Purpose:** Adds transparent reporting of tool calls and git diffs to every response where code or files were changed, plus a one-sentence outcome summary.

**Best for:** Agentic workflows where the user wants full visibility into what actions were taken and what changed in the codebase, without audio feedback.

**Key characteristics:**
- Normal response content comes first, unchanged
- After tool use: an ordered list of every tool called in the current response, formatted as TypeScript interface syntax with `...` placeholders for values and a one-line comment per call
- After code changes: a git diff report covering only files modified in this response — filename, one-sentence summary of changes, lines added vs removed, and a fenced diff block
- New files are reported by name only (no diff)
- Response ends with a single sentence directly stating the outcome
- Tool call list is omitted for conversational responses with no tool use
- Git diff section is omitted when no code was written

---

### observable-tools-diffs-tts

**Purpose:** Extends `observable-tools-diffs` with a spoken audio announcement at the end of every response, delivered via ElevenLabs TTS.

**Best for:** Hands-free or heads-down development sessions where the user (Dan) wants to hear a verbal confirmation of what was accomplished in addition to the written diff and tool log.

**Key characteristics:**
- All behaviors of `observable-tools-diffs` are included (tool call log, git diff report)
- Additionally, every response — including simple conversational replies — ends with a `---` separator, an `## Audio Summary for Dan` heading, and a spoken message
- The TTS message addresses Dan directly, focuses on outcome rather than process, and is kept to one sentence under 20 words
- The ElevenLabs TTS script is executed (not just shown) via `uv run`
- Audio summary always comes last, after the git diff report when both are present
- Conversational tone: "Dan, I've updated your..." or "Fixed the bug in..."

---

### table-based

**Purpose:** Structures response content using Markdown tables as the primary organizational unit wherever data can reasonably be presented in rows and columns.

**Best for:** Comparisons, configuration references, multi-step processes with context, analysis results with severity or priority, and any response where scanning across attributes of multiple items is the primary reading pattern.

**Key characteristics:**
- Four named table patterns: Comparison (options/tools), Step (processes), Information (data points), Analysis (findings/issues)
- Table headers are clear and descriptive; cell content is concise but informative
- Formatting within cells is allowed: bold for emphasis, inline code for technical terms
- Column alignment follows content type: left for text, center for status indicators, right for numbers
- Response structure itself is table-defined: Summary (paragraph + summary table), Details (tables by category), Actions (step table with priorities)
- Code-related content organized as tables: file changes, configuration options, test results, dependencies

---

### tts-summary-base

**Purpose:** Appends a spoken audio summary to every response via ElevenLabs TTS, without tool call logging or git diff reporting.

**Best for:** Conversational or task-completion workflows where the user wants audio confirmation of what was done, but does not need the additional overhead of tool transparency or diff output.

**Key characteristics:**
- Standard response content is otherwise unaffected
- Every response ends with a `---` separator and an `## Audio Summary for Dan` section
- Message addresses Dan directly, focuses on user benefit, uses conversational language
- One sentence, under 20 words
- The TTS command is executed (not just displayed) via `uv run`
- Applies to every response without exception, including simple queries

---

### tts-summary

**Purpose:** Combines git diff reporting, ordered tool call logging, and spoken audio summary into a single comprehensive observability style.

**Best for:** Full-observability agentic sessions where the user wants to see every tool used, every code change made, and also receive an audio announcement — the most feature-rich of the TTS styles.

**Key characteristics:**
- All behaviors of `observable-tools-diffs` are included (tool call log in TypeScript syntax, git diff report)
- Additionally, every response ends with an `## Audio Summary for Dan` section and ElevenLabs TTS execution
- Audio summary comes last, after the git diff report when both are present
- Message is direct, outcome-focused, conversational, one sentence under 20 words
- TTS command is always executed, not just shown
- Effectively a superset of `tts-summary-base` plus `observable-tools-diffs`

---

### ultra-concise

**Purpose:** Eliminates all non-essential words, formatting, and explanation from responses, producing the shortest possible output.

**Best for:** Experienced developers who want maximum signal-to-noise ratio, rapid iteration sessions, or situations where response length has a direct cost (token budgets, screen space, reading time).

**Key characteristics:**
- No greetings, pleasantries, or filler phrases
- Code and commands appear first; brief status line after if needed
- Sentence fragments preferred over full sentences
- Single-line summaries only — no multi-paragraph explanations
- Obvious steps are omitted entirely
- Commentary on tool outputs is skipped
- Explanations are included only when their absence would cause errors
- Assumes high technical expertise in the reader
- Framing: focused building and shipping, not conversation

---

### yaml-structured

**Purpose:** Formats all responses as valid, parseable YAML using a consistent schema of named top-level keys.

**Best for:** Responses that will be consumed programmatically, piped into other tools, parsed by scripts, or stored as structured data. Also useful when response content naturally maps to configuration-file semantics.

**Key characteristics:**
- 2-space indentation throughout; strict YAML syntax
- Standard top-level keys: `task`, `details`, `files`, `commands`, `status`, `next_steps`, `notes`
- File paths are always absolute
- YAML comments (`#`) used for explanatory context
- Lists use hyphen (`-`) notation; objects use key-value pairs
- Appropriate YAML data types used: strings, numbers, booleans, lists, objects
- Nesting is kept logical and not overly deep
- Responses wrapped in a fenced `yaml` code block

---

## Choosing a Style

### Comparison Table

| Style | Output Format | Tool Log | Git Diff | Audio (TTS) | Best Audience |
|---|---|---|---|---|---|
| `bullet-points` | Nested bullet lists | No | No | No | Anyone needing scannable output |
| `genui` | Full HTML file in browser | No | No | No | Visual/browser-based output |
| `html-structured` | Semantic HTML snippet | No | No | No | Web renderers, parsers |
| `markdown-focused` | Full Markdown | No | No | No | Docs, GitHub, Markdown editors |
| `observable-tools-diffs` | Normal + tool log + diff | Yes | Yes | No | Developers wanting transparency |
| `observable-tools-diffs-tts` | Normal + tool log + diff + audio | Yes | Yes | Yes | Hands-free dev sessions |
| `table-based` | Markdown tables | No | No | No | Comparisons, structured data |
| `tts-summary-base` | Normal + audio | No | No | Yes | Audio confirmation only |
| `tts-summary` | Normal + tool log + diff + audio | Yes | Yes | Yes | Full observability + audio |
| `ultra-concise` | Minimal text | No | No | No | Expert users, speed-focused |
| `yaml-structured` | YAML document | No | No | No | Programmatic consumption |

### Recommendations by Use Case

**I want clean, readable documentation or explanations.**
Use `markdown-focused`. It applies the full Markdown feature set strategically and renders well in GitHub, documentation sites, and most Markdown editors.

**I need to quickly scan results or a task summary.**
Use `bullet-points`. Everything is broken into hierarchical lists optimized for scanning rather than reading.

**I'm comparing options, tools, or configurations.**
Use `table-based`. Tables reduce cognitive load when evaluating multiple items across shared attributes.

**I want to see exactly what tools were called and what code changed.**
Use `observable-tools-diffs`. Every tool call is logged in order and every code change produces a diff report.

**I want the above, plus spoken audio confirmation when tasks complete.**
Use `observable-tools-diffs-tts` or `tts-summary` (they are functionally equivalent based on the file contents).

**I want audio confirmation only, without tool logs or diffs.**
Use `tts-summary-base`. It appends a spoken summary to every response without any additional overhead.

**I want a browser-rendered visual output.**
Use `genui`. It generates a fully styled HTML file and opens it automatically — ideal for reports, data visualization, or shareable results.

**My response will be consumed by a script or another tool.**
Use `yaml-structured` for structured key-value data, or `html-structured` if the consumer expects HTML with semantic markup and data attributes.

**I want maximum speed with minimum text.**
Use `ultra-concise`. It strips all filler and produces the shortest possible response, assuming expert-level technical knowledge.
