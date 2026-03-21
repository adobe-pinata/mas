# Spectrum S2 Design Examples

Real-world before/after examples demonstrating correct Spectrum S2 usage.

---

## Case Study: Dashboard Status Panel

### Context
Adding a status overview panel to an existing dashboard app using compact density.

### Wrong: Raw HTML with Custom Styles

```jsx
function StatusPanel({ services }) {
  return (
    <div style={{ padding: '16px', background: '#f5f5f5', borderRadius: '8px' }}>
      <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Service Status</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {services.map(s => (
          <div key={s.name} style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>{s.name}</span>
            <span style={{ color: s.healthy ? 'green' : 'red' }}>
              {s.healthy ? '● Online' : '● Offline'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Problems:**
- Raw `<div>`, `<h3>`, `<span>` instead of Spectrum components
- Hardcoded pixel values instead of size tokens
- Hardcoded hex colors instead of semantic tokens
- Custom status indicator instead of `StatusLight`
- No density awareness

### Right: Spectrum S2 Components

```jsx
import { View, Flex, Heading, Text, StatusLight } from '@react-spectrum/s2';

function StatusPanel({ services }) {
  return (
    <View
      backgroundColor="gray-75"
      padding="size-200"
      borderRadius="medium"
    >
      <Flex direction="column" gap="size-150">
        <Heading size="S">Service Status</Heading>
        {services.map(s => (
          <Flex key={s.name} justifyContent="space-between" alignItems="center">
            <Text>{s.name}</Text>
            <StatusLight variant={s.healthy ? 'positive' : 'negative'}>
              {s.healthy ? 'Online' : 'Offline'}
            </StatusLight>
          </Flex>
        ))}
      </Flex>
    </View>
  );
}
```

**Why this works:**
- `View` with token props replaces styled div
- `Heading size="S"` matches compact dashboard hierarchy
- `StatusLight` is purpose-built for this exact use case
- `positive`/`negative` variants carry semantic meaning
- Spacing uses size tokens, respects density

---

## Case Study: Action Toolbar

### Wrong: Row of Buttons

```jsx
<div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
  <Button>Edit</Button>
  <Button>Duplicate</Button>
  <Button>Delete</Button>
</div>
```

### Right: ActionGroup

```jsx
import { ActionGroup, Item } from '@react-spectrum/s2';
import Edit from '@spectrum-icons/workflow/Edit';
import Duplicate from '@spectrum-icons/workflow/Copy';
import Delete from '@spectrum-icons/workflow/Delete';

<ActionGroup onAction={handleAction}>
  <Item key="edit"><Edit /><Text>Edit</Text></Item>
  <Item key="duplicate"><Duplicate /><Text>Duplicate</Text></Item>
  <Item key="delete"><Delete /><Text>Delete</Text></Item>
</ActionGroup>
```

**Why:** `ActionGroup` handles spacing, overflow, keyboard navigation, and density automatically. A row of `Button`s does none of this.

---

## Case Study: Empty State

### Wrong: Blank Div with Text

```jsx
{items.length === 0 && (
  <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
    <p>No items found</p>
    <button onClick={onRefresh}>Refresh</button>
  </div>
)}
```

### Right: IllustratedMessage

```jsx
import { IllustratedMessage, Heading, Content, Button } from '@react-spectrum/s2';
import NoSearchResults from '@spectrum-icons/illustrations/NoSearchResults';

{items.length === 0 && (
  <IllustratedMessage>
    <NoSearchResults />
    <Heading>No items found</Heading>
    <Content>Try adjusting your filters or check back later.</Content>
    <Button variant="secondary" onPress={onRefresh}>Refresh</Button>
  </IllustratedMessage>
)}
```

**Why:** `IllustratedMessage` turns an empty state into a designed moment. The illustration adds visual interest, the structure is accessible, and it integrates with the theme.

---

## Case Study: Filter Bar

### Wrong: Custom Tag Chips

```jsx
<div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
  {filters.map(f => (
    <span
      key={f}
      onClick={() => removeFilter(f)}
      style={{
        background: '#e0e0e0',
        borderRadius: '16px',
        padding: '4px 12px',
        fontSize: '12px',
        cursor: 'pointer'
      }}
    >
      {f} ×
    </span>
  ))}
</div>
```

### Right: TagGroup

```jsx
import { TagGroup, Item } from '@react-spectrum/s2';

<TagGroup
  items={filters.map(f => ({ id: f, name: f }))}
  onRemove={keys => keys.forEach(removeFilter)}
  aria-label="Active filters"
>
  {item => <Item key={item.id}>{item.name}</Item>}
</TagGroup>
```

**Why:** `TagGroup` handles removal, keyboard navigation, overflow, and accessibility. Custom chips miss all of this.

---

## Case Study: Notification

### Wrong: alert() or Custom Modal

```jsx
// After save:
alert('Changes saved successfully!');

// Or worse, a custom toast:
<div className="custom-toast" style={{ position: 'fixed', bottom: 20, ... }}>
  Saved!
</div>
```

### Right: ToastQueue

```jsx
import { ToastQueue } from '@react-spectrum/s2';

// Create queue once:
const toast = new ToastQueue();

// After save:
toast.positive('Changes saved successfully', { timeout: 5000 });

// For errors:
toast.negative('Failed to save changes', { timeout: 5000 });
```

**Why:** ToastQueue handles positioning, stacking, dismissal, timeouts, and screen reader announcements. Custom toasts miss accessibility.

---

## Case Study: Form Layout Consistency

### Context
Existing settings page uses `Flex direction="column" gap="size-200"` for form fields. Adding a new section.

### Wrong: Different Spacing

```jsx
// New section with different spacing pattern
<div style={{ display: 'grid', gap: '24px', marginTop: '32px' }}>
  <TextField label="API Key" />
  <Picker label="Region">{...}</Picker>
</div>
```

### Right: Match Existing Pattern

```jsx
// Matches existing form sections exactly
<Flex direction="column" gap="size-200" marginTop="size-300">
  <Heading size="S">API Configuration</Heading>
  <TextField label="API Key" />
  <Picker label="Region">{...}</Picker>
</Flex>
```

**Why:** Consistency. The existing page uses `Flex` with `size-200` gaps. Introducing `Grid` with `24px` gaps creates visual inconsistency even if functionally equivalent.

---

## Case Study: Loading State

### Wrong: Custom Spinner

```jsx
{loading && (
  <div style={{ textAlign: 'center', padding: '20px' }}>
    <div className="spinner" /> {/* CSS animation */}
    <p>Loading...</p>
  </div>
)}
```

### Right: ProgressCircle

```jsx
import { Flex, ProgressCircle, Text } from '@react-spectrum/s2';

{loading && (
  <Flex direction="column" alignItems="center" gap="size-150">
    <ProgressCircle isIndeterminate aria-label="Loading" />
    <Text>Loading...</Text>
  </Flex>
)}
```

**Why:** `ProgressCircle` integrates with Spectrum's motion system and is accessible. Custom spinners don't. Note: `Body` is not exported from S2 — use `Text` instead.

---

## Anti-Pattern: Default Everything

### The Problem

```jsx
<Button>Save</Button>
<Button>Cancel</Button>
<Button>Delete</Button>
```

All three buttons look identical. No visual hierarchy. No semantic meaning.

### The Fix

```jsx
<Flex gap="size-100">
  <Button variant="accent">Save</Button>
  <Button variant="secondary">Cancel</Button>
  <Button variant="negative">Delete</Button>
</Flex>
```

**Rule:** If you have multiple actions, they MUST have different variants reflecting their semantic weight.

---

**See also:**
- [SKILL.md](SKILL.md) — Scenario router
- [EXISTING-APP-CHECKLIST.md](EXISTING-APP-CHECKLIST.md) — Consistency workflow
- [NEW-APP-DESIGN.md](NEW-APP-DESIGN.md) — Design stance selection
- [REFERENCE.md](REFERENCE.md) — Token system deep-dive
