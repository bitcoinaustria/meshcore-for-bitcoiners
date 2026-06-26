# MeshCore for Bitcoiners

A LaTeX **Beamer** presentation — a Bitcoin Austria talk drawing the structural
parallels between **Bitcoin** and **MeshCore** (LoRa mesh networking), and
honestly naming where each analogy breaks.

Built with the [Bitcoin Austria beamer style](https://github.com/bitcoinaustria/latex-beamer-style-2026),
included here as a **git submodule** at `theme/`.

> ## ⚠️ This repo uses a git submodule — you must check it out
>
> The theme lives in `theme/` as a submodule. A plain `git clone` leaves it
> **empty**, and the build fails with a missing-package error
> (`theme/bitcoin-austria.sty not found`). Do one of:
>
> ```bash
> # when cloning:
> git clone --recurse-submodules git@github.com:bitcoinaustria/meshcore-for-bitcoiners.git
>
> # or, in an existing clone:
> git submodule update --init --recursive
> ```

## Build

Requires **XeLaTeX** + `latexmk` (and `inkscape` only if you add SVG figures to
`pix/`). From the repo root:

```bash
make            # -> meshcore-for-bitcoiners.pdf
make view       # build and open
make watch      # continuous rebuild
make clean      # remove build artifacts
```

`make` checks that the submodule is present and gives a clear hint if it isn't.

## Releases

Pushing a tag matching `v*` triggers CI to build the PDF and publish it as a
**GitHub Release** (`.github/workflows/release.yml`):

```bash
git tag v1.0 && git push origin v1.0
```

Every push/PR to `main` also builds the PDF and uploads it as a CI artifact
(`.github/workflows/build.yml`).

## Layout

```
meshcore-for-bitcoiners.tex   the deck (entry point)
theme/                        submodule: Bitcoin Austria beamer style
pix/                          figures (PNG/PDF; or SVG, auto-converted)
generate-images/              uv project: AI image generation (fal.ai + Replicate)
makefile                      build / view / watch / clean
.github/workflows/            CI: build on push, release on tag
handoff-20260626.md           brainstorm notes the talk is based on
SPECS.md                      project specs
```

## Content

`meshcore-for-bitcoiners.tex` is a working **draft** developed from
`handoff-20260626.md`. The talk-specific `\bridgeslide{title}{bitcoin}{meshcore}{where-it-breaks}`
macro (a thin wrapper over the theme's `\comparisonslide`) is defined in the
deck preamble.

## License

Presentation content: © Bitcoin Austria. The beamer theme and the Blinker font
are licensed in the [theme repository](https://github.com/bitcoinaustria/latex-beamer-style-2026).
