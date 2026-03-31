/**
 * Pluggable strategy module.
 * Momentum strategy: long if last candle closed higher than open, short otherwise.
 */

function momentumStrategy() {
    return {
        /**
         * Decides the trade side based on the candle.
         * @param {{ open: number, close: number }} candle
         * @returns {'long'|'short'}
         */
        decideSide(candle) {
            return candle.close > candle.open ? 'long' : 'short';
        },
    };
}

export function createStrategy(name) {
    switch (name) {
        case 'momentum':
            return momentumStrategy();
        default:
            throw new Error(`Unknown strategy: ${name}`);
    }
}
