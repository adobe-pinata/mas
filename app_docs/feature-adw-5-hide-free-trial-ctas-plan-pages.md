# Hide Free Trial CTAs on Plan Pages

**ADW ID:** adw-5
**Date:** 2026-03-25
**Specification:** specs/issue-bdf67753-adw-1d78f7d6-sdlc_planner-hide-free-trial-ctas-plan-pages.md

## Overview

Free Trial CTA buttons are filtered out of the footer on `plans`, `plans-education`, `plans-students`, and `plans-v2` merch card variants before DOM insertion. The filtering is applied in `processCTAs()` by checking each anchor's `data-analytics-id` against a known set of trial IDs, ensuring trial CTAs are never rendered — not hidden via CSS.

## What Was Built

- `FREE_TRIAL_CTA_IDS` constant — a `Set` of the five trial analytics IDs to filter (`free-trial`, `start-free-trial`, `seven-day-trial`, `fourteen-day-trial`, `thirty-day-trial`)
- `PLANS_VARIANTS` constant — a `Set` of the four plan variant names where filtering applies
- Filtering logic in `processCTAs()` — removes matching anchors before the `transformLinkToButton` map, so they are never appended to the DOM
- Unit tests covering all four plan variants, all five trial IDs, mixed CTA lists, and non-plan variant passthrough

## Technical Implementation

### Files Modified

- `web-components/src/hydrate.js`: Added `FREE_TRIAL_CTA_IDS` and `PLANS_VARIANTS` constants near the top; modified `processCTAs()` to filter trial CTAs when the variant is in `PLANS_VARIANTS`
- `web-components/test/hydrate.test.js`: Added 9 new test cases for the trial CTA filtering behavior

### Key Changes

- Two module-level `Set` constants define the filter criteria — no magic strings inside the function body
- `processCTAs` signature already accepted a `variant` parameter; the filter is a guard clause wrapping `ctas.filter()` before the existing `.map()` call
- The footer element is still created and appended even when all CTAs are filtered, preserving slot structure and avoiding empty-slot layout issues
- Non-plan variants (`ccd-slice`, etc.) are entirely unaffected — the filter branch is only entered when `PLANS_VARIANTS.has(variant)` is true
- No CSS `display:none` used — elements are removed before DOM insertion

## How to Use

This behavior is automatic. When a merch card with variant `plans`, `plans-education`, `plans-students`, or `plans-v2` is hydrated, any CTA anchor whose `data-analytics-id` matches a trial ID is silently dropped. No configuration is required.

To add a new trial analytics ID to the filter, add it to the `FREE_TRIAL_CTA_IDS` set in `web-components/src/hydrate.js:15`.

To add a new plan variant to the filter, add it to the `PLANS_VARIANTS` set in `web-components/src/hydrate.js:21`.

## Configuration

No environment variables or runtime configuration. The filter set and variant set are compile-time constants in `hydrate.js`.

## Testing

```bash
# Run the full hydrate unit test suite
cd web-components && npm test
```

Key test cases in `web-components/test/hydrate.test.js` (line ~284 onward):
- Each trial ID filtered on `plans`
- `plans-education` and `plans-students` variants also filter
- `plans-v2` variant filters
- Mixed CTA list: trial removed, non-trial preserved
- Non-plan variant (`ccd-slice`): trial CTA passes through unchanged

## Notes

- The footer slot is always appended, even if empty after filtering, to avoid broken layout from a missing slot element.
- The `data-analytics-id` attribute is accessed via `cta.dataset.analyticsId` (camelCase DOM property mapping).
