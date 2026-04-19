export default class AcomLingoPage {
    // TODO(MWPW-XXXX): replace with Lingo fragment UUID
    static PRODUCT_UUID = '5a5ca143-a417-4087-b466-5b72ac68a830';
    // TODO(MWPW-XXXX): replace with Lingo fragment UUID
    static SPECIAL_OFFERS_UUID = '1736f2c9-0931-401b-b3c0-fe87ff72ad38';
    // TODO(MWPW-XXXX): replace with Lingo fragment UUID
    static IMAGE_UUID = '616273eb-3aad-462a-a6d7-6f6857973b77';
    // TODO(MWPW-XXXX): replace with Lingo fragment UUID
    static MINI_COMPARE_CHART_UUID = '8373b5c2-69e6-4e9c-befc-b424dd33469b';
    // TODO(MWPW-XXXX): replace with Lingo fragment UUID
    static SEGMENT_UUID = 'dfc2eede-7e88-4ed3-b96c-f5214472dfcf';

    constructor(page) {
        this.page = page;
    }

    getCard(uuid) {
        return this.page.locator(`merch-card:has(aem-fragment[fragment="${uuid}"])`);
    }

    getCardPrice(uuid) {
        return this.getCard(uuid).locator('span[data-template="price"]').first();
    }

    getCardCTA(uuid) {
        return this.getCard(uuid)
            .locator('div[slot="footer"] a[is="checkout-link"], div[slot="footer"] a[is="checkout-button"]')
            .first();
    }

    async waitForMasReady(uuid, timeout = 20000) {
        const card = this.getCard(uuid);
        await card.evaluate(
            (el, t) =>
                new Promise((resolve, reject) => {
                    const timer = setTimeout(() => reject(new Error('mas:ready timeout')), t);
                    el.addEventListener(
                        'mas:ready',
                        () => {
                            clearTimeout(timer);
                            resolve();
                        },
                        { once: true },
                    );
                }),
            timeout,
        );
    }
}
