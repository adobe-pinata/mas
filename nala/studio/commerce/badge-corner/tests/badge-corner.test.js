import BadgeCornerPage from '../badge-corner.page.js';
import { test, expect, studio, webUtil, miloLibs, setTestPage } from '../../../../../libs/mas-test.js';
import BadgeCornerSpec from '../specs/badge-corner.spec.js';

const { features } = BadgeCornerSpec;

test.describe('M@S Studio Merch Card Corner Badge test suite', () => {
    // @studio-badge-corner-truncation - Corner badge must truncate long text with ellipsis
    test(`${features[0].name},${features[0].tags}`, async ({ page, baseURL }) => {
        const { data } = features[0];
        const testPage = `${baseURL}${features[0].path}${miloLibs}${features[0].browserParams}${data.cardid}`;
        const badgeCorner = new BadgeCornerPage(page);
        setTestPage(testPage);

        await test.step('step-1: Go to test page', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
        });

        await test.step('step-2: Validate merch card with corner badge is visible', async () => {
            const card = await studio.getCard(data.cardid);
            await expect(card).toBeVisible();
            const badge = card.locator('div[class$="-badge"]').first();
            await expect(badge).toBeVisible();
        });

        await test.step('step-3: Validate corner badge has truncation CSS properties', async () => {
            const card = await studio.getCard(data.cardid);
            const badge = card.locator('div[class$="-badge"]').first();
            expect(await webUtil.verifyCSS(badge, badgeCorner.cssProp.badgeTruncation)).toBeTruthy();
        });

        await test.step('step-4: Validate corner badge retains absolute positioning and centering', async () => {
            const card = await studio.getCard(data.cardid);
            const badge = card.locator('div[class$="-badge"]').first();
            expect(await webUtil.verifyCSS(badge, badgeCorner.cssProp.badgeLayout)).toBeTruthy();
        });

        await test.step('step-5: Validate corner badge never wraps onto a second line', async () => {
            const card = await studio.getCard(data.cardid);
            const badge = card.locator('div[class$="-badge"]').first();
            const { scrollHeight, clientHeight } = await badge.evaluate((el) => ({
                scrollHeight: el.scrollHeight,
                clientHeight: el.clientHeight,
            }));
            // Single-line height when white-space: nowrap is active
            expect(scrollHeight).toBeLessThanOrEqual(clientHeight + 1);
        });
    });
});
