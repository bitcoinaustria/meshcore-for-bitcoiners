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
- `make` (build 16:9), `make view`, `make watch`, `make clean`.
- **Two aspect ratios, one source:** `make` builds 16:9
  (`meshcore-for-bitcoiners-16x9.pdf`); `make pdf-43` builds 4:3
  (`meshcore-for-bitcoiners-4x3.pdf`); `make both` builds both (what CI/release
  ship). The ratio is parameterised by `\baAspect` (default `169`); the 4:3
  build injects `\def\baAspect{43}` via `latexmk -usepretex`. Don't edit the
  `\documentclass` to switch — use the make targets. Both PDFs are gitignored
  release artifacts.
- **4:3 is the regression canary:** it's narrower, so slide overflow shows there
  first. The theme auto-scales typography on narrow formats (tighter lists +
  gentle paperwidth-driven heading/body scale), so dense slides fit on their
  own. For a slide that's *still* too dense at 4:3, use the theme's
  `\narrowonly{<code>}` escape hatch (e.g. `\narrowonly{\small}`) — a no-op at
  16:9. (Don't add a deck-side body nudge on top — it double-shrinks.)

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
- The EU 868 MHz duty-cycle figure is **verified** (2026-06-29): **10%** on the
  869.4–869.65 MHz "P" sub-band, up to 500 mW ERP — the deck states this. Sources
  in the throughput-section comment in the `.tex` and in `handoff-20260626.md`.
  (Still worth a final sanity-check against the current AT national frequency plan
  before stage.)
- Don't commit the built PDF or LaTeX aux files (see `.gitignore`).
