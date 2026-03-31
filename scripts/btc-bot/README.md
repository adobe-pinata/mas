# BTC Leverage Trading Bot

A standalone Node.js bot that monitors BTC/USDT 1-hour OHLCV candles on Binance, opens a simulated leveraged position at each candle open, resolves it at candle close, and records all trades in a structured JSON-lines log.

## Overview

- Fetches 1h BTC/USDT candles from the Binance public REST API (no credentials needed in paper mode)
- Applies a pluggable strategy to decide long vs. short
- Simulates leverage, stop-loss, and P&L in paper trading mode
- Appends each trade to `trades.log` as a JSON line
- Supports a `--once` flag for single-shot testing

## Setup

Node.js 18+ is required (uses native `fetch`).

```bash
# From the repo root
cp scripts/btc-bot/.env.example scripts/btc-bot/.env
# Edit .env to override defaults if desired
node scripts/btc-bot/bot.js --once
```

No npm install step is needed — the bot has zero external dependencies.

## Configuration

All configuration is read from environment variables (or an optional `.env` file in the `scripts/btc-bot/` directory).

| Variable | Default | Description |
|---|---|---|
| `LEVERAGE` | `2` | Leverage multiplier applied to each position |
| `POSITION_SIZE_USD` | `100` | Notional position size in USD |
| `STOP_LOSS_PCT` | `0.02` | Stop-loss cap as a fraction of position size (0.02 = 2%) |
| `STRATEGY` | `momentum` | Strategy name (`momentum` is the only built-in option) |
| `EXCHANGE` | `paper` | Exchange mode (`paper` or `live`; live is not yet implemented) |
| `LOG_FILE` | `trades.log` | Path to the JSON-lines trade log file |
| `CANDLE_INTERVAL_MS` | `3600000` | Candle interval in ms (default: 1 hour) |

## Usage

**Single iteration (useful for testing):**
```bash
node scripts/btc-bot/bot.js --once
```

**Continuous loop:**
```bash
node scripts/btc-bot/bot.js
```

The bot sleeps until the next candle boundary between iterations.

## Trade Log Format

Each line in `trades.log` is a JSON object:

```json
{
  "timestamp": "2026-03-31T10:00:00.000Z",
  "entryPrice": 82500.00,
  "exitPrice": 83100.00,
  "leverage": 2,
  "side": "long",
  "resolution": "YES",
  "pnl": 1.4545,
  "positionSizeUsd": 100
}
```

| Field | Description |
|---|---|
| `timestamp` | ISO 8601 candle open time |
| `entryPrice` | Candle open price (USD) |
| `exitPrice` | Candle close price (USD) |
| `leverage` | Leverage multiplier used |
| `side` | `long` or `short` |
| `resolution` | `YES` if close > open, `NO` otherwise |
| `pnl` | Profit/loss in USD (capped by stop-loss) |
| `positionSizeUsd` | Notional position size in USD |

## Paper vs Live Mode

**Paper mode** (default) simulates all trades locally. No exchange account or API keys are required. Only the public Binance klines endpoint is called to obtain price data.

**Live mode** is not yet implemented. Setting `EXCHANGE=live` will throw an error.

## Momentum Strategy

The built-in `momentum` strategy goes **long** if the previous candle closed above its open (bullish candle), and **short** otherwise. Add additional strategies by extending `scripts/btc-bot/strategy.js`.
