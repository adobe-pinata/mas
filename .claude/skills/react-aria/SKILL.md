---
name: react-aria
description: Look up React Aria component documentation — props, examples, usage patterns, and accessibility guidance. Use when building or modifying UI components with React Aria.
---

# react-aria

React Aria component documentation via MCP.

**MCP server:** `react-aria` (must be running — registered in `mcp/.mcp.react-aria.json`)

## Tools

| Tool | Input | Returns |
|------|-------|---------|
| `mcp__react-aria__list_react_aria_pages` | `includeDescription?: boolean` | All available doc pages |
| `mcp__react-aria__get_react_aria_page_info` | `page_name: string` | Page description + section list |
| `mcp__react-aria__get_react_aria_page` | `page_name: string, section_name?: string` | Full markdown or a single section |

## Lookup Flow

1. **Find the component** — call `list_react_aria_pages` with `includeDescription: true` to browse, or go direct if you know the name
2. **Check sections** — call `get_react_aria_page_info` with the page name (e.g. `"Button"`) to see available sections
3. **Get what you need** — call `get_react_aria_page` with the page name and optionally a section (e.g. `section_name: "Props"`)

## Page Names

Page names match the component name exactly: `Button`, `ComboBox`, `DatePicker`, `Menu`, `Table`, etc.

Non-component pages use path format: `collections`, `styling`, `forms`, `internationalized/date/CalendarDate`.

## Common Sections

Most component pages have: Props, Usage, Examples, Styling, Accessibility.

Use `section_name` to fetch only what you need — full pages can be large.

## When to Use

- Building a new UI component — look up the right React Aria primitive
- Checking prop types and allowed values
- Finding accessibility patterns (ARIA roles, keyboard nav)
- Getting usage examples for composition patterns
- Understanding styling hooks (`className`, `style`, render props)
