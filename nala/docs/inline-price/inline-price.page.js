export default class InlinePricePage {
    constructor(page) {
        this.page = page;

        this.priceSpan = (wcsOsi) =>
            this.page.locator(`span[is="inline-price"][data-wcs-osi="${wcsOsi}"][data-display-tax="true"]`).first();

        this.taxInclusivity = (wcsOsi) => this.priceSpan(wcsOsi).locator('.price-tax-inclusivity').first();

        this.cssProp = {
            taxInclusivity: {
                'white-space': 'nowrap',
            },
        };
    }
}
