import { test, expect, studio, miloLibs, setTestPage } from '../../../libs/mas-test.js';
import SearchPage from '../search.page.js';
import SearchSpec from '../specs/search.spec.js';

const { features } = SearchSpec;

test.describe('M@S Studio Search by Title feature test suite', () => {
    // @studio-search-by-title-placeholder - Validate search input reads "Search by title"
    test(`${features[0].name},${features[0].tags}`, async ({ page, baseURL }) => {
        const search = new SearchPage(page);
        const testPage = `${baseURL}${features[0].path}${miloLibs}${features[0].browserParams}`;
        setTestPage(testPage);

        await test.step('step-1: Go to MAS Studio test page', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
        });

        await test.step('step-2: Validate search field placeholder reads "Search by title"', async () => {
            await expect(await search.searchField).toBeVisible();
            await expect(await search.searchField).toHaveAttribute('placeholder', 'Search by title');
            await expect(await search.searchInput).toBeVisible();
            await expect(await search.searchIcon).toBeVisible();
        });
    });

    // @studio-search-by-title-exact-match - Searching an exact CF title returns that fragment
    test(`${features[1].name},${features[1].tags}`, async ({ page, baseURL }) => {
        const search = new SearchPage(page);
        const { data } = features[1];
        const testPage = `${baseURL}${features[1].path}${miloLibs}${features[1].browserParams}`;
        setTestPage(testPage);

        await test.step('step-1: Go to MAS Studio test page', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
            await studio.waitForCardsLoaded();
        });

        await test.step('step-2: Submit exact title query and validate fragment is found', async () => {
            await search.submitSearch(data.query);
            await studio.waitForCardsLoaded();
            await expect(await studio.getCard(data.cardid)).toBeVisible();
        });
    });

    // @studio-search-by-title-partial-match - Partial title matches return the fragment
    test(`${features[2].name},${features[2].tags}`, async ({ page, baseURL }) => {
        const search = new SearchPage(page);
        const { data } = features[2];
        const testPage = `${baseURL}${features[2].path}${miloLibs}${features[2].browserParams}`;
        setTestPage(testPage);

        await test.step('step-1: Go to MAS Studio test page', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
            await studio.waitForCardsLoaded();
        });

        await test.step('step-2: Submit partial title query and validate matching fragment is present', async () => {
            await search.submitSearch(data.query);
            await studio.waitForCardsLoaded();
            await expect(await studio.getCard(data.cardid)).toBeVisible();
        });
    });

    // @studio-search-by-title-case-insensitive - Case-insensitive title match
    test(`${features[3].name},${features[3].tags}`, async ({ page, baseURL }) => {
        const search = new SearchPage(page);
        const { data } = features[3];
        const testPage = `${baseURL}${features[3].path}${miloLibs}${features[3].browserParams}`;
        setTestPage(testPage);

        await test.step('step-1: Go to MAS Studio test page', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
            await studio.waitForCardsLoaded();
        });

        await test.step('step-2: Submit lowercase title query and validate match', async () => {
            await search.submitSearch(data.query);
            await studio.waitForCardsLoaded();
            await expect(await studio.getCard(data.cardid)).toBeVisible();
        });
    });

    // @studio-search-by-title-empty-query - Empty query returns all fragments in the folder
    test(`${features[4].name},${features[4].tags}`, async ({ page, baseURL }) => {
        const search = new SearchPage(page);
        const { data } = features[4];
        const testPage = `${baseURL}${features[4].path}${miloLibs}${features[4].browserParams}`;
        setTestPage(testPage);

        let unfilteredCount = 0;

        await test.step('step-1: Go to MAS Studio test page', async () => {
            await page.goto(testPage);
            await page.waitForLoadState('domcontentloaded');
            await studio.waitForCardsLoaded();
        });

        await test.step('step-2: Capture unfiltered fragment count', async () => {
            unfilteredCount = await search.cards.count();
            expect(unfilteredCount).toBeGreaterThan(1);
        });

        await test.step('step-3: Apply filter then clear it to restore the full list', async () => {
            await search.submitSearch(data.query);
            await studio.waitForCardsLoaded();
            const filteredCount = await search.cards.count();
            expect(filteredCount).toBeLessThanOrEqual(unfilteredCount);

            await search.clearSearch();
            await studio.waitForCardsLoaded();
            const restoredCount = await search.cards.count();
            expect(restoredCount).toBe(unfilteredCount);
        });
    });
});
