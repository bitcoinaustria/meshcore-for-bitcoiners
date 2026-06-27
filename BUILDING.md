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
make            # -> meshcore-for-bitcoiners.pdf
make view       # build and open
make watch      # continuous rebuild
make clean      # remove build artifacts
```

`make` checks that the submodule is present and prints a clear hint if it isn't.
The built `meshcore-for-bitcoiners.pdf` is a release artifact and is
**gitignored** — don't commit it (nor the LaTeX aux files).

## Releases

Pushing a tag matching `v*` triggers CI to build the PDF and publish it as a
**GitHub Release** (`.github/workflows/release.yml`):

```bash
git tag v1.0 && git push origin v1.0
```

Every push / PR to `main` also builds the PDF and uploads it as a CI artifact
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

The `generate-images/` directory is a `uv` project for AI image generation
(fal.ai + Replicate); run with `uv run`, with API keys via the `FAL_AI` /
`REPLICATE_API` environment variables.
