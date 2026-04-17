import { test, expect, studio, webUtil, miloLibs, setTestPage } from '../../../libs/mas-test.js';
import ToolbarSpec from '../specs/toolbar.spec.js';
import ToolbarPage from '../toolbar.page.js';

const { features } = ToolbarSpec;

test.describe('M@S Studio Toolbar feature test suite', () => {
    // @studio-toolbar-sticky - Validate mas-toolbar stays pinned at top while fragment list scrolls
    test(`${features[0].name},${features[0].tags}`, async ({ page, baseURL }) => {
        const testPage = `${baseURL}${features[0].path}${miloLibs}${features[0].browserParams}`;
        setTestPage(testPage);
        const toolbar = new ToolbarPage(page);

        await test.step('step-1: Go to MAS Studio content page', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
            await studio.waitForCardsLoaded();
        });

        await test.step('step-2: Validate toolbar is visible with expected controls', async () => {
            await expect(toolbar.toolbar).toBeVisible();
            await expect(toolbar.search).toBeVisible();
            await expect(toolbar.filterButton).toBeVisible();
            await expect(toolbar.createButton).toBeVisible();
            await expect(toolbar.selectButton).toBeVisible();
            await expect(toolbar.renderModeMenu).toBeVisible();
        });

        await test.step('step-3: Validate :host sticky CSS contract', async () => {
            expect(await webUtil.verifyCSS(toolbar.toolbar, toolbar.cssProp.toolbarSticky)).toBeTruthy();
        });

        await test.step('step-4: Validate .main-container is the scroll container', async () => {
            await expect(toolbar.mainContainer).toHaveCSS('overflow-y', 'auto');
        });

        await test.step('step-5: Scroll fragment list and confirm toolbar remains pinned', async () => {
            const initialBox = await toolbar.toolbar.boundingBox();
            expect(initialBox).not.toBeNull();

            await toolbar.mainContainer.evaluate((el) => {
                el.scrollTop = el.scrollHeight;
            });
            await page.waitForTimeout(500);

            await expect(toolbar.toolbar).toBeVisible();
            const scrolledBox = await toolbar.toolbar.boundingBox();
            expect(scrolledBox).not.toBeNull();
            expect(Math.round(scrolledBox.y)).toBe(Math.round(initialBox.y));
        });
    });

    // @studio-toolbar-sticky-table - Validate mas-toolbar stays pinned at top while fragment list scrolls in table view
    test(`${features[1].name},${features[1].tags}`, async ({ page, baseURL }) => {
        const testPage = `${baseURL}${features[1].path}${miloLibs}${features[1].browserParams}`;
        setTestPage(testPage);
        const toolbar = new ToolbarPage(page);

        await test.step('step-1: Go to MAS Studio content page in table view', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
            await studio.waitForCardsLoaded();
        });

        await test.step('step-2: Validate toolbar is visible with expected controls', async () => {
            await expect(toolbar.toolbar).toBeVisible();
            await expect(toolbar.search).toBeVisible();
            await expect(toolbar.filterButton).toBeVisible();
            await expect(toolbar.createButton).toBeVisible();
            await expect(toolbar.selectButton).toBeVisible();
            await expect(toolbar.renderModeMenu).toBeVisible();
        });

        await test.step('step-3: Validate :host sticky CSS contract', async () => {
            expect(await webUtil.verifyCSS(toolbar.toolbar, toolbar.cssProp.toolbarSticky)).toBeTruthy();
        });

        await test.step('step-4: Validate .main-container is the scroll container', async () => {
            await expect(toolbar.mainContainer).toHaveCSS('overflow-y', 'auto');
        });

        await test.step('step-5: Scroll fragment list and confirm toolbar remains pinned', async () => {
            const initialBox = await toolbar.toolbar.boundingBox();
            expect(initialBox).not.toBeNull();

            await toolbar.mainContainer.evaluate((el) => {
                el.scrollTop = el.scrollHeight;
            });
            await page.waitForTimeout(500);

            await expect(toolbar.toolbar).toBeVisible();
            const scrolledBox = await toolbar.toolbar.boundingBox();
            expect(scrolledBox).not.toBeNull();
            expect(Math.round(scrolledBox.y)).toBe(Math.round(initialBox.y));
        });
    });
});
