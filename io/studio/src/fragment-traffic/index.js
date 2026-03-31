/**
 * Fragment Traffic App Builder Action
 *
 * Actions:
 *  - getDisplays: returns bucketed traffic data for a specific fragment
 *  - refresh:     queries Grafana ClickHouse and stores new buckets (invoked by scheduled trigger)
 *
 * Stored data shape (per fragment key `${surface}/${locale}/${id}`):
 *   {
 *     lastHour:  { count: number, trend: string },
 *     lastDay:   { count: number, trend: string },
 *     lastMonth: { count: number, trend: string },
 *     updatedAt: ISO timestamp,
 *   }
 */

import { Core, State } from '@adobe/aio-sdk';
import { errorResponse } from '../../utils.js';

const logger = Core.Logger('fragment-traffic', { level: 'info' });

const GRAFANA_URL = 'https://grafana-us.trafficpeak.live/api/ds/query';
const GRAFANA_DATASOURCE_UID = 'clickhouse';
const MAS_IO_PATH_PATTERN = '/mas/io/fragment';
const STATE_KEY_PREFIX = 'fragment-traffic:';

// ------------------------------------------------------------------ helpers --

function stateKey(surface, locale, id) {
    return `${STATE_KEY_PREFIX}${surface}:${locale}:${id}`;
}

function trendPercent(current, previous) {
    if (!previous || previous === 0) return null;
    const pct = ((current - previous) / previous) * 100;
    const sign = pct > 0 ? '+' : '';
    return `${sign}${pct.toFixed(0)}%`;
}

function buildClickHouseQuery(fromIso, toIso) {
    return `SELECT
  toStartOfHour(timestamp) AS hour,
  path,
  count() AS requests
FROM cdn_requests
WHERE timestamp >= '${fromIso}' AND timestamp < '${toIso}'
  AND path LIKE '${MAS_IO_PATH_PATTERN}%'
GROUP BY hour, path
ORDER BY hour DESC`;
}

async function queryGrafana(grafanaToken, fromIso, toIso) {
    const body = {
        queries: [
            {
                datasourceId: 0,
                datasource: { uid: GRAFANA_DATASOURCE_UID },
                rawSql: buildClickHouseQuery(fromIso, toIso),
                format: 'table',
                refId: 'A',
            },
        ],
        from: fromIso,
        to: toIso,
    };

    const response = await fetch(GRAFANA_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${grafanaToken}`,
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        throw new Error(`Grafana query failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    // Extract rows from Grafana table response
    const frames = data?.results?.A?.frames || [];
    const rows = [];
    for (const frame of frames) {
        const fields = frame.schema?.fields || [];
        const values = frame.data?.values || [];
        const hourIdx = fields.findIndex((f) => f.name === 'hour');
        const pathIdx = fields.findIndex((f) => f.name === 'path');
        const countIdx = fields.findIndex((f) => f.name === 'requests');
        if (hourIdx < 0 || pathIdx < 0 || countIdx < 0) continue;
        const len = values[hourIdx]?.length || 0;
        for (let i = 0; i < len; i++) {
            rows.push({
                hour: values[hourIdx][i],
                path: values[pathIdx][i],
                count: values[countIdx][i],
            });
        }
    }
    return rows;
}

/**
 * Extract fragment id from a /mas/io/fragment path like:
 *   /mas/io/fragment?fragment=<uuid>&...
 * Returns null if not parseable.
 */
function extractFragmentId(path) {
    try {
        const url = new URL(`https://x${path}`);
        return url.searchParams.get('fragment') || null;
    } catch {
        return null;
    }
}

// ---------------------------------------------------------------- handlers --

async function handleRefresh(params) {
    const { grafanaToken } = params;
    if (!grafanaToken) return errorResponse(400, 'grafanaToken parameter required', logger);

    const now = new Date();
    const ago30d = new Date(now - 30 * 24 * 60 * 60 * 1000);
    const rows = await queryGrafana(grafanaToken, ago30d.toISOString(), now.toISOString());

    // Bucket per fragmentId
    const hourMs = 60 * 60 * 1000;
    const dayMs = 24 * hourMs;
    const monthMs = 30 * dayMs;
    const nowMs = now.getTime();

    const buckets = {};
    for (const row of rows) {
        const id = extractFragmentId(row.path);
        if (!id) continue;
        if (!buckets[id]) buckets[id] = { lastHour: 0, prevHour: 0, lastDay: 0, lastMonth: 0 };
        const ts = new Date(row.hour).getTime();
        const age = nowMs - ts;
        if (age <= hourMs) buckets[id].lastHour += row.count;
        if (age > hourMs && age <= 2 * hourMs) buckets[id].prevHour += row.count;
        if (age <= dayMs) buckets[id].lastDay += row.count;
        if (age <= monthMs) buckets[id].lastMonth += row.count;
    }

    let stateLib;
    try {
        stateLib = await State.init();
    } catch {
        // State unavailable; skip persisting buckets this run
        stateLib = null;
    }

    const entries = Object.entries(buckets);
    for (const [id, counts] of entries) {
        const value = JSON.stringify({
            lastHour: { count: counts.lastHour, trend: trendPercent(counts.lastHour, counts.prevHour) },
            lastDay: { count: counts.lastDay, trend: trendPercent(counts.lastDay, counts.lastHour * 24) },
            lastMonth: { count: counts.lastMonth, trend: trendPercent(counts.lastMonth, counts.lastDay * 30) },
            updatedAt: now.toISOString(),
        });
        const key = `${STATE_KEY_PREFIX}${id}`;
        if (stateLib) {
            await stateLib.put(key, value, { ttl: 90 * 24 * 60 * 60 });
        }
    }

    logger.info(`Refreshed traffic buckets for ${entries.length} fragments`);
    return { statusCode: 200, body: { refreshed: entries.length } };
}

async function handleGetDisplays(params) {
    const { id, locale, surface } = params;
    if (!id) return errorResponse(400, 'id parameter required', logger);

    let stateLib;
    try {
        stateLib = await State.init();
    } catch {
        return { statusCode: 200, body: { lastHour: null, lastDay: null, lastMonth: null } };
    }

    // Try by raw id first, then by surface:locale:id key
    const keys = [`${STATE_KEY_PREFIX}${id}`];
    if (surface && locale) keys.push(stateKey(surface, locale, id));

    let stored = null;
    for (const key of keys) {
        const entry = await stateLib.get(key).catch(() => null);
        if (entry?.value) {
            stored = JSON.parse(entry.value);
            break;
        }
    }

    if (!stored) {
        return { statusCode: 200, body: { lastHour: null, lastDay: null, lastMonth: null } };
    }

    return {
        statusCode: 200,
        body: {
            lastHour: stored.lastHour ?? null,
            lastDay: stored.lastDay ?? null,
            lastMonth: stored.lastMonth ?? null,
        },
    };
}

// -------------------------------------------------------------- main entry --

async function main(params) {
    try {
        const action = params.action || params.__ow_body?.action;

        if (action === 'refresh') {
            return handleRefresh(params);
        }

        if (action === 'getDisplays') {
            return handleGetDisplays(params);
        }

        return errorResponse(400, `Unknown action: "${action}". Use "getDisplays" or "refresh".`, logger);
    } catch (err) {
        logger.error(err);
        return errorResponse(500, err.message, logger);
    }
}

export { main };
