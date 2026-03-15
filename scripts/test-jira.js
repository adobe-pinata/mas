#!/usr/bin/env node
/**
 * test-jira.js — Jira integration smoke test
 *
 * Creates a test issue, attaches a dummy screenshot, then deletes it.
 *
 * Usage:
 *   node --env-file=apps/experience-qa/server/.env scripts/test-jira.js
 *
 * Required env vars:
 *   JIRA_BASE_URL, JIRA_EMAIL, JIRA_TOKEN, JIRA_PROJECT_KEY
 */

const base    = process.env.JIRA_BASE_URL
const email   = process.env.JIRA_EMAIL
const token   = process.env.JIRA_TOKEN
const project = process.env.JIRA_PROJECT_KEY

if (!base || !email || !token || !project) {
  console.error('❌  Missing required env vars: JIRA_BASE_URL, JIRA_EMAIL, JIRA_TOKEN, JIRA_PROJECT_KEY')
  process.exit(1)
}

const auth = `Basic ${Buffer.from(`${email}:${token}`).toString('base64')}`

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

// ── 1. Create issue ───────────────────────────────────────────────────────────
console.log('\n📋  Jira smoke test\n')
console.log('1. Creating test issue …')

const createRes = await fetch(`${base}/rest/api/3/issue`, {
  method: 'POST',
  headers: {
    Authorization: auth,
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  body: JSON.stringify({
    fields: {
      project:     { key: project },
      summary:     '[experience-qa smoke test] DELETE ME',
      description: {
        version: 1,
        type: 'doc',
        content: [{
          type: 'paragraph',
          content: [{ type: 'text', text: 'Automated smoke test — safe to delete.' }],
        }],
      },
      issuetype: { name: 'Bug' },
      priority:  { name: 'P3' },
      labels:    ['experience-qa', 'smoke-test'],
    },
  }),
})

ok('POST /rest/api/3/issue → 201', createRes.status === 201, `HTTP ${createRes.status}`)

if (!createRes.ok) {
  const body = await createRes.text()
  console.error('Response:', body)
  process.exit(1)
}

const created = await createRes.json()
const { id: issueId, key: issueKey } = created

ok('Response has issueKey',  typeof issueKey === 'string' && issueKey.length > 0, issueKey)
ok('Response has id',        typeof issueId  === 'string' && issueId.length  > 0, issueId)
console.log(`   → ${base}/browse/${issueKey}`)

// ── 2. Attach screenshot ──────────────────────────────────────────────────────
console.log('\n2. Attaching dummy screenshot …')

// 1×1 red PNG (minimal valid PNG bytes)
const PNG_1x1 = Buffer.from(
  '89504e470d0a1a0a0000000d49484452000000010000000108020000009001' +
  '2e00000000c4944415478016360f8cfc00000000200018e8644590000000049454e44ae426082',
  'hex'
)

const form = new FormData()
form.append('file', new Blob([PNG_1x1], { type: 'image/png' }), 'smoke-test.png')

const attachRes = await fetch(`${base}/rest/api/3/issue/${issueId}/attachments`, {
  method: 'POST',
  headers: {
    Authorization: auth,
    'X-Atlassian-Token': 'no-check',
  },
  body: form,
})

ok('POST /attachments → 200', attachRes.ok, `HTTP ${attachRes.status}`)

if (attachRes.ok) {
  const attachments = await attachRes.json()
  ok('Attachment has filename', attachments?.[0]?.filename === 'smoke-test.png', attachments?.[0]?.filename)
}

// ── 3. Verify issue shape ─────────────────────────────────────────────────────
console.log('\n3. Verifying issue shape …')

const getRes = await fetch(`${base}/rest/api/3/issue/${issueKey}`, {
  headers: { Authorization: auth, Accept: 'application/json' },
})

ok('GET /rest/api/3/issue/:key → 200', getRes.ok, `HTTP ${getRes.status}`)

if (getRes.ok) {
  const issue    = await getRes.json()
  const fields   = issue.fields
  const summary  = fields.summary
  const priority = fields.priority?.name
  const labels   = fields.labels ?? []

  ok('summary matches',          summary === '[experience-qa smoke test] DELETE ME', summary)
  ok('priority is P3',           priority === 'P3',            priority)
  ok('label experience-qa set',  labels.includes('experience-qa'),  JSON.stringify(labels))
  ok('label smoke-test set',     labels.includes('smoke-test'),     JSON.stringify(labels))
}

// ── 4. Delete issue ───────────────────────────────────────────────────────────
console.log('\n4. Deleting test issue …')

const deleteRes = await fetch(`${base}/rest/api/3/issue/${issueKey}`, {
  method: 'DELETE',
  headers: { Authorization: auth },
})

ok('DELETE /rest/api/3/issue/:key → 204', deleteRes.status === 204, `HTTP ${deleteRes.status}`)

// ── Result ────────────────────────────────────────────────────────────────────
console.log(`\n${passed + failed} checks: ${passed} passed, ${failed} failed\n`)
process.exit(failed > 0 ? 1 : 0)
