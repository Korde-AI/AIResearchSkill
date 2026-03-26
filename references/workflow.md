# OpenReview Workflow Notes

## Auth

- Prefer `OPENREVIEW_TOKEN` when available.
- Otherwise use `OPENREVIEW_USERNAME` and `OPENREVIEW_PASSWORD`.
- If no credentials are present and stdin is a TTY, prompt interactively.

## Existing Draft Updates

- Fetch the current note.
- Fetch the note's invitation.
- Keep only fields present in `invitation.edit.note.content`.
- Update `authors` and `authorids`.
- Repost with `post_note_edit()`.

This avoids errors caused by system fields such as `paperhash`.

## Author Resolution

- Search the author's name with `search_profiles(term=...)`.
- Use institution history and prior coauthor context to disambiguate.
- When available, mine the user's past submissions to recover known `authorids`.

## Batch Submission

- Use API v2.
- Upload local files with `put_attachment()`.
- Post the note with `post_note_edit()`.
- Default invitation is `<venue-id>/-/Submission` unless explicitly overridden.
