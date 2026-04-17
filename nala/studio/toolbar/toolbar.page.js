export default class ToolbarPage {
    constructor(page) {
        this.page = page;

        // Scroll container (defined in studio/style.css)
        this.mainContainer = page.locator('.main-container');
        this.contentContainer = page.locator('#content-container');

        // Toolbar host — :host sticky styles apply to this element
        this.toolbar = page.locator('mas-toolbar');

        // Elements inside mas-toolbar shadow DOM
        this.toolbarActions = page.locator('mas-toolbar #actions');
        this.toolbarRead = page.locator('mas-toolbar #read');
        this.toolbarWrite = page.locator('mas-toolbar #write');
        this.search = page.locator('mas-toolbar sp-search');
        this.searchInput = page.locator('mas-toolbar sp-search input');
        this.filterButton = page.locator('mas-toolbar sp-action-button[label="Filter"]');
        this.filterPanel = page.locator('mas-toolbar mas-filter-panel');
        this.createButton = page.locator('mas-toolbar sp-button:has-text("Create")');
        this.selectButton = page.locator('mas-toolbar sp-button:has-text("Select")');
        this.renderModeMenu = page.locator('mas-toolbar sp-action-menu[value="render"]');

        // CSS properties — :host sticky contract per plan
        this.cssProp = {
            toolbarSticky: {
                position: 'sticky',
                top: '0px',
                'z-index': '10',
                'background-color': 'rgb(255, 255, 255)',
                'padding-top': '24px',
                'margin-bottom': '10px',
                display: 'block',
                'box-sizing': 'border-box',
                width: '100%',
            },
        };
    }
}
