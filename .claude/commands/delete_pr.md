---
description: Close a GitHub PR and optionally delete its branch
---

Close GitHub PR $ARGUMENTS.

Run the following command:

```bash
./scripts/delete_pr.sh $ARGUMENTS
```

The script will show PR details and prompt for confirmation before closing. Pass `--delete-branch` as the second argument to also delete the branch.

If the PR number is missing, remind the user: usage is `/delete_pr <pr-number> [--delete-branch]`.
