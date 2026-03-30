---
name: latex-page-reduction
description: Reduce page count in a LaTeX conference paper to meet a strict page limit. Use when a paper exceeds the allowed page count and the conclusion or main content overflows the last permitted page.
---

# LaTeX Page Reduction

Use this skill to trim a LaTeX paper to a hard page limit (e.g., 9 pages for COLM/ICLR/ICML) without losing content integrity.

## Goal

Conclusion and all main content must end on or before the target page. References and appendix may follow freely.

## Workflow

### Step 1 — Measure the overflow

```bash
latexmk -pdf -interaction=nonstopmode -quiet main.tex
pdfinfo main.pdf | grep Pages
pdftotext -f <target_page> -l <target_page+1> main.pdf - | grep -v "^$"
```

Count exactly how many lines overflow past the target page. This determines how aggressively to cut.

To confirm the final section (e.g., Conclusion) lands on the target page:

```bash
pdftotext -f <target_page> -l <target_page> main.pdf - | grep -A8 "Conclusion"
```

### Step 2 — Apply reductions in priority order

Work through the priority list below, stopping as soon as the paper fits. Do not skip to aggressive cuts when light cuts suffice.

**Priority 1 — Syntactic tightening (no content loss)**
- Merge two short sentences into one without dropping any information.
- Replace wordy constructions: "in order to" → "to", "the fact that" → "that", "it is important to note that" → drop entirely.
- Combine parallel lists expressed in separate sentences.
- Remove transitional filler: "Taken together,", "As mentioned above,".

**Priority 2 — Remove redundant elaboration**
- Remove inline examples that restate a point already made abstractly (e.g., a "For instance..." sentence after a general claim).
- Remove a sentence whose content is already implied by the surrounding paragraph.
- Do NOT remove any finding, result, citation, or claim that stands on its own.

**Priority 3 — Tighten spacing**
- Add or increase negative vspace before section headers and after figures: `\vspace{-9pt}` before `\section{}` is typical.
- Do not add negative vspace inside a paragraph or before a `\finding` that would create visible gaps.
- Shorten figure/table captions by removing redundant preamble ("The figure shows..." → directly state the content).

**Priority 4 — Structural moves (last resort)**
- Move a paragraph or subsection to the appendix only if the main text still makes sense without it and the appendix is explicitly labeled as such.
- Do not move content to appendix without telling the user.

### Step 3 — Special case: `[H]` table on the target page

When a `[H]` table occupies most of the target page and leaves insufficient room for the concluding section:

- **Do NOT change `[H]` to `[t]` or any other specifier.** This is a hard rule.
- Instead, trim prose in the sections that appear *before* the table on the target page to free up lines for the conclusion below it.
- If the table itself is the last item on the page and the conclusion follows, ensure the conclusion source appears *before* the `\begin{table}` in the `.tex` file only if the table float is allowed to move; otherwise trim prose.

### Step 4 — Verify and compile

```bash
latexmk -pdf -interaction=nonstopmode -quiet main.tex
pdfinfo main.pdf | grep Pages
pdftotext -f <target_page> -l <target_page> main.pdf - | tail -10
```

Confirm that the conclusion (or last main section) ends on or before the target page.

### Step 5 — Push

```bash
git stash && git pull --rebase && git stash pop
git add <changed_files>
git commit -m "<description>"
git push
```

If push is rejected (non-fast-forward), run:

```bash
git pull --rebase && git push
```

## Hard Rules

These rules must never be violated regardless of how much space is needed.

- **Never change `[H]` to `[t]` (or any other float specifier)** on tables or figures. `[H]` placement is intentional. Find prose savings instead.
- **Never delete content without user approval.** Syntactic compression is always preferred over deletion. If a cut is necessary beyond pure syntax, ask the user first.
- **No em dashes in authored prose.** This includes both the LaTeX form `---` and the Unicode character `—` (U+2014). Use commas, semicolons, or restructure. Exception: verbatim quotes from external sources (system prompts, code) must be preserved exactly.
- **Do not restore previously deleted content** without explicit user instruction.
- **Do not change numerical claims, statistics, or citation keys** while tightening prose.

## Detecting em dashes

Both forms must be checked — `---` and the Unicode character `—`:

```bash
grep -n "\-\-\-\|—" main.tex | grep -v "^[^%]*%"
```

Then inspect each match: if it is inside a verbatim quote (tcolorbox, `\texttt`, quoted system prompt), leave it. If it is in authored prose, replace it.

## Estimating savings

| Technique | Typical saving |
|-----------|---------------|
| Merge two 1-line sentences into one | ~1 line |
| Remove a "For instance..." example sentence | ~1.5–2 lines |
| Merge 3-sentence paragraph into 2 | ~1–2 lines |
| Add `\vspace{-9pt}` before a section header | ~0.3–0.5 lines |
| Shorten a caption by one clause | ~0.5–1 line |

## Pitfalls

- **Merge conflicts on pull**: Overleaf may push changes concurrently. Always `stash → pull --rebase → stash pop` before committing. Resolve conflicts by taking upstream additions plus your prose changes, then recompile to verify page count is still correct.
- **Float reflow**: Changing prose length can cause figures to reflow and shift the page break. Always recompile and re-check the target page after every edit batch.
- **Duplicate sections**: If a section is moved in the source, check for duplicates with `grep -n "\\\\section{" main.tex`. A section appearing twice will render twice and waste pages.
- **Wrong figure paths after pull**: After a pull that adds new figures, paths may use the wrong prefix (e.g., `colm/figure/` instead of `figure/`). Fix immediately or the build will fail silently with a missing-file error.
- **`[H]` reverting after pull**: If you previously changed a float specifier and the upstream reverts it, do not fight it. Adapt by trimming prose instead.
