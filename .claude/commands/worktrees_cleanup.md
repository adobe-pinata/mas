---
description: Clean up all git worktrees, branches, and port processes
---

# Worktrees Cleanup

Remove all isolated worktrees, their branches, and any processes running on isolated ports.

## Instructions

1. **Check current status** first:
```bash
./scripts/check_ports.sh
```

2. **Run cleanup** (with preview):
```bash
./scripts/cleanup_worktrees.sh --dry-run
```

3. **Run cleanup** (for real):
```bash
./scripts/cleanup_worktrees.sh
```

4. **Verify** everything is clean:
```bash
git worktree list
ls trees/
./scripts/check_ports.sh
```

## What Gets Cleaned

- Processes on ports 3100-3314 (force killed)
- All git worktrees under `trees/`
- All branches matching `*-adw-*`, `feature-issue-*`, `fix-issue-*`
- The `trees/` directory contents
- Git garbage collection
