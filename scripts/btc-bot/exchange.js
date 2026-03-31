/**
 * Exchange adapter.
 * Paper mode: simulates position open/close with no real credentials.
 * Live Binance mode: not implemented.
 */

const BINANCE_KLINES_URL =
    'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=2';

export function createExchange(config) {
    if (config.exchange !== 'paper') {
        throw new Error('live mode not implemented');
    }

    return {
        /**
         * Fetches the last closed 1h BTC/USDT candle from Binance public API.
         * Falls back to a synthetic candle in paper mode when the API is unreachable.
         * Returns: { openTime, open, high, low, close, volume }
         */
        async getLatestCandle() {
            try {
                const res = await fetch(BINANCE_KLINES_URL);
                if (!res.ok) {
                    throw new Error(`Binance API error: ${res.status} ${res.statusText}`);
                }
                const data = await res.json();
                // data[0] is the previously closed candle, data[1] is the current open candle
                const [openTime, open, high, low, close, volume] = data[0];
                return {
                    openTime: Number(openTime),
                    open: Number(open),
                    high: Number(high),
                    low: Number(low),
                    close: Number(close),
                    volume: Number(volume),
                };
            } catch (err) {
                // In paper mode, fall back to a synthetic candle so the bot can run offline
                console.warn(`[paper] Candle fetch failed (${err.message}); using synthetic candle.`);
                const now = Date.now();
                const hourMs = 3600000;
                const openTime = now - (now % hourMs) - hourMs;
                const open = 82000 + Math.random() * 4000;
                const close = open + (Math.random() - 0.5) * 1000;
                return {
                    openTime,
                    open: Number(open.toFixed(2)),
                    high: Number((Math.max(open, close) + Math.random() * 200).toFixed(2)),
                    low: Number((Math.min(open, close) - Math.random() * 200).toFixed(2)),
                    close: Number(close.toFixed(2)),
                    volume: Number((Math.random() * 5000).toFixed(4)),
                };
            }
        },

        /**
         * Opens a paper position.
         * @param {'long'|'short'} side
         * @param {number} entryPrice
         * @param {object} cfg
         * @returns {{ side, entryPrice, size, leverage }}
         */
        openPosition(side, entryPrice, cfg) {
            return {
                side,
                entryPrice,
                size: cfg.positionSizeUsd,
                leverage: cfg.leverage,
            };
        },

        /**
         * Closes a paper position and computes PnL.
         * @param {{ side, entryPrice, size, leverage }} position
         * @param {number} exitPrice
         * @returns {{ pnl: number }}
         */
        closePosition(position, exitPrice) {
            const { side, entryPrice, size, leverage } = position;
            const direction = side === 'long' ? 1 : -1;
            const pnl =
                ((exitPrice - entryPrice) / entryPrice) * leverage * size * direction;
            return { pnl };
        },
    };
}
