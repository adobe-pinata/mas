/**
 * Trade logger — appends JSON lines to a log file and prints a human-readable summary.
 */

import { appendFileSync } from 'fs';

export function createLogger(logFile) {
    return {
        /**
         * Logs a completed trade.
         * @param {{ timestamp, entryPrice, exitPrice, leverage, side, resolution, pnl, positionSizeUsd }} entry
         */
        log(entry) {
            const line = JSON.stringify(entry);
            appendFileSync(logFile, line + '\n', 'utf8');

            const sign = entry.pnl >= 0 ? '+' : '';
            console.log(
                `[${entry.timestamp}] ${entry.side.toUpperCase()} | ` +
                `entry=${entry.entryPrice.toFixed(2)} exit=${entry.exitPrice.toFixed(2)} | ` +
                `${entry.resolution} | PnL=${sign}${entry.pnl.toFixed(4)} USD`
            );
        },
    };
}
