---
name: openreview-submission-helper
description: Automate OpenReview submission work with API v2. Use when Codex needs to inspect an OpenReview submission, list a user's existing submissions, resolve author profile IDs, fill or correct author lists on existing drafts, or batch-submit/edit papers from local metadata and files.
---

# OpenReview Submission Helper

Use this skill for repeatable OpenReview author-fill and submission-edit work. Prefer the bundled scripts over ad hoc one-off Python snippets.

## Workflow

1. Gather the target.
   Use a forum URL or forum id when updating an existing draft. Use a venue id or invitation id when creating submissions in bulk.

2. Authenticate safely.
   Prefer environment variables:
   - `OPENREVIEW_USERNAME`
   - `OPENREVIEW_PASSWORD`
   - `OPENREVIEW_TOKEN`

   If they are absent and the session is interactive, the scripts will prompt without putting secrets in command arguments.

3. Inspect before editing.
   Run `scripts/openreview_helper.py inspect-submission --forum-id <id>` to confirm:
   - title
   - invitation id
   - current authors and authorids
   - current content keys
   - whether the note is already published

4. Resolve author ids.
   Use one or both:
   - `scripts/openreview_helper.py list-own-notes --signature <tilde-id>` to mine previous submissions for known coauthor ids
   - `scripts/openreview_helper.py search-profiles --name "Author Name"` to find candidate profile ids and institutions

   If a name is ambiguous, do not guess silently. Prefer matching by institution, prior coauthorship context, or an existing submission/history record.

5. Update only allowed fields.
   Run `scripts/openreview_helper.py update-authors --forum-id <id> --signature <tilde-id> --authors-json '[...]' --authorids-json '[...]'`.

   The script fetches the submission invitation, keeps only invitation-allowed content fields, and then updates `authors` and `authorids`. This avoids API errors from system-managed fields like `paperhash`.

6. Batch-submit when needed.
   Use `scripts/batch_submit.py` for CSV, JSON, or JSONL driven submission creation. It uploads attachments with `put_attachment()` and posts notes with `post_note_edit()`.

## Commands

Inspect a draft:

```bash
python ~/.codex/skills/openreview-submission-helper/scripts/openreview_helper.py \
  inspect-submission \
  --forum-id waPs6ngxsI
```

List your existing submissions:

```bash
python ~/.codex/skills/openreview-submission-helper/scripts/openreview_helper.py \
  list-own-notes \
  --signature ~Shenzhe_Zhu1
```

Search author candidates:

```bash
python ~/.codex/skills/openreview-submission-helper/scripts/openreview_helper.py \
  search-profiles \
  --name "Shu Yang" \
  --limit 10
```

Update author list on an existing draft:

```bash
python ~/.codex/skills/openreview-submission-helper/scripts/openreview_helper.py \
  update-authors \
  --forum-id wCvLt1Wauj \
  --signature ~Shenzhe_Zhu1 \
  --authors-json '["Shenzhe Zhu","Shu Yang","Michiel A. Bakker","Alex Pentland","Jiaxin Pei"]' \
  --authorids-json '["~Shenzhe_Zhu1","~Shu_Yang10","~Michiel_Anton_Bakker1","~Alex_Pentland1","~Jiaxin_Pei1"]'
```

Batch-submit from metadata:

```bash
python ~/.codex/skills/openreview-submission-helper/scripts/batch_submit.py \
  --venue-id 'colmweb.org/COLM/2026/Conference' \
  --signature '~Shenzhe_Zhu1' \
  --input-file submissions.jsonl \
  --await-process
```

## Rules

- Never put passwords or tokens directly into command-line arguments if interactive prompting is available.
- Always inspect the submission before editing it.
- Always preserve existing allowed content fields when updating a note.
- Always confirm ambiguous coauthor identities before writing `authorids`.
- Treat `pdf` and supplementary fields according to the venue invitation instead of assuming they are required.

## Resources

- `scripts/openreview_helper.py`: inspect submissions, list prior notes, search profiles, update authors
- `scripts/batch_submit.py`: create submissions in bulk from local metadata
- `references/workflow.md`: quick operational notes and common failure modes
