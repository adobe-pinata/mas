export default class SearchPage {
    constructor(page) {
        this.page = page;

        this.searchField = page.locator('#actions sp-search');
        this.searchInput = page.locator('#actions sp-search input');
        this.searchIcon = page.locator('#actions sp-search[placeholder="Search by title"] sp-icon-search');
        this.renderView = page.locator('#render');
        this.cards = this.renderView.locator('merch-card');
    }

    async submitSearch(query) {
        await this.searchInput.fill(query);
        await this.page.keyboard.press('Enter');
    }

    async clearSearch() {
        await this.searchInput.fill('');
        await this.page.keyboard.press('Enter');
    }

    async getCardTitle(card) {
        return card.locator('[slot="heading-xs"], h3').first();
    }
}
