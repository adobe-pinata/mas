import { LitElement, html, css } from 'lit';

class MasSideNavItem extends LitElement {
    static properties = {
        label: { type: String },
        selected: { type: Boolean },
        disabled: { type: Boolean },
        href: { type: String },
    };

    static styles = css`
        :host {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 12px 8px;
            margin: 4px;
            border-radius: 8px;
            font-size: 12px;
            color: var(--spectrum-gray-800, #292929);
            text-align: center;
            min-height: 52px;
            width: 68px;
            box-sizing: border-box;
            cursor: pointer;
            transition:
                background-color 0.2s ease,
                color 0.2s ease;
            user-select: none;
        }

        :host(:hover:not([disabled])) {
            background-color: rgba(0, 0, 0, 0.04);
        }

        :host([disabled]) {
            opacity: 0.4;
            cursor: not-allowed;
        }

        .icon-container {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            margin-bottom: 4px;
        }

        :host([selected]) .icon-container {
            background-color: var(--spectrum-gray-900, #000000);
            border-radius: 8px;
        }

        ::slotted(*) {
            width: 20px;
            height: 20px;
            color: var(--spectrum-gray-800, #292929);
        }

        :host([selected]) ::slotted(*) {
            color: var(--spectrum-white, #ffffff);
        }

        .label {
            font-family: 'Adobe Clean', sans-serif;
            font-size: 12px;
            font-weight: inherit;
            line-height: 18px;
            text-align: center;
            white-space: nowrap;
        }

        .support-indicator {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 14px;
            height: 14px;
        }

        :host(.side-nav-support) {
            position: relative;
        }

        a.nav-anchor {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            height: 100%;
            text-decoration: none;
            color: inherit;
        }
    `;

    constructor() {
        super();
        this.handleClick = this.handleClick.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        this.addEventListener('click', this.handleClick);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.removeEventListener('click', this.handleClick);
    }

    handleClick(event) {
        if (this.href) return; // anchor handles navigation
        if (this.disabled) {
            event.stopPropagation();
            event.preventDefault();
            return;
        }
        this.dispatchEvent(
            new CustomEvent('nav-click', {
                bubbles: true,
                composed: true,
            }),
        );
    }

    #handleAnchorClick(event) {
        if (this.disabled) {
            event.preventDefault();
            return;
        }
        // Middle-click or modifier key: let browser open in new tab natively
        if (event.button === 1 || event.ctrlKey || event.metaKey || event.shiftKey) {
            return;
        }
        // Left-click: prevent full navigation, use SPA router via nav-click
        event.preventDefault();
        this.dispatchEvent(
            new CustomEvent('nav-click', {
                bubbles: true,
                composed: true,
            }),
        );
    }

    render() {
        const content = html`
            <div class="icon-container">
                <slot name="icon"></slot>
            </div>
            <div class="label">${this.label}</div>
        `;
        if (this.href) {
            return html`<a
                class="nav-anchor"
                href="${this.href}"
                @click="${this.#handleAnchorClick}"
                >${content}</a
            >`;
        }
        return content;
    }
}

customElements.define('mas-side-nav-item', MasSideNavItem);
