---
allowed-tools: Bash
description: Rebase current branch from either main (for mas) or stage/upstream (for milo)
argument-hint: [mas|milo]
model: haiku
---

# Purpose

This command performs a git rebase operation for the specified project type. For `mas` projects, it rebases from the `main` branch. For `milo` projects, it rebases from the `stage/upstream` branch. The command handles error cases and provides clear feedback to the user about the rebase status.

## Variables

PROJECT: $1

## Instructions

- Accept a single argument specifying which project type to rebase: `mas` or `milo`
- Always navigate to the `apps/$PROJECT` directory before running any git commands
  - For `mas`: `cd apps/mas`
  - For `milo`: `cd apps/milo`
- For `mas`, rebase from the `main` branch
- For `milo`, rebase from the `stage/upstream` branch
- Check that the git repository is in a clean state before attempting rebase
- Fetch the latest changes from the remote before rebasing
- Handle rebase conflicts gracefully with instructions for user resolution
- Provide clear status messages throughout the process
- Ensure the rebase completes successfully before returning to the user

## Workflow

1. Validate that the user provided either 'mas' or 'milo' as the argument
2. Change directory to apps/$PROJECT (either apps/mas or apps/milo)
3. Check git repository state and verify it's clean
4. Fetch latest changes from the remote repository
5. Determine the base branch based on the project type:
   - `mas` → rebase from `main`
   - `milo` → rebase from `stage/upstream`
6. Perform the git rebase operation
7. If rebase conflicts occur, provide instructions for resolving them
8. Report the final status to the user

## Report

Return a clear status message indicating:
- Whether the rebase was successful
- If conflicts occurred and what the user should do to resolve them
- The current branch state after the rebase operation
