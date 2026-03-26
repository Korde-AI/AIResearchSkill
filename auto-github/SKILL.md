---
name: github-repo-publisher
description: Create GitHub repositories and push local projects with the GitHub CLI. Use when Codex needs to initialize git for a local directory, create a new GitHub repo with `gh repo create`, attach or verify remotes, commit changes, and push safely without destructive git operations.
---

# GitHub Repo Publisher

Use this skill when the user wants a repeatable workflow for turning a local folder into a GitHub repository or pushing an existing git project to GitHub.

## Workflow

1. Inspect local git and GitHub auth state.
   Run `scripts/github_repo_publish.py inspect --source-dir <dir>`.

2. Create or attach the remote.
   Run `scripts/github_repo_publish.py create-repo --source-dir <dir> --repo <owner/name> [--public|--private] [--description "..."] [--topics a,b,c]`.

3. Commit and push.
   Run `scripts/github_repo_publish.py push --source-dir <dir> --message "<commit message>"`.

4. If the remote already exists, do not overwrite history.
   Reuse `origin` when it already points to the requested repository. If it points elsewhere, stop and make the user choose.

## Commands

Inspect:

```bash
python ~/.codex/skills/github-repo-publisher/scripts/github_repo_publish.py \
  inspect \
  --source-dir /path/to/project
```

Create a repository and set `origin`:

```bash
python ~/.codex/skills/github-repo-publisher/scripts/github_repo_publish.py \
  create-repo \
  --source-dir /path/to/project \
  --repo ShenzheZhu/my-project \
  --public \
  --description "Reusable AI agent skills and automation workflows." \
  --topics ai,agents,automation,codex,developer-tools
```

Commit and push:

```bash
python ~/.codex/skills/github-repo-publisher/scripts/github_repo_publish.py \
  push \
  --source-dir /path/to/project \
  --message "Initial commit"
```

## Rules

- Prefer `gh auth status` instead of assuming GitHub CLI is ready.
- Never use destructive commands like `git reset --hard` or force-push unless the user explicitly asks.
- If the directory is not a git repo, initialize it with `git init -b main`.
- If the repo has no commits, create a normal initial commit before pushing.
- If `origin` already exists and does not match the requested remote, stop instead of rewriting it silently.
- When creating a public repo, prefer setting a clear GitHub description and 3-8 relevant topics.

## Resources

- `scripts/github_repo_publish.py`: inspect, create a GitHub repo, and push
- `references/workflow.md`: quick reference for common repo creation and push cases
