export default class MasLingo {
    constructor(page) {
        this.page = page;
    }

    getCard(id) {
        return this.page.locator(`merch-card:has(aem-fragment[fragment="${id}"])`).first();
    }

    getGalleryFooterCtas(variant) {
        return this.page.locator(`merch-card[variant="${variant}"] div[slot="footer"] :is(a, button)`);
    }
}
