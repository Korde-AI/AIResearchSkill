# Workflow Notes

## Inspect

- Check `gh auth status`
- Check whether `.git/` exists
- Check current branch
- Check remotes
- Check worktree status

## Create Repo

- Initialize git when missing
- Default branch is `main`
- Use `gh repo create <owner/name> --source . --remote origin`
- Use `--push` only when the user already wants an immediate first push and the worktree is committed

## Push

- Stage intended files
- Create a commit if there are staged or tracked changes
- Push `HEAD` to `origin/<current-branch>`
- Set upstream on first push

## Guardrails

- Stop on remote mismatch
- Stop on missing `gh` auth
- Avoid changing remotes unrelated to the requested repo
