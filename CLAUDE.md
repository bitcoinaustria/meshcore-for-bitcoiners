# CLAUDE.md — MeshCore for Bitcoiners

A LaTeX Beamer presentation (Bitcoin Austria). English content.

## ⚠️ Git submodule — check it out first

The beamer theme is a **git submodule** at `theme/`
(`bitcoinaustria/latex-beamer-style-2026`). Nothing builds without it.

```bash
git submodule update --init --recursive
```

If `theme/bitcoin-austria.sty` is missing, that's the cause. `make` checks for
it and prints this hint.

## Build

- Engine: **XeLaTeX** via `latexmk` (the theme loads the Blinker font with
  `fontspec` — pdflatex will not work). Build from the **repo root**.
- `make` (build), `make view`, `make watch`, `make clean`.
- Output: `meshcore-for-bitcoiners.pdf` (gitignored — it's a release artifact).

## Structure

- `meshcore-for-bitcoiners.tex` — the deck. Loads `\usepackage{theme/bitcoin-austria}`.
- `theme/` — the Bitcoin Austria style (submodule). Provides the brand, plus
  `\comparisonslide` and `\fillerslide`. Edit the **theme repo** to change the
  brand; edit the `.tex` to change this talk.
- `\bridgeslide{title}{bitcoin}{meshcore}{where-it-breaks}` is talk-specific and
  defined in the deck preamble (wraps `\comparisonslide`).
- `pix/` — figures. SVGs are auto-converted to PDF by the makefile
  (inkscape / rsvg-convert).
- `generate-images/` — a `uv` project for AI image generation (fal.ai +
  Replicate). Run with `uv run`; API keys via env `FAL_AI` / `REPLICATE_API`.

## Writing style

- **Bold the load-bearing phrase in every bullet.** Wrap the words the audience
  should remember in `\textbf{...}` so each slide is skimmable from the back of
  the room. The bold phrase is the takeaway; the rest is supporting prose.
- **One highlight per bullet, not five.** Bolding everything emphasises nothing —
  pick the single key phrase. Use `\emph{...}` (italics) for a lighter, secondary
  stress (a caveat, an "honest flaw" aside), and reserve `\textbf` for the point.
- **Keep comparison columns parallel.** On `\bridgeslide` / `\comparisonslide`,
  bold the matching phrase on *both* the Bitcoin and MeshCore sides so the two
  columns read as a pair (e.g. `costly` ↔ `free`, `permanent ledger` ↔
  `only as transmitted`).
- **One idea per bullet.** Don't join two distinct thoughts with a semicolon —
  split them into separate bullets (this applies to the "where it breaks" notes
  too).

## Releases

Tag `v*` → CI builds the PDF and creates a GitHub Release. Push/PR to `main`
builds the PDF as a CI artifact. CI checks out submodules (`submodules: recursive`).

Latest: **v1.1** (2026-06-29). Record every release in `CHANGELOG.md` — it's a
changelog for the *slides* (what changed on stage), so update it whenever you
cut a tag.

## Notes

- The deck is a **draft** based on `handoff-20260626.md`; develop further.
- There is a `TODO` in the throughput section: verify the exact EU 868 MHz
  duty-cycle figure before stating a number on stage.
- Don't commit the built PDF or LaTeX aux files (see `.gitignore`).
