import { expect } from '@esm-bundle/chai';
import {
    getDiscount,
    createDiscountTemplate,
} from '../../src/discount/template.js';

describe('discount template', () => {
    [
        [undefined, undefined, undefined],
        [null, null, undefined],
        ['', '', undefined],
        [50, 100, 50],
        [27, -1, undefined],
        [27, 30, 10],
    ].forEach(([price, priceWithoutDiscount, expected]) =>
        it(`For price=${price} and old price=${priceWithoutDiscount} and the discount percentage is${expect}`, () => {
            expect(getDiscount(price, priceWithoutDiscount)).to.equal(expected);
        }),
    );

    it('Generates discount markup', () => {
        expect(
            createDiscountTemplate()(
                {},
                { price: 27, priceWithoutDiscount: 30 },
            ),
        ).to.equal('<span class="discount">10%</span>');
    });

    it('Generates no discount markup', () => {
        expect(createDiscountTemplate()({}, { price: 27 })).to.equal(
            '<span class="no-discount"></span>',
        );
    });

    describe('display-savings attribute', () => {
        const yearlyContext = {
            displaySavings: true,
            commitment: 'YEAR',
            term: 'ANNUAL',
            formatString: "'US$'#,##0",
            usePrecision: false,
        };

        const monthlyContext = {
            displaySavings: true,
            commitment: 'MONTH',
            term: 'MONTHLY',
            formatString: "'US$'#,##0",
            usePrecision: false,
        };

        it('does not render savings span when display-savings is absent', () => {
            const result = createDiscountTemplate()(
                {},
                { price: 27, priceWithoutDiscount: 30 },
            );
            expect(result).to.equal('<span class="discount">10%</span>');
            expect(result).to.not.include('discount-savings');
        });

        it('renders percentage and savings span when display-savings is present (yearly)', () => {
            const result = createDiscountTemplate()(yearlyContext, {
                price: 80,
                priceWithoutDiscount: 100,
            });
            expect(result).to.include('<span class="discount">20%</span>');
            expect(result).to.include('discount-savings');
            expect(result).to.include('/yr');
            expect(result).to.include('US$20');
        });

        it('renders savings span with /mo suffix for monthly pricing', () => {
            const result = createDiscountTemplate()(monthlyContext, {
                price: 8,
                priceWithoutDiscount: 10,
            });
            expect(result).to.include('<span class="discount">20%</span>');
            expect(result).to.include('discount-savings');
            expect(result).to.include('/mo');
        });

        it('renders only no-discount span when prices are invalid even with display-savings', () => {
            const result = createDiscountTemplate()(yearlyContext, {
                price: 27,
            });
            expect(result).to.equal('<span class="no-discount"></span>');
            expect(result).to.not.include('discount-savings');
        });
    });
});
