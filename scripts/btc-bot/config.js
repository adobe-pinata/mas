/**
 * Config loader — reads env vars with defaults.
 * Optionally loads a .env file from the current working directory.
 */

import { readFileSync } from 'fs';
import { resolve } from 'path';

function loadDotEnv() {
    try {
        const envPath = resolve(new URL('.', import.meta.url).pathname, '.env');
        const lines = readFileSync(envPath, 'utf8').split('\n');
        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith('#')) continue;
            const eqIdx = trimmed.indexOf('=');
            if (eqIdx === -1) continue;
            const key = trimmed.slice(0, eqIdx).trim();
            const value = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, '');
            if (!(key in process.env)) {
                process.env[key] = value;
            }
        }
    } catch {
        // .env file is optional
    }
}

export function loadConfig() {
    loadDotEnv();

    return {
        leverage: Number(process.env.LEVERAGE ?? 2),
        positionSizeUsd: Number(process.env.POSITION_SIZE_USD ?? 100),
        stopLossPct: Number(process.env.STOP_LOSS_PCT ?? 0.02),
        strategy: process.env.STRATEGY ?? 'momentum',
        exchange: process.env.EXCHANGE ?? 'paper',
        logFile: process.env.LOG_FILE ?? 'trades.log',
        candleIntervalMs: Number(process.env.CANDLE_INTERVAL_MS ?? 3600000),
    };
}
