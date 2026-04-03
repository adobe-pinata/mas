import { expect, test } from '@playwright/test';
import { features } from '../specs/mnemonic_list_css.spec.js';
import MnemonicListPage from '../mnemonic-list.page.js';
import WebUtil from '../../../libs/webutil.js';
import { createWorkerPageSetup, DOCS_GALLERY_PATH } from '../../../utils/commerce.js';

let mnemonicPage;
let webUtil;

const workerSetup = createWorkerPageSetup({
    pages: [{ name: 'US', url: DOCS_GALLERY_PATH.MNEMONIC_LIST }],
});

test.describe('Merch Mnemonic List CSS test suite', () => {
    test.skip(({ browserName }) => browserName !== 'chromium', 'Not supported to run on multiple browsers.');

    test.beforeAll(async ({ browser, baseURL }) => {
        await workerSetup.setupWorkerPages({ browser, baseURL });
    });

    test.afterAll(async () => {
        await workerSetup.cleanupWorkerPages();
    });

    test.afterEach(async ({}, testInfo) => {
        workerSetup.attachWorkerErrorsToFailure(testInfo);
    });

    // @MAS-mnemonic-list-description-font-size
    test(`${features[0].name},${features[0].tags}`, async () => {
        await test.step('step-1: Go to mnemonic list test page', async () => {
            const page = workerSetup.getPage('US');
            mnemonicPage = new MnemonicListPage(page);
            webUtil = new WebUtil(page);

            await workerSetup.verifyPageURL('US', DOCS_GALLERY_PATH.MNEMONIC_LIST, expect);
        });

        await test.step('step-2: Verify merch-mnemonic-list is visible', async () => {
            await expect(mnemonicPage.mnemonicList).toBeVisible();
            await expect(mnemonicPage.description).toBeVisible();
        });

        await test.step('step-3: Verify description slot font-size uses --type-heading-xs-size (18px)', async () => {
            expect(await webUtil.verifyCSS(mnemonicPage.description, mnemonicPage.cssProp.description)).toBeTruthy();
        });
    });
});
