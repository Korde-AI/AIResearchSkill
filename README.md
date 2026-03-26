# Common Skills

This repository stores reusable Codex skills.

## Structure

- `openreview-submit/`
  OpenReview automation for inspecting submissions, resolving author profile IDs, filling author lists, and batch submission/edit workflows.

- `auto-github/`
  GitHub automation for creating repositories with `gh`, initializing git when needed, attaching `origin`, and pushing local projects safely.

## Usage

Copy a skill folder into `~/.codex/skills/` or keep this repository as a reference collection.

Each skill contains:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/`
- `references/`
