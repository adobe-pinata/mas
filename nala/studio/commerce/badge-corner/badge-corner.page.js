export default class BadgeCornerPage {
    constructor(page) {
        this.page = page;

        // Corner badge matches any `div[class$='-badge']` inside a merch-card
        // (e.g. `.ccd-slice-badge`, `.ccd-suggested-badge`, `.plans-badge`, etc.)
        this.cardBadge = page.locator('div[class$="-badge"]').first();

        // CSS properties validating the truncation behavior added in MWPW-191478.
        // These must hold for every merch-card variant that renders a corner badge.
        this.cssProp = {
            badgeTruncation: {
                'white-space': 'nowrap',
                overflow: 'hidden',
                'text-overflow': 'ellipsis',
            },
            badgeLayout: {
                position: 'absolute',
                'text-align': 'center',
            },
        };
    }
}
