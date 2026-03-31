// Docs gallery tests use base @playwright/test (not masTest) — masTest fixtures
// (fragment tracking, request counting) are for Studio tests. Docs tests use
// createWorkerPageSetup for shared page lifecycle instead.
// See nala/docs/acom/plansdocs.test.js for the canonical docs-test precedent.
import { expect, test } from '@playwright/test';
import { features } from './lingodocs.spec.js';
import MasLingo from './lingo.page.js';
import { createWorkerPageSetup, DOCS_GALLERY_PATH } from '../../utils/commerce.js';

test.skip(({ browserName }) => browserName !== 'chromium', 'Not supported to run on multiple browsers.');

const workerSetup = createWorkerPageSetup({
    pages: [{ name: 'US', url: DOCS_GALLERY_PATH.LINGO }],
});

test.describe('ACOM MAS Lingo cards feature test suite', () => {
    test.beforeAll(async ({ browser, baseURL }) => {
        await workerSetup.setupWorkerPages({ browser, baseURL });
    });

    test.afterAll(async () => {
        await workerSetup.cleanupWorkerPages();
    });

    test.afterEach(async ({}, testInfo) => {
        workerSetup.attachWorkerErrorsToFailure(testInfo);
    });

    // @MAS-Lingo-Product
    test(`${features[0].name},${features[0].tags}`, async () => {
        const { data } = features[0];
        let lingoPage;

        await test.step('step-1: Go to Lingo Merch Card feature test page', async () => {
            const page = workerSetup.getPage('US');
            lingoPage = new MasLingo(page);

            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify Lingo Product Merch Card', async () => {
            await lingoPage.waitForCard(data.id);
            await expect(lingoPage.getCardTitle(data.id)).toContainText(data.title);
            await expect(lingoPage.getCardCTA(data.id)).toBeVisible();
        });
    });

    // @MAS-Lingo-Special-Offers
    test(`${features[1].name},${features[1].tags}`, async () => {
        const { data } = features[1];
        let lingoPage;

        await test.step('step-1: Go to Lingo Merch Card feature test page', async () => {
            const page = workerSetup.getPage('US');
            lingoPage = new MasLingo(page);

            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify Lingo Special Offers Merch Card', async () => {
            await lingoPage.waitForCard(data.id);
            await expect(lingoPage.getCardTitle(data.id)).toContainText(data.title);
            await expect(lingoPage.getCardCTA(data.id)).toBeVisible();
        });
    });

    // @MAS-Lingo-Image
    test(`${features[2].name},${features[2].tags}`, async () => {
        const { data } = features[2];
        let lingoPage;

        await test.step('step-1: Go to Lingo Merch Card feature test page', async () => {
            const page = workerSetup.getPage('US');
            lingoPage = new MasLingo(page);

            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify Lingo Image Merch Card', async () => {
            await lingoPage.waitForCard(data.id);
            await expect(lingoPage.getCardTitle(data.id)).toContainText(data.title);
            await expect(lingoPage.getCardCTA(data.id)).toBeVisible();
        });
    });

    // @MAS-Lingo-Mini-Compare
    test(`${features[3].name},${features[3].tags}`, async () => {
        const { data } = features[3];
        let lingoPage;

        await test.step('step-1: Go to Lingo Merch Card feature test page', async () => {
            const page = workerSetup.getPage('US');
            lingoPage = new MasLingo(page);

            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify Lingo Mini Compare Merch Card', async () => {
            await lingoPage.waitForCard(data.id);
            await expect(lingoPage.getCardTitle(data.id)).toContainText(data.title);
            await expect(lingoPage.getCardCTA(data.id)).toBeVisible();
        });
    });

    // @MAS-Lingo-Segment
    test(`${features[4].name},${features[4].tags}`, async () => {
        const { data } = features[4];
        let lingoPage;

        await test.step('step-1: Go to Lingo Merch Card feature test page', async () => {
            const page = workerSetup.getPage('US');
            lingoPage = new MasLingo(page);

            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify Lingo Segment Merch Card', async () => {
            await lingoPage.waitForCard(data.id);
            await expect(lingoPage.getCardTitle(data.id)).toContainText(data.title);
            await expect(lingoPage.getCardCTA(data.id)).toBeVisible();
        });
    });
});
