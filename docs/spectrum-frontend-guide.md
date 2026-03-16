# Spectrum Frontend Guide

How the Spectrum frontend stack works together — skills, agents, and commands — with practical use cases.

## The Three Layers

| Layer | Type | What it does | How it activates |
|-------|------|-------------|------------------|
| `frontend-design` | Skill | Design philosophy — typography, layout, color, anti-patterns | Auto-loads when you mention frontend/Spectrum/UI work |
| `adobe-spectrum` | Agent | Doc lookup — "what props does X have?" | Claude spawns it as a subagent |
| `agent-frontend` | Agent | Full builder — design + lookup + code in one shot | Claude spawns it as a subagent |

Supporting commands: `/spectrum-check` (audit existing code), `/scaffold` (new app boilerplate).

## How They Connect

```
You say something about building UI
        │
        ├─ Light guidance needed?
        │   └─ frontend-design skill auto-loads into context
        │      Claude uses it to inform its own code writing
        │
        ├─ "What component should I use for X?"
        │   └─ adobe-spectrum agent spawns
        │      Calls MCP tools → returns docs
        │      (no code written)
        │
        └─ "Build me a page / component / refactor this"
            └─ agent-frontend spawns
               1. Reads frontend-design skill
               2. Calls MCP tools for component docs
               3. Writes the actual code
               4. Self-checks for anti-patterns
               (returns working code)
```

## Quick Reference: What to Say

| You want to... | Say something like... | Routes to |
|---|---|---|
| Build a new component/page | "Build a dashboard with status cards and a data table" | `agent-frontend` |
| Refactor HTML → Spectrum | "Convert this form to use Spectrum S2 components" | `agent-frontend` |
| Look up a component | "What props does DatePicker have?" | `adobe-spectrum` |
| Compare components | "Should I use Dialog or DialogTrigger here?" | `adobe-spectrum` |
| Scaffold a new app | `/scaffold my-app "landing page with hero and feature cards"` | `/scaffold` |
| Audit Spectrum adoption | `/spectrum-check` | `/spectrum-check` |
| Design guidance while coding | Just start coding — the skill auto-loads | `frontend-design` skill |

---

## Use Case 1: Build a New Page

**Prompt:**

> Build a settings page for the QA app with a form for configuring test environments — name, URL, region selector, and an enable/disable toggle. Include a save button and toast confirmation.

**What happens:**

1. Claude detects this is a build task → spawns `agent-frontend`
2. Agent reads `frontend-design/SKILL.md` → picks **clean & minimal** direction (productivity tool)
3. Agent calls MCP tools:
   - `search_components("form")` → finds TextField, Picker, Switch
   - `get_component("TextField")` → gets exact props
   - `get_component("Picker")` → gets region selector props
   - `get_component("Switch")` → gets toggle props
   - `get_component("Button")` → confirms `variant="accent"` for primary save action
4. Agent writes the page file using:
   - `<Flex direction="column" gap="size-200">` for form layout (not raw divs)
   - `<Heading size="L">` for page title (not `<h1>`)
   - `<TextField>` for name/URL (not `<input>`)
   - `<Picker>` for region (not `<select>`)
   - `<Switch>` for enable/disable (not `<input type="checkbox">`)
   - `<Button variant="accent">` for save (semantic choice, not default)
   - `<ToastQueue>` for confirmation (not `alert()`)
5. Agent self-checks: no raw HTML, no pixel values, no default-everything
6. Returns the working component with imports and design rationale

**You get back:** A complete `SettingsPage.tsx` with correct `@react-spectrum/s2` imports, density-consistent layout, and semantic color choices.

---

## Use Case 2: Refactor Existing HTML to Spectrum

**Prompt:**

> This component uses raw HTML buttons and divs. Refactor it to use Spectrum S2: `apps/experience-qa/client/src/components/RunToolbar.jsx`

**What happens:**

1. Claude detects refactoring to Spectrum → spawns `agent-frontend`
2. Agent reads the existing file with `Read` tool — finds:
   ```jsx
   <div style={{ display: 'flex', gap: '8px' }}>
     <button onClick={onStart}>Start</button>
     <button onClick={onStop}>Stop</button>
     <button onClick={onExport}>Export</button>
     <span className="status-dot green" />
   </div>
   ```
3. Agent reads `frontend-design/SKILL.md` → notes:
   - "Use `<ActionGroup>` for multi-action toolbars instead of a row of `<Button>`"
   - "Use `<StatusLight>` for ambient state"
4. Agent calls MCP tools:
   - `get_component("ActionGroup")` → confirms props: `onAction`, items pattern
   - `get_component("ActionButton")` → individual button props
   - `get_component("StatusLight")` → confirms `variant="positive"` for green
5. Agent writes the refactored code:
   ```jsx
   <Flex alignItems="center" gap="size-100">
     <ActionGroup onAction={handleAction}>
       <ActionButton key="start">Start</ActionButton>
       <ActionButton key="stop">Stop</ActionButton>
       <ActionButton key="export">Export</ActionButton>
     </ActionGroup>
     <StatusLight variant="positive">Running</StatusLight>
   </Flex>
   ```
6. Self-check passes — no raw HTML remains

**You get back:** The refactored component with before/after diff and the S2 imports needed.

---

## Use Case 3: Quick Component Lookup (No Build)

**Prompt:**

> What's the difference between Meter and ProgressBar in Spectrum? When should I use which?

**What happens:**

1. Claude detects this is a **question**, not a build task → spawns `adobe-spectrum` agent (lighter, lookup-only)
2. Agent calls MCP tools:
   - `get_component("Meter")` → reads description, props, examples
   - `get_component("ProgressBar")` → reads description, props, examples
3. Agent returns a concise comparison:

   | | Meter | ProgressBar |
   |---|---|---|
   | **Purpose** | Shows a known quantity relative to a max | Shows progress toward completion |
   | **Use when** | Disk usage, budget spent, quota consumed | File upload, task completion |
   | **Key prop** | `value` + `maxValue` (known ratio) | `value` (0-100) or `isIndeterminate` |
   | **Visual** | Static fill bar | Animated, can be indeterminate |
   | **Import** | `@react-spectrum/s2` | `@react-spectrum/s2` |

**You get back:** A direct answer with props and guidance. No code written, no files touched.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────┐
│                Main Claude Context              │
│                                                 │
│  frontend-design skill (auto-loaded ~3KB)       │
│  ┌─────────────────────────────────────────┐    │
│  │ Design direction, typography, layout,   │    │
│  │ color tokens, anti-patterns             │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  ┌──────────────┐    ┌───────────────────────┐  │
│  │ adobe-       │    │ agent-frontend        │  │
│  │ spectrum     │    │                       │  │
│  │ (lookup)     │    │ (builder)             │  │
│  │              │    │                       │  │
│  │ MCP tools    │    │ MCP tools             │  │
│  │ Read         │    │ Read/Write/Edit       │  │
│  │              │    │ Grep/Glob/Bash        │  │
│  │ Returns:     │    │                       │  │
│  │ docs only    │    │ Reads frontend-design │  │
│  │              │    │ Looks up components   │  │
│  │              │    │ Writes code           │  │
│  │              │    │ Self-checks output    │  │
│  │              │    │                       │  │
│  │              │    │ Returns:              │  │
│  │              │    │ working code          │  │
│  └──────────────┘    └───────────────────────┘  │
│                                                 │
│  /spectrum-check ──── post-build audit          │
│  /scaffold ────────── new app boilerplate        │
└─────────────────────────────────────────────────┘
```
