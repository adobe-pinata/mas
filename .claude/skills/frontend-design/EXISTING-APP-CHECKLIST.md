# Existing App: Design Consistency Checklist

Use this workflow when adding components, pages, or UI modifications to an app that already uses Adobe Spectrum S2.

**Rule: No code until Phase 1 and Phase 2 are complete.**

---

## Phase 1: Design Language Analysis

Scan 3–5 existing files that are closest to the work you're about to do. Document:

### Provider Configuration
- Color scheme: light, dark, or OS-following (undefined)?
- Background: `base`, `layer-1`, `layer-2`, or none?
- Locale?
- What `size` prop is used consistently across components? (`S`, `M`, `L`)

### Layout Patterns
- Primary layout primitives in use (`Flex`, `Grid`, `View`)?
- Container widths / max-width patterns?
- Spacing tokens used (e.g., `gap="size-200"`, `padding="size-150"`)?
- Sidebar/panel/main-area structure?

### Typography Hierarchy
- Which `Heading` sizes are used and where (page title, section title, card title)?
- `Text` usage — where and how is body copy rendered?
- Label-style text — is it done via `style()` macro with uppercase, or raw `<span>`?
- Any raw `<h1>`–`<p>` tags that should be Spectrum?

### Component Inventory
- Which S2 components are already in use?
- Common patterns: `ActionGroup` for toolbars? `TagGroup` for filters? `StatusLight` for status?
- Form patterns: which form components, what validation approach?
- Navigation: `TabList`, `Breadcrumbs`, `Link`?
- Feedback: `ToastQueue`, `AlertDialog`, `InlineAlert`?

### Color Token Usage
- Which semantic colors appear: `positive`, `negative`, `notice`, `informative`, `neutral`?
- Background layering: `gray-50` vs `gray-100` vs `gray-200`?
- Any custom CSS colors that break Spectrum conventions? (Flag these)

### Files Scanned
List the exact files you examined:
1. `path/to/file1` — why you chose it
2. `path/to/file2` — why you chose it
3. ...

---

## Phase 2: Design Decisions

Based on Phase 1, document explicit decisions before writing code:

### Pattern Application
- Which existing patterns apply directly to the new work?
- Which patterns need adaptation? Why?

### Component Strategy
For each new UI element needed:

| Element | Existing Component | Action | Rationale |
|---------|-------------------|--------|-----------|
| e.g., filter bar | `TagGroup` used on /dashboard | Reuse same pattern | Consistency with existing filters |
| e.g., empty state | None found | Introduce `IllustratedMessage` | S2 best practice for zero-data |

### Consistency Constraints
What MUST remain consistent:
- [ ] Same component `size` props as existing pages
- [ ] Same `Heading` size hierarchy
- [ ] Same spacing tokens
- [ ] Same color token semantics
- [ ] Same layout primitive patterns

What CAN vary (with justification):
- List anything that legitimately differs from existing patterns, with reason

---

## Phase 3: Implementation

Now write code. As you implement:

- [ ] Every layout uses `Flex`, `Grid`, or `View` — no raw `<div style={...}>`
- [ ] Every text element uses `Heading`, `Text`, or `Content` — no raw `<h1>`–`<p>` (note: `Body` and `Detail` are not S2 exports)
- [ ] Every interactive element uses S2 components — no raw `<button>`, `<input>`, `<select>`
- [ ] Spacing uses size tokens (`size-100`, `size-150`, etc.) — no pixel values
- [ ] Colors use semantic tokens — no hex values
- [ ] Component variants chosen semantically (`Button variant="primary"` vs `"secondary"` vs `"accent"`) — not defaulted
- [ ] Component `size` props are consistent across the page (S2 has no Provider-level density)
- [ ] Import paths are `@react-spectrum/s2` — no mixed Spectrum 1 imports

---

## Common Mistakes

- **Scanning too few files** — 1–2 files is not enough. You need 3–5 to see patterns.
- **Skipping Phase 2** — Jumping to code produces inconsistent UIs.
- **Introducing new tokens** — If existing pages use `size-200` for card gaps, don't use `size-300` without reason.
- **Creating custom components** when an S2 component exists — always check MCP tools first.
- **Mixing component sizes** — If the app uses `size="S"` throughout, don't add `size="L"` components.
- **Adding custom colors** — If the semantic system doesn't have what you need, reconsider the design, not the token system.

---

**When in doubt: match existing patterns. Consistency beats novelty.**
