import { isPositiveFiniteNumber } from '@dexter/tacocat-core';
import { formatRegularPrice } from '../price/utilities.js';

const getDiscount = (price, priceWithoutDiscount) => {
    if (
        !isPositiveFiniteNumber(price) ||
        !isPositiveFiniteNumber(priceWithoutDiscount)
    )
        return;
    return Math.floor(
        ((priceWithoutDiscount - price) / priceWithoutDiscount) * 100,
    );
};

// Map recurrenceTerm values returned by formatRegularPrice to period suffix strings
const periodSuffix = { MONTH: '/mo', YEAR: '/yr' };

/**
 * Renders the discount markup
 * @param {PriceContext & PromoPriceContext} context
 * @param {PriceData} value
 * @param {PriceAttributes} attributes
 !* @returns {string} the discount markup
 !*/
const createDiscountTemplate = () => (context, value) => {
    const { price, priceWithoutDiscount } = value;
    const discount = getDiscount(price, priceWithoutDiscount);

    // Base percentage span — unchanged behavior
    const percentageSpan =
        discount === undefined
            ? `<span class="no-discount"></span>`
            : `<span class="discount">${discount}%</span>`;

    // Savings amount span — only rendered when display-savings attribute is present
    if (context.displaySavings && discount !== undefined) {
        const savingsAmount = priceWithoutDiscount - price;
        const formatted = formatRegularPrice({
            ...context,
            price: savingsAmount,
        });
        const suffix = periodSuffix[formatted.recurrenceTerm] ?? '';
        const savingsSpan = `<span class="discount-savings">${formatted.accessiblePrice}${suffix}</span>`;
        return `${percentageSpan}${savingsSpan}`;
    }

    return percentageSpan;
};

export { getDiscount, createDiscountTemplate };
