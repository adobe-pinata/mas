import { expect, test } from '@playwright/test';
import { features } from './lingo.spec.js';
import MasLingo from './lingo.page.js';
import { createWorkerPageSetup, DOCS_GALLERY_PATH } from '../../utils/commerce.js';

let galleryPage;

test.skip(({ browserName }) => browserName !== 'chromium', 'Not supported to run on multiple browsers.');

const workerSetup = createWorkerPageSetup({
    pages: [{ name: 'US', url: DOCS_GALLERY_PATH.LINGO }],
});

test.describe('Lingo cards gallery feature test suite', () => {
    test.beforeAll(async ({ browser, baseURL }) => {
        await workerSetup.setupWorkerPages({ browser, baseURL });
    });

    test.afterAll(async () => {
        await workerSetup.cleanupWorkerPages();
    });

    test.afterEach(async ({}, testInfo) => {
        // eslint-disable-line no-empty-pattern
        workerSetup.attachWorkerErrorsToFailure(testInfo);
    });

    test(`[Test Id - ${features[0].tcid}] ${features[0].name},${features[0].tags}`, async () => {
        const { data } = features[0];

        await test.step('step-1: Go to Lingo gallery page', async () => {
            const page = workerSetup.getPage('US');
            galleryPage = new MasLingo(page);
            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify card renders and CTA is present', async () => {
            const card = galleryPage.getCard(data.id);
            await expect(card).toBeVisible();
            await expect(card).toHaveAttribute('variant', data.variant);
            const ctas = galleryPage.getGalleryFooterCtas(data.variant);
            await expect(ctas.first()).toBeVisible();
        });
    });

    test(`[Test Id - ${features[1].tcid}] ${features[1].name},${features[1].tags}`, async () => {
        const { data } = features[1];

        await test.step('step-1: Go to Lingo gallery page', async () => {
            const page = workerSetup.getPage('US');
            galleryPage = new MasLingo(page);
            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify card renders and CTA is present', async () => {
            const card = galleryPage.getCard(data.id);
            await expect(card).toBeVisible();
            await expect(card).toHaveAttribute('variant', data.variant);
            const ctas = galleryPage.getGalleryFooterCtas(data.variant);
            await expect(ctas.first()).toBeVisible();
        });
    });

    test(`[Test Id - ${features[2].tcid}] ${features[2].name},${features[2].tags}`, async () => {
        const { data } = features[2];

        await test.step('step-1: Go to Lingo gallery page', async () => {
            const page = workerSetup.getPage('US');
            galleryPage = new MasLingo(page);
            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify card renders and CTA is present', async () => {
            const card = galleryPage.getCard(data.id);
            await expect(card).toBeVisible();
            await expect(card).toHaveAttribute('variant', data.variant);
            const ctas = galleryPage.getGalleryFooterCtas(data.variant);
            await expect(ctas.first()).toBeVisible();
        });
    });

    test(`[Test Id - ${features[3].tcid}] ${features[3].name},${features[3].tags}`, async () => {
        const { data } = features[3];

        await test.step('step-1: Go to Lingo gallery page', async () => {
            const page = workerSetup.getPage('US');
            galleryPage = new MasLingo(page);
            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify card renders and CTA is present', async () => {
            const card = galleryPage.getCard(data.id);
            await expect(card).toBeVisible();
            await expect(card).toHaveAttribute('variant', data.variant);
            const ctas = galleryPage.getGalleryFooterCtas(data.variant);
            await expect(ctas.first()).toBeVisible();
        });
    });

    test(`[Test Id - ${features[4].tcid}] ${features[4].name},${features[4].tags}`, async () => {
        const { data } = features[4];

        await test.step('step-1: Go to Lingo gallery page', async () => {
            const page = workerSetup.getPage('US');
            galleryPage = new MasLingo(page);
            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.LINGO, expect);
        });

        await test.step('step-2: Verify card renders and CTA is present', async () => {
            const card = galleryPage.getCard(data.id);
            await expect(card).toBeVisible();
            await expect(card).toHaveAttribute('variant', data.variant);
            const ctas = galleryPage.getGalleryFooterCtas(data.variant);
            await expect(ctas.first()).toBeVisible();
        });
    });
});
