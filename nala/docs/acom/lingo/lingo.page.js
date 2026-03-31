export default class MasLingo {
    constructor(page) {
        this.page = page;
    }

    getCard(id) {
        return this.page.locator(`merch-card:has(aem-fragment[fragment="${id}"])`);
    }

    async waitForCard(id) {
        const card = this.getCard(id);
        await card.waitFor({ state: 'visible' });
        await this.page.waitForFunction(
            (selector) => document.querySelector(selector)?.closest('merch-card')?.readyState === 'done',
            `merch-card:has(aem-fragment[fragment="${id}"])`,
        );
        return card;
    }

    getCardTitle(id) {
        const card = this.getCard(id);
        return card.locator('h3[slot="heading-xs"]');
    }

    getCardDescription(id) {
        const card = this.getCard(id);
        return card.locator('div[slot="body-xs"]');
    }

    getCardPrice(id) {
        const card = this.getCard(id);
        return card.locator('p[slot="heading-m"]');
    }

    getCardCTA(id) {
        const card = this.getCard(id);
        return card.locator('div[slot="footer"] > a[is="checkout-link"]');
    }

    getCardIcon(id) {
        const card = this.getCard(id);
        return card.locator('merch-icon');
    }

    getCardBadge(id) {
        const card = this.getCard(id);
        return card.locator('merch-badge');
    }
}
