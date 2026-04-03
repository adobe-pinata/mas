export default class MnemonicListPage {
    constructor(page) {
        this.page = page;
        this.mnemonicList = page.locator('merch-mnemonic-list').first();
        this.description = this.mnemonicList.locator('[slot="description"]');

        this.cssProp = {
            description: {
                'font-size': '18px',
            },
        };
    }
}
