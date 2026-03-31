/**
 * BTC Leverage Trading Bot — main entry point.
 *
 * Usage:
 *   node scripts/btc-bot/bot.js           # runs continuously
 *   node scripts/btc-bot/bot.js --once    # single iteration then exit
 */

import { loadConfig } from './config.js';
import { createExchange } from './exchange.js';
import { createStrategy } from './strategy.js';
import { createLogger } from './logger.js';

const args = process.argv.slice(2);
const runOnce = args.includes('--once');

async function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function tick(exchange, strategy, logger, config) {
    const candle = await exchange.getLatestCandle();
    const entryPrice = candle.open;
    const exitPrice = candle.close;

    const side = strategy.decideSide(candle);
    const position = exchange.openPosition(side, entryPrice, config);
    let { pnl } = exchange.closePosition(position, exitPrice);

    // Apply stop-loss cap
    const maxLoss = config.positionSizeUsd * config.stopLossPct;
    if (pnl < -maxLoss) {
        pnl = -maxLoss;
    }

    const resolution = exitPrice > entryPrice ? 'YES' : 'NO';

    logger.log({
        timestamp: new Date(candle.openTime).toISOString(),
        entryPrice,
        exitPrice,
        leverage: config.leverage,
        side,
        resolution,
        pnl,
        positionSizeUsd: config.positionSizeUsd,
    });

    return candle;
}

async function main() {
    const config = loadConfig();
    const exchange = createExchange(config);
    const strategy = createStrategy(config.strategy);
    const logger = createLogger(config.logFile);

    if (runOnce) {
        await tick(exchange, strategy, logger, config);
        return;
    }

    // Continuous loop — sleep until next candle boundary
    while (true) {
        let candle;
        try {
            candle = await tick(exchange, strategy, logger, config);
        } catch (err) {
            console.error('Error during tick:', err.message);
        }

        // Sleep until the start of the next candle interval
        const nextCandleTime = candle
            ? candle.openTime + config.candleIntervalMs
            : Date.now() + config.candleIntervalMs;
        const delay = nextCandleTime - Date.now();
        await sleep(delay > 0 ? delay : config.candleIntervalMs);
    }
}

main().catch((err) => {
    console.error('Fatal error:', err.message);
    process.exit(1);
});
