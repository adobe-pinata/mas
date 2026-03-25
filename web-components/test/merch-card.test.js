import { CheckoutLink } from '../src/checkout-link.js';
import { mockFetch } from './mocks/fetch.js';
import { mockIms, unmockIms } from './mocks/ims.js';
import { withWcs } from './mocks/wcs.js';
import {
    expect,
    initMasCommerceService,
    removeMasCommerceService,
} from './utilities.js';
import '../src/mas.js';
import '../src/merch-card.js';

function createMerchCard(checkoutLinkOptions = {}) {
    const card = document.createElement('merch-card');
    const footer = document.createElement('div');
    footer.setAttribute('slot', 'footer');
    const link = CheckoutLink.createCheckoutLink(
        { wcsOsi: 'abm', ...checkoutLinkOptions },
        'Buy now',
    );
    footer.append(link);
    card.append(footer);
    return { card, link };
}

afterEach(() => {
    document.querySelectorAll('merch-card').forEach((el) => el.remove());
    removeMasCommerceService();
    unmockIms();
});

beforeEach(async () => {
    await mockFetch(withWcs);
});

describe('merch-card entitlement attributes', () => {
    it('sets no entitled or upgrade attribute for a plain checkout link', async () => {
        initMasCommerceService();
        const { card, link } = createMerchCard();
        document.body.append(card);
        await card.updateComplete;
        await link.onceSettled();
        expect(card.hasAttribute('entitled')).to.be.false;
        expect(card.hasAttribute('upgrade')).to.be.false;
    });

    it('sets entitled attribute when data-entitlement is true', async () => {
        initMasCommerceService();
        const { card, link } = createMerchCard({ entitlement: 'true' });
        document.body.append(card);
        await card.updateComplete;
        await link.onceSettled();
        expect(card.hasAttribute('entitled')).to.be.true;
        expect(card.hasAttribute('upgrade')).to.be.false;
    });

    it('sets upgrade attribute when data-upgrade is true', async () => {
        initMasCommerceService();
        const { card, link } = createMerchCard({ upgrade: 'true' });
        document.body.append(card);
        await card.updateComplete;
        await link.onceSettled();
        expect(card.hasAttribute('upgrade')).to.be.true;
        expect(card.hasAttribute('entitled')).to.be.false;
    });

    it('removes entitled attribute when data-entitlement changes to false', async () => {
        initMasCommerceService();
        const { card, link } = createMerchCard({ entitlement: 'true' });
        document.body.append(card);
        await card.updateComplete;
        await link.onceSettled();
        expect(card.hasAttribute('entitled')).to.be.true;

        link.dataset.entitlement = 'false';
        await link.onceSettled();
        expect(card.hasAttribute('entitled')).to.be.false;
    });
});
