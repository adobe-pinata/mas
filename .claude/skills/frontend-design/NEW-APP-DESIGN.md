# New App: Design Stance Selection

Use this workflow when building a new application or standalone page from scratch with Adobe Spectrum S2. No existing patterns to match — full design freedom within Spectrum's vocabulary.

**The trap to avoid:** Using every S2 component at its default size/variant/color. That reads as undesigned. Make explicit choices.

---

## Step 1: Understand the Context

Before any design decisions:

- **What problem does this UI solve?**
- **Who are the users?** (developers, content authors, business users, consumers)
- **What's the primary interaction pattern?** (data browsing, form filling, monitoring, content creation)
- **What density of information?** (sparse, moderate, high)
- **What's the emotional tone?** (efficient, friendly, serious, playful)
- **What's the ONE memorable thing?** Every app needs a signature element — the single design decision that gives it identity. A bold `StatusLight` dashboard grid. An editorial `Heading` hierarchy with `XXL`/`XS` contrast. An unexpected use of `Meter` as a visual rhythm element. A `TagGroup` that defines the entire interaction model. Name it before you start building.

---

## Anti-Convergence Rule

Don't reuse the same S2 component composition across different apps. Each app should feel like it made its own choices within Spectrum. If the last app you built was a compact dashboard with `TableView` + `StatusLight`, don't default to that pattern again — explore `ListView`, `CardView`, `Grid` layouts, or editorial approaches instead.

---

## Step 2: Choose a Design Stance

Pick ONE and commit. Each maps to specific Spectrum configuration:

### Clean & Minimal
**Best for:** Productivity tools, settings pages, utilities
- Theme: `default`
- Component sizes: `size="M"` (default)
- Color scheme: light (dark as secondary)
- Typography: `Heading size="M"` for page titles, `Text` for body copy, generous whitespace
- Layout: Simple `Flex direction="column"` with `size-300`+ gaps
- Color: Muted — lean on `neutral`, `informative`. Minimal use of `positive`/`negative`
- Components: Prefer understated variants — `Button variant="secondary"`, subtle `Divider`s

### Expressive & Vibrant
**Best for:** Consumer-facing, marketing, onboarding flows
- Theme: `express` (intentionally different from default)
- Component sizes: `size="L"` or `"XL"` on components
- Typography: `Heading size="XL"` or `"XXL"` for hero text, `Text` for body copy
- Layout: Asymmetric `Grid` layouts, large `View` sections with background colors
- Color: Bold semantic colors — `accent` buttons, `informative` badges, layered backgrounds
- Components: `IllustratedMessage` for empty states, large `ActionButton`s, `Avatar`

### Information-Dense & Structured
**Best for:** Dashboards, admin panels, monitoring tools, data tables
- Theme: `default`
- Component sizes: `size="S"` across all components for maximum density
- Typography: `Heading size="S"` for sections, `Text` for content, uppercase `style()` macro text for metadata labels
- Layout: `Grid` with tight `size-100` gaps, `View` panels with `gray-75`/`gray-100` layering
- Color: Semantic status colors are load-bearing — `positive`/`negative`/`notice` for real meaning
- Components: `TableView`, `ListView`, `Meter`, `StatusLight`, `Badge`, `TagGroup` for filters

### Editorial & Spatial
**Best for:** Story-focused UIs, documentation, narrative onboarding, content-rich pages
- Theme: `default`
- Component sizes: `size="M"` or `"L"` for spacious feel
- Typography: Mixed `Heading` scales — `"XXL"` for page titles, `"S"` for section labels. `Text` for body copy. Uppercase `style()` macro text for captions
- Layout: Asymmetric `Flex`/`Grid`, large negative space zones via `View` with generous padding
- Color: Restrained palette — mostly `neutral` and `gray-*` backgrounds, single accent color for CTAs
- Components: `IllustratedMessage`, `Breadcrumbs` for navigation, `Divider` for rhythm

---

## Step 3: Configure the Provider

Based on your stance, set up the root Provider:

```jsx
import { Provider } from '@react-spectrum/s2';
import '@react-spectrum/s2/page.css';

<Provider
  colorScheme="light"        // "light" | "dark" | undefined (follows OS)
  background="base"          // "base" | "layer-1" | "layer-2" | undefined
  locale="en-US"
>
  {children}
</Provider>
```

**S2 Provider props:** `colorScheme`, `background`, `locale`, `router`, `styles`, `elementType`. There is **no** `density`, `scale`, or `theme` prop — control density via per-component `size` props, applied consistently across the page.

**Set Provider ONCE at the root.** Control visual density by choosing a consistent `size` across components (e.g., all `size="S"` for compact feel, all `size="M"` for regular).

---

## Step 4: Select Components

For each UI need, find the right S2 component. Use MCP tools to verify props and imports.

### Decision shortcuts

| Need | Component | Not this |
|------|-----------|----------|
| Page title | `<Heading size="XL">` | `<h1>` |
| Body text | `<Text>` | `<p>` |
| Metadata label | `style()` macro with uppercase | `<span className="label">` |
| Button | `<Button variant="...">` | `<button>` |
| Text input | `<TextField>` | `<input>` |
| Select | `<Picker>` | `<select>` |
| Checkbox | `<Checkbox>` | `<input type="checkbox">` |
| Toggle | `<Switch>` | custom toggle |
| Toolbar | `<ActionGroup>` | row of `<Button>` |
| Filter tags | `<TagGroup>` | custom chips |
| Status dot | `<StatusLight>` | colored `<span>` |
| Empty state | `<IllustratedMessage>` | blank div |
| Loading | `<ProgressCircle>` or `<ProgressBar>` | custom spinner |
| Notification | `<ToastQueue>` | `alert()` |
| Layout zone | `<View padding="size-200">` | `<div style={{padding: 12}}>` |
| Flex container | `<Flex gap="size-200">` | `<div style={{display: 'flex'}}>` |

### Variant choices

Don't default. Choose semantically:

- **Button**: `primary` (main action), `secondary` (supporting), `accent` (call-to-action), `negative` (destructive)
- **Badge**: `informative` (info), `positive` (success), `negative` (error), `notice` (warning), `neutral` (default)
- **AlertDialog**: `information`, `warning`, `error`, `confirmation` — match the message severity

---

## Match Complexity to Vision

Implementation depth should match the design stance:

- **Information-dense** apps need more components, tighter layout code, multiple `View` panels with layered backgrounds, `StatusLight`/`Badge`/`Meter` throughout — the code is inherently more elaborate because the UI demands it.
- **Clean & minimal** apps need restraint — fewer components, precise spacing, careful typography sizing. The code is simpler but the token choices matter more. Every `size-*` value is load-bearing.
- **Expressive** apps need bold choices — `XXL` headings, `accent` buttons, express theme, large scale. Lean into Spectrum's personality.
- **Editorial** apps need spatial control — asymmetric `Grid` areas, mixed `Heading` scales, generous `View` padding. Layout is the design.

Don't write the same amount of code for every stance. A minimal settings page and a dense monitoring dashboard should look fundamentally different in both UI and codebase.

---

## Step 5: Self-Check Before Returning

- [ ] Design stance is stated and consistent throughout
- [ ] Signature element identified — the ONE memorable design choice
- [ ] Provider is configured with explicit theme/density/colorScheme
- [ ] No raw HTML where S2 equivalents exist
- [ ] No `style={{ }}` where token props work
- [ ] No default-everything — explicit size/variant/color choices documented
- [ ] No hex colors — semantic tokens only
- [ ] No mixed Spectrum 1 / S2 imports
- [ ] Import paths verified via MCP tools
- [ ] Implementation depth matches the stance (not same boilerplate for every app)

---

**The goal: an app that looks intentionally designed, not just "has Spectrum components in it."**
