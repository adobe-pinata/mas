---
name: frontend-design
description: Produce intentional, characterful Adobe Spectrum S2 UIs — not generic default-everything Spectrum. Activates on frontend design work using React Spectrum or Adobe design system components.
---

# frontend-design

Design philosophy and practical guidance for building bold, distinctive UIs with Adobe Spectrum 2 (S2).

## Design Direction in Spectrum

Choose a clear aesthetic stance *within* Spectrum's vocabulary:

- **Clean & minimal**: tight density, muted semantic colors, generous whitespace. Ideal for productivity tools.
- **Expressive & vibrant**: Express theme, large-size scale, bold Heading weights. Use for consumer-facing / marketing contexts.
- **Information-dense & structured**: Table/ListView/Grid-heavy, small density, monospace Detail text. Best for dashboards and data-heavy UIs.
- **Editorial & spatial**: mixed Heading scales, asymmetric Flex layouts, large illustrative elements. For story-focused or narrative UIs.

**Express theme** (`colorScheme="light"` with `theme={expressTheme}`) is qualitatively different from the default — use it intentionally for consumer-facing contexts; default theme for productivity / tool UIs.

**Density** should be picked once and applied consistently at the Provider level (`density="compact"` | `"regular"` | `"spacious"`) rather than per-component. This creates cohesion across the entire UI.

## Typography in Spectrum

Use Spectrum's typography hierarchy intentionally:

- **`<Heading>` levels** (`size="S"` through `"XXL"`): Choose size purposefully — don't default to H2 for everything. Pair a large display Heading (`size="XXL"` or `"XL"`) with `<Body size="S">` detail text for visual contrast.
- **`<Body>`**: Body copy with configurable size. Use `size="S"` for secondary text, `size="M"` for primary.
- **`<Text>`**: Inline copy within paragraphs — more economical than wrapping in div + styles.
- **`<Content>`**: Body content inside Card/Dialog/Popover — respects density settings automatically.
- **`<Detail>`** (uppercase label-style text): Creates hierarchy without a heading — use it for section labels, metadata rows, and table headers.

**Avoid** rendering raw `<h1>`–`<p>` tags when Spectrum typography components cover the case. The Spectrum components integrate with theme tokens and density settings.

## Layout Composition

Build structure with Spectrum layout primitives:

- **`<Flex>`** and **`<Grid>`**: Use for all structural layout instead of raw `<div style="display:flex">`. Flex handles alignment, spacing, direction. Grid handles area-based layouts.
- **`<View>`**: Create visual zones with `backgroundColor`, `borderColor`, `padding`, `borderRadius` token props (e.g., `padding="size-150"`, `borderRadius="medium"`). Avoids custom CSS.
- **`<Flex wrap>` with gap tokens**: For responsive card grids, use `<Flex wrap gap="size-200">` instead of fixed CSS grids. Wraps naturally on mobile.
- **`<Divider>` + `<Flex direction="column">`**: Create clean visual rhythm in lists and panels without custom CSS borders.
- **`<Grid areas>`** with named template areas: Can create editorial layouts that feel designed, not default. Use when you need precise control.
- **Size tokens over pixels**: Never use `style={{ padding: "12px" }}`. Use `padding="size-150"` on `<View>` or `<Flex>`. This ensures consistency with theme scaling.

## Component Selection Philosophy

Prefer S2 styled components first; drop to React Aria headless only when you need bespoke visual control:

- **`<ActionGroup>`**: Use for multi-action toolbars instead of a row of `<Button>` components. Handles spacing and orientation.
- **`<TagGroup>`**: For filterable facet UIs; don't build custom tag chips.
- **`<Meter>` and `<ProgressBar>`**: Underused visual interest elements — add them to dashboards beyond just "loading" states. `<Meter>` shows proportional fill; `<ProgressBar>` shows progress over time.
- **`<StatusLight>`**: Creates ambient status awareness (online, busy, warning) without taking up layout space.
- **`<IllustratedMessage>`**: Transforms empty states from a blank div into a designed moment — always use it for zero-data screens.
- **Component variants**: When a component has a `variant` prop:
  - `Button`: `primary|secondary|negative|accent` — choose semantically
  - `Badge`: `informative|positive|negative|notice|neutral` — match the semantic meaning
  - `Alert`: `information|success|warning|error` — align with the message tone
  - Avoid defaulting to `primary`; let the semantic intent drive the choice.
- **Look up components** via the `react-spectrum-s2` skill before writing custom implementations. Get the exact props, examples, and categories.

## Color and Visual Atmosphere

Build a cohesive visual language with Spectrum's color system:

- **Semantic color tokens**: `positive`, `negative`, `notice`, `informative`, `neutral` — use them consistently to build visual language, not decoration. Every use of color should serve semantic meaning.
- **Dark mode as a first-class design choice**: Design for both `colorScheme="light"` and `colorScheme="dark"` from the start. Don't retrofit dark mode.
- **Layering tokens**: `<View backgroundColor="gray-100">` vs `<View backgroundColor="gray-50">` creates subtle depth in sidebars and panels — use intentionally.
- **No hardcoded hex colors**: Every color must map to a Spectrum token. If the semantic token system doesn't have what you need, reconsider the design direction — a custom hex color is a sign the design is straying from Spectrum.
- **Icon + label pairs**: Use `<Icon>` (from `@spectrum-icons/workflow`) with labels at consistent sizes (`size="S"` / `"M"`) per density level. Icons add visual anchors and reduce cognitive load.

## Motion and Interaction

Spectrum components have built-in motion — lean into it:

- **Dialog, Toast, Tooltip motion**: Spectrum components animate on open/close/show automatically. Don't add competing CSS transitions.
- **Page-level transitions**: Coordinate route changes with Spectrum's timing. Use `@spectrum-css/vars` motion tokens if custom animation is needed.
- **Progress communication**: Use `<ProgressCircle isIndeterminate>` and `<ProgressBar>` to communicate async work — prefer these over custom spinners.
- **Transient feedback**: Use `<ToastQueue>` for notifications. Never use `alert()` or raw DOM modals.
- **Keyboard accessibility**: Don't override Spectrum's focus ring or keyboard navigation — it's part of the design language, not a technical detail.

## What to Avoid

Patterns that lead to generic, undesigned UIs:

- **Default everything**: Using every component at its default size, variant, and color reads as undesigned. Make explicit choices.
- **Raw HTML tags**: Don't use raw `<div>`, `<button>`, `<input>`, `<select>` when a Spectrum equivalent exists.
- **Mixed Spectrum versions**: Don't mix Spectrum 1 (`@adobe/react-spectrum`) and S2 (`@react-spectrum/s2`) imports in the same component tree.
- **Overriding Spectrum CSS**: Don't override Spectrum's CSS custom properties globally — it breaks theming contracts and defeats the purpose of a design system.
- **Missing accessibility labels**: Don't ignore `aria-label` on icon-only buttons. Spectrum's accessibility is part of the design.
- **Inventing custom colors**: If the semantic token system doesn't have what you need, reconsider the design direction instead of adding a custom color variable.

## Integration Points

Before and after building UI:

- **Before writing**: Look up the S2 component via MCP tools (`react-spectrum-s2` skill) or the `adobe-spectrum` agent to confirm the correct import path and required props.
- **After implementing**: Run `/spectrum-check` to catch raw HTML/CSS that should be Spectrum.
- **New applications**: Use `/scaffold` to set up boilerplate structure and wire up the S2 Provider and theme.

## References

- **`react-spectrum-s2` skill**: Look up S2 component docs, props, examples, and categories.
- **`react-aria` skill**: Reference for headless accessibility primitives when building custom components.
- **`adobe-spectrum` agent**: Verify import paths and required props for S2 components.
- **`/spectrum-check` command**: Audit for Spectrum adoption opportunities in changed files.
- **`/scaffold` command**: Set up new S2-based applications with Provider, theme, and boilerplate.
