# Spectrum S2 Reference

Deep-dive reference for Adobe Spectrum S2's design token system, theming, and component primitives.

---

## Table of Contents

1. [Size Tokens](#size-tokens)
2. [Density](#density)
3. [Themes](#themes)
4. [Color Tokens](#color-tokens)
5. [Typography Components](#typography-components)
6. [Layout Primitives](#layout-primitives)
7. [Component Categories](#component-categories)
8. [Icon System](#icon-system)
9. [Accessibility Essentials](#accessibility-essentials)

---

## Size Tokens

Spectrum uses a consistent size token scale instead of pixel values. Use these for all spacing, padding, and gap props.

| Token | Approx. Value | Common Use |
|-------|--------------|------------|
| `size-0` | 0px | No spacing |
| `size-10` | 1px | Borders |
| `size-25` | 2px | Minimal gap |
| `size-50` | 4px | Tight inline spacing |
| `size-75` | 6px | Compact element padding |
| `size-100` | 8px | Default inline spacing |
| `size-125` | 10px | Between related items |
| `size-150` | 12px | Card padding (compact) |
| `size-200` | 16px | Standard card padding, form gaps |
| `size-250` | 20px | Section padding |
| `size-300` | 24px | Between sections |
| `size-400` | 32px | Large section margins |
| `size-500` | 40px | Page-level padding |
| `size-600` | 48px | Hero spacing |
| `size-700` | 56px | Large hero spacing |
| `size-800` | 64px | Maximum spacing |

**Rule:** Never use `style={{ padding: '12px' }}`. Use `padding="size-150"` on `View` or `Flex`.

---

## Density

S2's `Provider` does **not** have a `density` prop. Density is controlled per-component via the `size` prop.

| Desired Feel | How to Achieve | Character |
|---------|----------|-----------|
| Compact | `size="S"` on components + tight spacing tokens (`gap="size-100"`) | Maximum info density |
| Regular | `size="M"` (default) + standard spacing (`gap="size-200"`) | Balanced readability |
| Spacious | `size="L"` or `"XL"` + generous spacing (`gap="size-300"+`) | Relaxed, editorial feel |

```jsx
// No density prop on Provider — use size on individual components:
<TextField size="S" label="Name" />
<Button size="S" variant="accent">Save</Button>
<Picker size="S" label="Region">{...}</Picker>
```

**Be consistent** — pick a size level and apply it across all components on the page. Mixing `size="S"` and `size="L"` on the same page creates visual inconsistency.

---

## Themes

### Default Theme
- Neutral, professional palette
- Suitable for productivity tools, admin UIs, internal apps
- Gray-based backgrounds with blue accents

### Express Theme
- Vibrant, consumer-facing palette
- Bolder colors, more expressive personality
- Suitable for marketing, onboarding, creative tools

```jsx
import { Provider } from '@react-spectrum/s2';

// Productivity app
<Provider theme={defaultTheme} colorScheme="light">

// Consumer app
<Provider theme={expressTheme} colorScheme="light">
```

### Color Scheme

| Value | Behavior |
|-------|----------|
| `"light"` | Light mode only |
| `"dark"` | Dark mode only |
| `"auto"` | Follows system preference |

**Design for both.** Don't retrofit dark mode — consider it from the start.

---

## Color Tokens

### Semantic Colors

Use semantic tokens for all color decisions. These adapt automatically to light/dark mode.

| Token | Meaning | Use For |
|-------|---------|---------|
| `positive` | Success, healthy, go | Status lights, success badges, confirmation |
| `negative` | Error, danger, destructive | Error states, delete actions, alerts |
| `notice` | Warning, caution | Warnings, approaching limits, attention needed |
| `informative` | Info, neutral highlight | Info badges, tips, secondary highlights |
| `neutral` | Default, no semantic weight | Inactive states, disabled, de-emphasized |

### Background Layering

Create depth with gray background tokens on `View`:

| Token | Use |
|-------|-----|
| `gray-50` | Page background (lightest) |
| `gray-75` | Card/panel background |
| `gray-100` | Sidebar, secondary panels |
| `gray-200` | Active/selected panel background |

```jsx
<View backgroundColor="gray-50">           {/* Page */}
  <View backgroundColor="gray-100">         {/* Sidebar */}
  <View backgroundColor="gray-75">          {/* Content card */}
```

### Border Colors

| Token | Use |
|-------|-----|
| `gray-200` | Subtle dividers |
| `gray-300` | Card borders |
| `gray-400` | Input borders |

**No hex colors.** If the semantic system doesn't have what you need, reconsider the design.

---

## Typography Components

### Heading

Page and section titles. Choose size intentionally.

| Size | Use |
|------|-----|
| `XXL` | Hero/page titles (editorial, express) |
| `XL` | Page titles (standard) |
| `L` | Section titles |
| `M` | Card titles, sub-sections |
| `S` | Small section titles, compact UI |
| `XS` | Minimal headings |

```jsx
import { Heading } from '@react-spectrum/s2';

<Heading size="XL">Dashboard</Heading>
<Heading size="S">Recent Activity</Heading>
```

### Text

General-purpose text component. Use for body copy, inline text, and secondary content. In S2, `Text` replaces what was `Body` and `Detail` in older Spectrum versions.

```jsx
import { Text } from '@react-spectrum/s2';

<Text>Primary body text</Text>
```

For label-style uppercase text (metadata, section headers), use the `style` macro:

```jsx
<span className={style({ color: 'gray-700' })} style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
  LAST UPDATED
</span>
```

### Content

Body content inside Card, Dialog, Popover. Respects container context automatically.

**Note:** `Body` and `Detail` are **not exported** from `@react-spectrum/s2`. Use `Text` for inline/body copy. Use `Heading` for titles. Use `Content` inside container components.

---

## Layout Primitives

### Flex

Primary 1D layout component. Replaces `<div style={{display:'flex'}}>`.

Key props:
- `direction`: `"row"` (default) | `"column"`
- `gap`: size token (e.g., `"size-200"`)
- `wrap`: boolean
- `justifyContent`: `"start"` | `"center"` | `"end"` | `"space-between"`
- `alignItems`: `"start"` | `"center"` | `"end"` | `"stretch"`

```jsx
<Flex direction="column" gap="size-200">
  <Flex justifyContent="space-between" alignItems="center">
    <Heading size="M">Title</Heading>
    <Button variant="primary">Action</Button>
  </Flex>
  <Text>Content here</Text>
</Flex>
```

### Grid

2D layout. Use for complex page structures and card grids.

Key props:
- `columns`: column template (e.g., `"1fr 1fr 1fr"`, `repeat(3, 1fr)`)
- `rows`: row template
- `areas`: named grid areas
- `gap`: size token
- `columnGap`, `rowGap`: separate gap control

### View

Visual zone with token-based styling. Replaces styled `<div>`.

Key props:
- `backgroundColor`: color token
- `padding`, `paddingX`, `paddingY`, `paddingStart`, `paddingEnd`: size tokens
- `borderRadius`: `"small"` | `"medium"` | `"large"` | `"xsmall"`
- `borderWidth`: `"thin"` | `"thick"` | `"thicker"` | `"thickest"`
- `borderColor`: color token
- `overflow`: `"hidden"` | `"auto"`

```jsx
<View
  backgroundColor="gray-75"
  padding="size-200"
  borderRadius="medium"
  borderWidth="thin"
  borderColor="gray-200"
>
  {children}
</View>
```

### Divider

Visual separator. Use with `Flex direction="column"` for rhythm.

```jsx
<Flex direction="column" gap="size-200">
  <Section1 />
  <Divider />
  <Section2 />
</Flex>
```

---

## Component Categories

Quick reference for finding the right component.

### Actions (13)
Button, ActionButton, ActionGroup, ToggleButton, ActionMenu, MenuTrigger, SubmenuTrigger, ActionBarContainer, ActionBar

### Forms (32)
TextField, TextArea, NumberField, SearchField, Picker, ComboBox, Checkbox, CheckboxGroup, RadioGroup, Radio, Switch, Slider, RangeSlider, DatePicker, DateRangePicker, TimeField, ColorField, ColorSlider, ColorArea, ColorWheel, FileTrigger, DropZone, Form

### Collections (7)
TableView, ListView, GridList, TagGroup, ListBox, TreeView

### Overlays (10)
Dialog, DialogTrigger, AlertDialog, Popover, Tooltip, TooltipTrigger, ContextualHelp, Modal

### Content (8)
Avatar, Badge, Card, IllustratedMessage, Image, Heading, Text, Content

### Status (10)
ProgressBar, ProgressCircle, Meter, StatusLight, InlineAlert, ToastQueue, Banner

### Navigation (4)
TabList, Tab, TabPanel, Tabs, Breadcrumbs, Link

### Layout (6)
Flex, Grid, View, Divider

---

## Icon System

Icons come from `@spectrum-icons/workflow` (400+ icons) and `@spectrum-icons/illustrations` (for empty states).

```jsx
import Edit from '@spectrum-icons/workflow/Edit';
import Delete from '@spectrum-icons/workflow/Delete';
import NoSearchResults from '@spectrum-icons/illustrations/NoSearchResults';

<Button variant="primary"><Edit /><Text>Edit</Text></Button>
<IllustratedMessage><NoSearchResults /></IllustratedMessage>
```

**Size icons consistently** with the density level. Use `size="S"` in compact, `size="M"` in regular.

---

## Accessibility Essentials

Spectrum S2 handles most accessibility automatically. Don't break it:

- **Never remove focus rings** — Spectrum's focus management is part of the design language
- **Always add `aria-label`** to icon-only buttons: `<ActionButton aria-label="Delete"><Delete /></ActionButton>`
- **Use Spectrum's keyboard navigation** — don't add custom `onKeyDown` handlers that conflict
- **Let components manage ARIA roles** — don't add `role="button"` to a `<Button>`
- **Use `isDisabled` prop** instead of CSS opacity hacks
- **Use `isRequired` prop** on form fields instead of manual asterisks

---

**See also:**
- [SKILL.md](SKILL.md) — Scenario router
- [EXISTING-APP-CHECKLIST.md](EXISTING-APP-CHECKLIST.md) — Consistency workflow
- [NEW-APP-DESIGN.md](NEW-APP-DESIGN.md) — Design stance selection
- [EXAMPLES.md](EXAMPLES.md) — Before/after case studies
