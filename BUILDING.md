# Building & developing

The technical companion to the [README](README.md): how to clone, build, and
release **MeshCore for Bitcoiners**.

## ⚠️ This repo uses a git submodule — check it out first

The beamer theme lives in `theme/` as a **git submodule**
([`latex-beamer-style-2026`](https://github.com/bitcoinaustria/latex-beamer-style-2026)).
A plain `git clone` leaves it **empty**, and the build fails with a
missing-package error (`theme/bitcoin-austria.sty not found`). Do one of:

```bash
# when cloning:
git clone --recurse-submodules git@github.com:bitcoinaustria/meshcore-for-bitcoiners.git

# or, in an existing clone:
git submodule update --init --recursive
```

## Build

Requires **XeLaTeX** + `latexmk` — the theme loads the Blinker font via
`fontspec`, so pdfLaTeX will **not** work. `inkscape` (or `rsvg-convert`) is only
needed if you add SVG figures to `pix/`. From the repo root:

```bash
make            # -> meshcore-for-bitcoiners.pdf      (16:9, default)
make pdf-43     # -> meshcore-for-bitcoiners-4x3.pdf  (4:3)
make both       # both ratios (what CI / release builds)
make view       # build and open the 16:9 PDF
make watch      # continuous rebuild (16:9)
make clean      # remove build artifacts
```

`make` checks that the submodule is present and prints a clear hint if it isn't.
The built PDFs are release artifacts and are **gitignored** — don't commit them
(nor the LaTeX aux files).

### Two aspect ratios from one source

The deck ships in **16:9** (widescreen, default) and **4:3** (legacy
projectors). Both come from the same `.tex`: the documentclass aspect ratio is
parameterised by `\baAspect` (default `169`), and the 4:3 build just injects
`\def\baAspect{43}` via `latexmk -usepretex` under a separate `-jobname` (so the
two builds' aux files don't collide). You never edit the source to switch — use
the make targets above.

Building both is also a cheap **regression check on the theme**: 4:3 is the
narrower canvas, so anything that overflows a slide edge shows up there first.
The theme **auto-scales typography on narrow formats** (tighter lists + a gentle
paperwidth-driven heading/body scale) so dense slides fit without deck-side
fuss. If a slide is *still* too dense on 4:3, reach for the theme's
`\narrowonly{<code>}` escape hatch (e.g. `\narrowonly{\small}`), which runs
`<code>` only on narrow formats and is a no-op at 16:9.

## Releases

Pushing a tag matching `v*` triggers CI to build **both PDFs** (16:9 + 4:3) and
publish them as a **GitHub Release** (`.github/workflows/release.yml`):

```bash
git tag v1.0 && git push origin v1.0
```

Every push / PR to `main` also builds both PDFs and uploads them as CI artifacts
(`.github/workflows/build.yml`). CI checks out submodules recursively.

Record every release in [`CHANGELOG.md`](CHANGELOG.md) — it's a changelog for the
*slides* (what changed on stage), so update it whenever you cut a tag.

## Repo layout

```
meshcore-for-bitcoiners.tex   the deck (entry point)
theme/                        submodule: Bitcoin Austria beamer style
pix/                          figures (PNG/PDF; or SVG, auto-converted)
generate-images/              uv project: AI image generation (fal.ai + Replicate)
makefile                      build / view / watch / clean
.github/workflows/            CI: build on push, release on tag
CHANGELOG.md                  per-release log of what changed on stage
handoff-20260626.md           brainstorm notes the talk is based on
SPECS.md                      project specs
```

## Deck internals

`meshcore-for-bitcoiners.tex` is a working **draft** developed from
`handoff-20260626.md`. Two talk-specific helpers are defined in the preamble:

- `\bridgeslide{title}{bitcoin}{meshcore}{where-it-breaks}` — a Bitcoin-vs-MeshCore
  comparison with a "where the analogy breaks" callout (a thin wrapper over the
  theme's `\comparisonslide`).
- `\screenshotcard[width]{image}{caption}` — a captioned phone-screenshot card.

The theme auto-scales typography on narrow (4:3-class) formats, so dense slides
generally fit without intervention. For the rare slide that's still too dense at
4:3, the theme exports `\narrowonly{<code>}` (e.g. `\narrowonly{\small}`) — runs
`<code>` only on narrow formats, a no-op at 16:9.

The `generate-images/` directory is a `uv` project for AI image generation
(fal.ai + Replicate); run with `uv run`, with API keys via the `FAL_AI` /
`REPLICATE_API` environment variables.
