# Increase Plans Page Header Height

**ADW ID:** 8
**Date:** 2026-03-25
**Specification:** specs/issue-7529f35b-adw-8-sdlc_planner-increase-plans-page-header-height.md

## Overview

Increases the height of the `merch-card-collection-header` component on plans pages by approximately 50%, from the default 44px to 66px. This applies to both the standard plans variant and the plans-v2 variant, improving visual prominence and touch target size for the filter and search controls.

## What Was Built

- CSS custom property overrides in `plans.css.js` raising the filter button and search input height to 66px
- Matching overrides in `plans-v2.css.js` for consistent behavior across both plans variants
- No JavaScript changes required — implementation is purely CSS variable overrides

## Technical Implementation

### Files Modified

- `web-components/src/variants/plans.css.js`: Added `--merch-card-collection-header-filter-height: 66px` and `--merch-card-collection-header-search-min-height: 66px` to the `merch-card-collection-header.plans` rule
- `web-components/src/variants/plans-v2.css.js`: Same two overrides added to the matching `merch-card-collection-header.plans` rule

### Key Changes

- Both overrides target the `merch-card-collection-header.plans` CSS rule in each variant file
- The default values (44px) are defined in `merch-card-collection.js` via CSS custom properties; these overrides scope the change to plans pages only
- Child elements (search input, filter button, result count) remain vertically centered via the existing `align-items: center` on the `#header` grid — no alignment fixes were needed
- Change is scoped to plans pages only; no impact on other merch card collection variants

## How to Use

No user action required. The taller header renders automatically on any plans page that uses `merch-card-collection-header.plans`.

## Configuration

No configuration. The height is hardcoded at 66px via CSS custom properties.

## Testing

1. Open a plans page that renders `merch-card-collection-header`
2. Verify the header (filter/search area) appears visually taller than on non-plans pages
3. Confirm the search input and filter button are centered vertically within the header
4. Check at mobile, tablet, and desktop breakpoints for layout regressions

Syntax validation:
```
node --check web-components/src/variants/plans.css.js
node --check web-components/src/variants/plans-v2.css.js
```

## Notes

- The 66px target was derived from the spec (no exact height specified in the issue; ~50% increase from 44px was chosen)
- Both `plans.css.js` and `plans-v2.css.js` must be kept in sync for consistent behavior across plan card variants
