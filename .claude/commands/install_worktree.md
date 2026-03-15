---
description: Setup an isolated git worktree for parallel ADW execution
---

# Install Worktree

Setup an isolated git worktree for a given ADW ID. This allows multiple ADWs to run in parallel without git conflicts.

## Instructions

1. **Get the ADW ID** from the user or generate one with `python -c "import uuid; print(uuid.uuid4())"`

2. **Create the worktree** using the Python module:

```bash
uv run -c "
import sys
sys.path.insert(0, 'adws')
from adw_modules.worktree_ops import create_isolated_environment
from adw_modules.branching import create_branch_name

adw_id = '$ARGUMENTS'
branch = create_branch_name(adw_id, 'isolated-workspace')
result = create_isolated_environment(adw_id, branch, skip_deps=False)
if result:
    print(f'Worktree: {result[\"worktree_path\"]}')
    print(f'Studio port: {result[\"studio_port\"]}')
    print(f'WC port: {result[\"web_components_port\"]}')
    print(f'AEM port: {result[\"aem_libs_port\"]}')
else:
    print('Failed to create worktree')
"
```

3. **Verify the setup** by checking:
   - `trees/<adw_id>/` exists
   - `trees/<adw_id>/.ports.env` has correct ports
   - `trees/<adw_id>/apps/mas/node_modules/` exists (if deps installed)

4. **Copy MCP configuration** if needed:
   - Copy `.mcp.json` from project root to worktree root
   - Update any paths in the MCP config to point to worktree

5. **Start dev servers** for the worktree:
```bash
./scripts/start_worktree.sh <adw_id> all
```

6. **Check port status**:
```bash
./scripts/check_ports.sh
```

## Port Allocation

Each worktree gets 3 deterministic ports (up to 15 concurrent):
- **Studio**: 3100-3114
- **Web-Components**: 3200-3214
- **AEM/Libs**: 3300-3314

## Cleanup

Remove a single worktree:
```bash
./scripts/purge_tree.sh <adw_id>
```

Remove all worktrees:
```bash
./scripts/cleanup_worktrees.sh
```
