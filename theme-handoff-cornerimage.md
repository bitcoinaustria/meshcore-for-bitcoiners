# Handoff: graduate `\cornerimage` into the Bitcoin Austria beamer theme

**To:** maintainer of [`bitcoinaustria/latex-beamer-style-2026`](https://github.com/bitcoinaustria/latex-beamer-style-2026) (the `theme/` submodule)
**From:** `meshcore-for-bitcoiners` deck
**Status:** a deck-local interim version ships now (PR #10); this proposes moving it into the theme.

---

## TL;DR

The deck added a small helper, `\cornerimage[width]{image}`, that floats a
little image into a slide's **top-right corner** — even on theme-generated
slides (`\comparisonslide`, `\fillerslide`, …) where you can't inject frame
content. It's a **generic presentation utility**, so it belongs in the theme
next to `\comparisonslide` / `\fillerslide` / `\fullbleedslide`, not in the
talk. Crucially, **only the theme knows where its logo / title band sit**, so
only the theme can place a corner image that's guaranteed not to collide with
the brand furniture.

## Why it exists

The deck wanted a small chip photo in the corner of an *existing*
`\bridgeslide` (a thin wrapper over the theme's `\comparisonslide`). That macro
emits a whole `frame`, so there's no way to add an overlay from the call site.
The trick: `eso-pic`'s starred foreground hook paints only the **next** shipped
page, so calling the helper immediately before a slide macro decorates exactly
that slide — without the theme's cooperation.

## Current deck-local implementation (the starting point)

```latex
\usepackage{eso-pic}
% Float a small image into the next slide's top-right corner. Call right BEFORE
% a slide macro (\comparisonslide, \fillerslide, \begin{frame}{...}).
%   \cornerimage[width]{image}     % optional arg = width (default ~2 cm)
\newcommand{\cornerimage}[2][0.13\paperwidth]{%
  \AddToShipoutPictureFG*{%
    \put(\LenToUnit{\dimexpr\paperwidth-#1-0.035\paperwidth\relax},%
         \LenToUnit{\dimexpr\paperheight-#1-0.045\paperheight\relax}){%
      \includegraphics[width=#1,keepaspectratio]{#2}}}}
```

Usage in the deck:

```latex
\cornerimage{sx1262}
\bridgeslide{Purpose-built silicon, for opposite reasons}{...}{...}{...}
```

## What the theme version should improve

The deck version positions blind (fixed offsets from the page edge). The theme
can do better because it owns the layout:

1. **Logo / title-safe placement.** Position the corner image relative to the
   theme's actual top-right element (brand logo?) and title band, so it never
   overlaps them. If the theme already paints a top-right logo via its own
   `eso-pic` / headline template, define a safe anchor below/beside it.
2. **Corner choice.** Add an optional placement key, e.g.
   `\cornerimage[corner=top-right, width=0.13\paperwidth]{img}` with
   `top-right` (default), `top-left`, `bottom-right`, `bottom-left`. A
   `keyval`/`pgfkeys` interface fits the theme's style.
3. **Brand margins.** Reuse whatever margin lengths the theme already defines
   instead of the hard-coded `0.035\paperwidth` / `0.045\paperheight`.
4. **Compose with the theme's own foreground.** `\AddToShipoutPictureFG*` is
   additive per page, so it should stack with a theme logo overlay — but please
   verify it doesn't get cleared/overwritten by the theme's headline machinery.
5. **Optional niceties (nice-to-have):** a thin frame/padding option, an
   optional caption, and an `\cornerimage*` variant that persists on a run of
   slides rather than just the next one.

## Requirements / dependencies

- Load **`eso-pic`** in the theme `.sty` (it's in `texlive-latex-extra`, which
  the deck's CI already installs).
- `\LenToUnit` and `\AddToShipoutPictureFG*` come from `eso-pic`.
- Works under **XeLaTeX** (the theme's engine). Raster images (JPEG/PNG) are
  fine via `graphicx`.

## Acceptance checklist

- [ ] `\cornerimage` defined in the theme; builds under XeLaTeX.
- [ ] Image lands clear of the logo and title on a `\comparisonslide`, a
      `\fillerslide`, and a plain `frame`.
- [ ] Only the intended slide is decorated (the next shipped page), not the one
      after.
- [ ] Optional `corner=` placement works for all four corners.
- [ ] Graphics path: resolves bare image names like the theme's other graphics.

## Migration once the theme ships it

1. Bump the `theme/` submodule in `meshcore-for-bitcoiners` to the new version.
2. Remove the deck-local `\cornerimage` definition **and** the `\usepackage{eso-pic}`
   line from `meshcore-for-bitcoiners.tex` (the theme now provides both).
3. Keep the call sites unchanged (e.g. `\cornerimage{sx1262}` before the ASIC
   `\bridgeslide`) — same name, same first-arg semantics, so nothing else moves.
4. Rebuild; confirm the SX1262 corner image still renders correctly.

> Keep the public signature `\cornerimage[width]{image}` backward-compatible so
> the deck's existing call keeps working without edits.
