import { test, expect, webUtil, miloLibs, setTestPage } from '../../../libs/mas-test.js';
import InlinePricePage from '../inline-price.page.js';
import InlinePriceSpec from '../specs/inline-price.spec.js';

const { features } = InlinePriceSpec;

test.describe('Inline Price — Tax Inclusivity feature test suite', () => {
    test(`${features[0].name},${features[0].tags}`, async ({ page, baseURL }) => {
        const { data } = features[0];
        const inlinePrice = new InlinePricePage(page);
        const testPage = `${baseURL}${features[0].path}${miloLibs}${features[0].browserParams}`;
        setTestPage(testPage);

        await test.step('step-1: Go to inline-price tax nowrap test page', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
        });

        await test.step('step-2: Verify inline-price span and tax inclusivity element render', async () => {
            await expect(inlinePrice.priceSpan(data.wcsOsi)).toBeVisible();
            await expect(inlinePrice.taxInclusivity(data.wcsOsi)).toBeVisible();
        });

        await test.step('step-3: Verify .price-tax-inclusivity has white-space: nowrap', async () => {
            await expect(inlinePrice.taxInclusivity(data.wcsOsi)).toHaveCSS('white-space', 'nowrap');
            expect(
                await webUtil.verifyCSS(inlinePrice.taxInclusivity(data.wcsOsi), inlinePrice.cssProp.taxInclusivity),
            ).toBeTruthy();
        });
    });
});
