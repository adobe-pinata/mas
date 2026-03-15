#!/usr/bin/env node
/**
 * test-slack.js — Slack webhook smoke test
 *
 * Posts a Block Kit test message to the configured webhook and validates the response.
 *
 * Usage:
 *   node --env-file=apps/experience-qa/server/.env scripts/test-slack.js
 *
 * Required env vars:
 *   SLACK_WEBHOOK_URL
 */

const webhookUrl = process.env.SLACK_WEBHOOK_URL

if (!webhookUrl) {
  console.error('❌  Missing required env var: SLACK_WEBHOOK_URL')
  process.exit(1)
}

let passed = 0
let failed = 0

function ok(label, cond, detail = '') {
  if (cond) {
    console.log(`  ✅  ${label}`)
    passed++
  } else {
    console.log(`  ❌  ${label}${detail ? ` — ${detail}` : ''}`)
    failed++
  }
}

console.log('\n💬  Slack webhook smoke test\n')

// ── Post Block Kit test message ───────────────────────────────────────────────
console.log('1. Posting Block Kit test message …')

const payload = {
  blocks: [
    {
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: '*[experience-qa smoke test]* Slack integration is working ✅\n_This message was sent automatically — safe to ignore._',
      },
    },
    {
      type: 'section',
      fields: [
        { type: 'mrkdwn', text: '*Test:*\nSmoke test' },
        { type: 'mrkdwn', text: `*Time:*\n${new Date().toISOString()}` },
      ],
    },
    {
      type: 'context',
      elements: [
        { type: 'mrkdwn', text: 'Sent by `scripts/test-slack.js` — Adobe Experience QA Platform' },
      ],
    },
  ],
}

const res = await fetch(webhookUrl, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
})

ok('POST to webhook → 200', res.ok, `HTTP ${res.status}`)

if (res.ok) {
  const body = await res.text()
  ok('Response body is "ok"', body === 'ok', JSON.stringify(body))
} else {
  const body = await res.text()
  console.error('  Response:', body)
}

// ── Result ────────────────────────────────────────────────────────────────────
console.log(`\n${passed + failed} checks: ${passed} passed, ${failed} failed\n`)
process.exit(failed > 0 ? 1 : 0)
