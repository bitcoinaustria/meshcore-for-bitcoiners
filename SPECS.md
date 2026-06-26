# MeshCore for Bitcoiners — Project Specs

> Living spec. Reflects the current architecture (theme extracted to a shared
> submodule).

## What this is

A **LaTeX Beamer** presentation, **"MeshCore for Bitcoiners"** — a Bitcoin
Austria talk on the structural parallels between Bitcoin and MeshCore (LoRa
mesh networking), naming where each analogy breaks. English content.

- Output: a PDF deck, built in CI, released on git tags.
- Content basis: `handoff-20260626.md` (brainstorm notes).

## Repositories (both under the `bitcoinaustria` GitHub org)

| Repo | Visibility | Role |
|------|-----------|------|
| `meshcore-for-bitcoiners` | private | **this** talk (content + build/CI) |
| `latex-beamer-style-2026` | public  | the reusable **Bitcoin Austria beamer theme** |

The theme is included here as a **git submodule** at `theme/`. The talk repo is
private; the theme repo is public, so CI can pull the submodule with no extra
auth.

> Cloning requires the submodule: `git clone --recurse-submodules …` or
> `git submodule update --init --recursive`. See README / CLAUDE.md.

## The theme (`theme/` submodule)

`latex-beamer-style-2026` implements the Bitcoin Austria 2026 brand:

- Palette: red `#E3000F`, black `#222222`, light grey `#ECECEC`, white
  (exact codes from `Bitcoin Austria Branding.pdf`).
- Typeface: **Blinker** (SIL OFL 1.1), shipped in the theme, loaded via fontspec.
- Dark logomark top-left, running short-title centre, frame number top-right.
- Bold dark headlines + short red accent rule. **Rectangular (sharp) blocks.**
- Macros: `\comparisonslide` (two-column compare + callout), `\fillerslide`
  (dark topic-divider with the light logomark).
- `bitcoin-austria.sty` is **self-locating** (`\CurrentFilePath`), so it finds
  its own fonts/assets wherever the submodule is mounted.

The talk loads it with `\usepackage{theme/bitcoin-austria}` and defines a
talk-specific `\bridgeslide{title}{bitcoin}{meshcore}{where-it-breaks}` wrapper
in its preamble.

## Build

- Engine: **XeLaTeX** via `latexmk` (Blinker needs fontspec). Build from repo root.
- `make` (build), `make view`, `make watch`, `make clean`. `make` checks the
  submodule is present.
- Figures in `pix/` may be SVG; the makefile converts them to PDF
  (inkscape / rsvg-convert). CI installs inkscape + xvfb for this.

## CI / Releases (GitHub Actions)

- `build.yml`: push/PR to `main` → checkout (`submodules: recursive`) → install
  TeX → `make build` → upload PDF artifact.
- `release.yml`: tag `v*` → build → `softprops/action-gh-release` attaches the
  PDF to a GitHub Release.

## AI images (`generate-images/`)

A `uv` project (`fal-client` + `replicate`). `generate_image.py` targets both
fal.ai and Replicate, writes a `.json` metadata sidecar per image. Keys via env
`FAL_AI` / `REPLICATE_API`.

## Status / decisions

- [x] Entry point: `meshcore-for-bitcoiners.tex`.
- [x] Engine: XeLaTeX.
- [x] Brand: Bitcoin Austria 2026 (Blinker + palette), via shared submodule theme.
- [x] Topology: per-talk repo + shared theme submodule; both in `bitcoinaustria` org.
- [x] Tag scheme: `v*`.
- [ ] Final content / slide order (current `.tex` is a draft from the handoff).
- [ ] Verify the EU 868 MHz duty-cycle figure before stating it on stage.
- [ ] Real figures/images in `pix/`.
