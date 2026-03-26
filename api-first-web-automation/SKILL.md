---
name: api-first-web-automation
description: Discover official APIs, docs, direct URLs, and likely endpoints before using browser or UI automation. Use when a user asks Codex to perform a website task and it is not yet clear whether the site exposes an API, upload endpoint, form action, or documented workflow that is more reliable than clicking through the UI.
---

# API-First Web Automation

Use this skill whenever a task might require web automation. Default rule: try to find a stable API or direct endpoint first, and use browser automation only if API or documented URLs are unavailable or insufficient.

## Workflow

1. Identify the target domain and task.
   Extract:
   - product/site name
   - target domain
   - action: upload, submit, search, create, delete, export, login, etc.

2. Generate candidate docs and endpoints.
   Run:

```bash
python ~/.codex/skills/api-first-web-automation/scripts/api_candidates.py \
  --url https://example.com \
  --task "submit a paper"
```

3. Check official docs first.
   Look for:
   - `/api`
   - `/docs`
   - `/developers`
   - `/developer`
   - `/swagger`
   - `/openapi.json`
   - `/redoc`
   - help center pages that mention API, SDK, webhook, import, upload, or integration

4. Prefer stable transport over UI clicks.
   In descending order:
   - official public API
   - official SDK or CLI
   - documented direct form/upload endpoint
   - existing authenticated HTTP calls already visible in the product
   - browser automation

5. Use browser automation only as fallback.
   If no reliable API exists, then proceed with UI automation. While doing so, still record:
   - final working URLs
   - upload/submit forms
   - any network endpoints discovered during the process

## Rules

- Do not assume a site lacks an API just because the user asked for automation.
- Prefer primary documentation and first-party domains.
- If the task is repetitive, save the discovered endpoint or workflow in the relevant project skill or repo.
- If authentication or CSRF makes direct HTTP calls risky, document the limitation and fall back to browser automation.
- If a web app obviously uses JSON/XHR calls for the target action, inspect those before scripting the UI.

## Outputs

For each task, produce a short discovery result:

- target domain
- candidate docs URLs
- candidate API URLs
- recommended execution path
- fallback UI path if needed

## Resources

- `scripts/api_candidates.py`: generate likely docs/API URLs and search queries from a domain
- `references/heuristics.md`: quick heuristics for deciding API first vs UI first
