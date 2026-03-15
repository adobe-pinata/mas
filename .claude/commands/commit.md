# Generate Git Commit

Create a git commit with a properly formatted conventional commit message based on the staged changes.

## Instructions

### Commit Message Format

Use conventional commits format: `<type>(<scope>): <description>`

**Types:**
- `feat` - New feature or functionality
- `fix` - Bug fix
- `refactor` - Code refactoring without behavior change
- `docs` - Documentation changes
- `test` - Adding or updating tests
- `chore` - Maintenance tasks, dependency updates
- `style` - Code style/formatting changes
- `perf` - Performance improvements

**Scopes** (based on project structure):
- `server` - Server actions, services, routes
- `client` - React SPA, components, pages
- `integrations` - Jira, Slack, WCS, AOS, webhooks
- `storage` - storage.js, local adapter, AIO adapter
- `oauth` - oauth.js token lifecycle
- `specs` - specs/, PROGRESS.md, DECISIONS.md
- `claude` - .claude/ config, hooks, skills, commands
- `adw` - Developer Workflows
- Omit scope for cross-cutting changes

**Description rules:**
- Present tense (e.g., "add", "fix", "update")
- 50 characters or less (entire first line under 72 chars)
- Descriptive of the actual changes made
- No period at the end
- Lowercase first letter

### Examples

- `feat(mas): add merch-card variant for trials`
- `fix(studio): resolve fragment loading race condition`
- `refactor(io): simplify authentication middleware`
- `test(mas): add unit tests for price formatting`
- `chore: update dependencies to latest versions`
- `docs(mcp): document playwright server configuration`

### Rules

- Do NOT include 'Generated with...', 'Authored by...', or AI attribution
- Do NOT commit files that may contain secrets (.env, credentials.json, etc.)
- Focus purely on describing the changes made

## Run

1. Run `git status` to see what files have changed
2. Run `git diff --staged` to see staged changes, or `git diff` for unstaged
3. Run `git add -A` to stage all changes (or selectively add files)
4. Run `git commit` with a HEREDOC message:

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>
EOF
)"
```

5. Run `git status` to verify the commit succeeded

## Post-commit: PROGRESS.md check

After a successful commit, scan the changed files to identify if any tracked open items were completed:

- If changed files are in `server/` or `actions/` → check PROGRESS.md server-side open items
- If changed files are in `client/src/` → check PROGRESS.md client-side open items
- If a tracked open item matches what was just committed, print:
  > "Run `/done \"<item>\"` to mark it complete in PROGRESS.md"

Do not update PROGRESS.md automatically — only suggest it.

## Report

Return ONLY the commit message that was used, followed by any `/done` suggestion if applicable
