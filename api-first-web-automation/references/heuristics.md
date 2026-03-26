# Heuristics

## Check These First

- Official docs site
- Developer portal
- Public OpenAPI or Swagger spec
- Help pages that mention import, export, upload, submission, or integration
- Existing product URLs that expose entity ids or form ids

## Good API Signals

- `/api`, `/v1`, `/v2`
- `/docs`, `/developers`, `/developer`
- `swagger`, `openapi`, `redoc`
- Public SDK packages
- Examples using `curl`

## When To Fall Back To UI Automation

- No official API or docs are available
- The action depends on anti-CSRF or opaque browser-only flows
- The endpoint exists but is too unstable or clearly unsupported
- The user specifically wants browser automation

## What To Save

- Direct submission URLs
- Invitation ids, form ids, object ids
- Upload endpoints
- Required headers or request shapes when they are clearly documented
