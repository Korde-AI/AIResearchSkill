# myskill

This repository stores reusable agent skills and automation toolkits.

It is designed to work across agents:

- Codex can use each folder as a native skill source.
- Claude Code and other coding agents can read the same folders as reusable playbooks and run the bundled scripts directly.
- The `scripts/` and `references/` folders are agent-agnostic; `SKILL.md` is the Codex-oriented entrypoint.

## Structure

- `openreview-submit/`
  OpenReview automation for inspecting submissions, resolving author profile IDs, filling author lists, and batch submission/edit workflows.

- `auto-github/`
  GitHub automation for creating repositories with `gh`, initializing git when needed, attaching `origin`, and pushing local projects safely.

- `api-first-web-automation/`
  Web-task automation guidance that first searches for official APIs, docs, direct URLs, and likely endpoints before falling back to browser automation.

## Usage

For Codex:

- Copy a skill folder into `~/.codex/skills/`
- Or clone this repo and copy the specific folders you want

For Claude Code or other agents:

- Read the skill folder's `SKILL.md` for the workflow
- Run the scripts in `scripts/`
- Use `references/` as supporting documentation

The repository is intentionally simple so the same folder can be consumed by multiple agents without format conversion.

Each skill contains:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/`
- `references/`
