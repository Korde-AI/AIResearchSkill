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

**Priority 3 — Tighten spacing and captions**
- Reduce `\vspace` values by 1–2 pt where multiple explicit vspace commands appear in sequence.
- Shorten figure/table captions by removing redundant preamble ("The figure shows..." → directly state the content).

**Priority 4 — Structural moves (last resort)**
- Move a paragraph or subsection to the appendix only if the main text still makes sense without it and the appendix is explicitly labeled as such.
- Do not move content to appendix without telling the user.

### Step 3 — Verify and compile

```bash
latexmk -pdf -interaction=nonstopmode -quiet main.tex
pdfinfo main.pdf | grep Pages
pdftotext -f <target_page> -l <target_page> main.pdf - | tail -10
```

Confirm that the conclusion (or last main section) ends on or before the target page.

### Step 4 — Push

```bash
git stash && git pull --rebase && git stash pop
git add <changed_files>
git commit -m "<description>"
git push
```

## Hard Rules

These rules must never be violated regardless of how much space is needed.

- **Never change `[H]` to `[t]` (or any other float specifier)** on tables or figures. `[H]` placement is intentional. Find prose savings instead.
- **Never delete content without user approval.** Syntactic compression is always preferred over deletion. If a cut is necessary beyond pure syntax, ask the user first.
- **No em dashes (`---`) in authored prose.** Use commas, semicolons, or restructure. Exception: verbatim quotes from external sources (system prompts, code) must be preserved exactly.
- **Do not restore previously deleted content** without explicit user instruction.
- **Do not change numerical claims, statistics, or citation keys** while tightening prose.

## Estimating savings

| Technique | Typical saving |
|-----------|---------------|
| Merge two 1-line sentences into one | ~1 line |
| Remove a "For instance..." example sentence | ~1.5–2 lines |
| Merge 3-sentence paragraph into 2 | ~1–2 lines |
| Tighten one `\vspace` by 3 pt | ~0.3 lines |
| Shorten a caption by one clause | ~0.5–1 line |

## Pitfalls

- **Merge conflicts on pull**: Overleaf may push changes concurrently. Always `stash → pull --rebase → stash pop` before committing. Resolve conflicts by taking upstream additions plus your prose changes.
- **Float reflow**: Changing prose length can cause figures to reflow and shift the page break. Always recompile and re-check the target page after every edit batch.
- **Duplicate sections**: After structural moves, check with `grep -n "\\section{" main.tex` to ensure no section appears twice.
- **Wrong figure paths**: After a pull that adds new figures, paths may use the wrong prefix (e.g., `colm/figure/` instead of `figure/`). Fix immediately or the build will fail.
