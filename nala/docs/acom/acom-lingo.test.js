import { test, expect } from '../../libs/mas-test.js';
import { features } from './acom-lingo.spec.js';
import AcomLingoPage from './acom-lingo.page.js';
import { createWorkerPageSetup, DOCS_GALLERY_PATH } from '../../utils/commerce.js';

test.skip(({ browserName }) => browserName !== 'chromium', 'Not supported to run on multiple browsers.');

const workerSetup = createWorkerPageSetup({
    pages: [{ name: 'LINGO', url: DOCS_GALLERY_PATH.ACOM_LINGO }],
});

test.describe('ACOM Lingo cards feature test suite', () => {
    test.beforeAll(async ({ browser, baseURL }) => {
        await workerSetup.setupWorkerPages({ browser, baseURL });
    });

    test.afterAll(async () => {
        await workerSetup.cleanupWorkerPages();
    });

    test.afterEach(async ({}, testInfo) => {
        workerSetup.attachWorkerErrorsToFailure(testInfo);
    });

    for (const feature of features) {
        test(`${feature.name},${feature.tags}`, async () => {
            const { data } = feature;
            let acomPage;

            await test.step(`step-1: Go to ACOM Lingo gallery page (${data.variant})`, async () => {
                const page = workerSetup.getPage('LINGO');
                acomPage = new AcomLingoPage(page);
                await workerSetup.verifyPageURL('LINGO', DOCS_GALLERY_PATH.ACOM_LINGO, expect);
            });

            await test.step(`step-2: Verify ${data.variant} card is visible`, async () => {
                await expect(acomPage.getCard(data.id)).toBeVisible({ timeout: 20000 });
            });

            await test.step(`step-3: Verify ${data.variant} card fires mas:ready within 20s`, async () => {
                await acomPage.waitForMasReady(data.id, 20000);
            });

            await test.step(`step-4: Verify ${data.variant} card has a price or CTA`, async () => {
                const priceVisible = await acomPage
                    .getCardPrice(data.id)
                    .isVisible()
                    .catch(() => false);
                const ctaVisible = await acomPage
                    .getCardCTA(data.id)
                    .isVisible()
                    .catch(() => false);
                expect(priceVisible || ctaVisible).toBe(true);
            });
        });
    }
});
