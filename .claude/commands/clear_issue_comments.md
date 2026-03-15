---
description: Delete all comments from a GitHub issue to prepare for re-run
---

Delete all comments from GitHub issue #$ARGUMENTS.

Run the following command and show the output:

```bash
./scripts/clear_issue_comments.sh $ARGUMENTS
```

If the issue number is missing, remind the user: usage is `/clear_issue_comments <issue-number>`.
