# fix: increase product name font size in mnemonic list from XXS to XS

## Summary

Product names in the "What's included" section of the M@S Catalog marquee render at `--type-heading-xxs-size` (XXS). They should render at XS (`--type-heading-xs-size`).

## Affected Component

- `web-components/src/merch-mnemonic-list.js`
- Selector: `.mnemonic-list .product-list .product-item strong`

## Acceptance Criteria

- [ ] Font size uses `var(--type-heading-xs-size)` instead of `var(--type-heading-xxs-size)`
- [ ] No visual regressions on other mnemonic-list instances

## References

- Issue: adobe-pinata/mas#126
- Jira: MWPW-191054
