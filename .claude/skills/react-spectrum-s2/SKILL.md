---
name: react-spectrum-s2
description: Look up React Spectrum 2 (S2) component documentation — props, examples, categories, and design patterns. Use when building or modifying UI with React Spectrum, Spectrum 2, S2 components, or Adobe's design system. Also use when migrating from Spectrum 1 to S2, searching for the right component for a UI pattern, or checking S2-specific props and styling.
---

# react-spectrum-s2

React Spectrum 2 (S2) component documentation via MCP.

**MCP server:** `react-spectrum-s2` (must be running — registered in `mcp/.mcp.react-spectrum-s2.json`)

## Tools

| Tool | Input | Returns |
|------|-------|---------|
| `mcp__react-spectrum-s2__list_all_components` | `category?: string` | All 90 S2 components, optionally filtered by category |
| `mcp__react-spectrum-s2__get_component` | `name: string` | Full component docs — props, examples, description |
| `mcp__react-spectrum-s2__search_components` | `query: string` | Components matching a search by name, description, category, or props |

## Lookup Flow

1. **Find the component** — call `search_components` with a keyword, or `list_all_components` to browse
2. **Filter by category** — call `list_all_components` with `category` (e.g. `"Forms"`, `"Actions"`, `"Navigation"`)
3. **Get full docs** — call `get_component` with the component name (e.g. `"Button"`, `"TextField"`)

## Categories (8)

| Category | Count | Examples |
|----------|-------|---------|
| Actions | 13 | Button, ActionButton, ToggleButton, MenuTrigger |
| Forms | 32 | TextField, NumberField, DatePicker, ComboBox, Checkbox |
| Collections | 7 | TableView, ListView, TagGroup, CardView |
| Overlays | 10 | Dialog, Popover, Tooltip, ContextualHelp |
| Content | 8 | Avatar, Badge, Heading, Text, Illustration |
| Status | 10 | ProgressBar, Meter, StatusLight, InlineAlert |
| Navigation | 4 | Tabs, Breadcrumbs, Link, StepList |
| Layout | 6 | Flex, Grid, Divider, Disclosure |

## React Spectrum vs React Aria

- **React Spectrum (S2)** = Adobe's themed design system components (this skill)
- **React Aria** = headless, unstyled accessibility primitives (see `react-aria` skill)
- Use this skill when the user wants styled, ready-to-use Adobe design system components
- Use `react-aria` when building custom components with accessibility hooks

## When to Use

- Building UI with Adobe's Spectrum 2 design system
- Checking available S2 component props and variants
- Searching for the right component for a UI pattern
- Migrating from Spectrum 1 (v3) to Spectrum 2
- Understanding S2 styling, theming, or layout patterns
