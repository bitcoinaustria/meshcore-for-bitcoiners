# MeshCore for Bitcoiners — build the presentation.
#
# Requires the Bitcoin Austria beamer style in ./theme (git submodule):
#   git submodule update --init --recursive
#
# Content figures in pix/ may be authored as SVG; they are converted to PDF
# before the build (inkscape, or rsvg-convert as a fallback).
#
# Two aspect ratios share one source (the .tex parameterises the documentclass
# via \baAspect, default 169):
#   make        / make build  -> meshcore-for-bitcoiners.pdf      (16:9, default)
#   make pdf-43               -> meshcore-for-bitcoiners-4x3.pdf  (4:3)
#   make both                 -> both of the above (used by CI / release)

NAME    := meshcore-for-bitcoiners
TEX     := $(NAME).tex
PDF     := $(NAME).pdf       # 16:9 (default)
PDF_43  := $(NAME)-4x3.pdf   # 4:3

# pix/*.svg -> pix/*.pdf
SVGS    := $(wildcard pix/*.svg)
SVG_PDFS := $(SVGS:.svg=.pdf)

# Pick an available SVG converter.
INKSCAPE := $(shell command -v inkscape 2>/dev/null)
RSVG     := $(shell command -v rsvg-convert 2>/dev/null)

LATEXMK := latexmk -xelatex -interaction=nonstopmode -halt-on-error

.PHONY: all build both pdf-43 clean clean-all view view-43 watch check-theme

all: build

check-theme:
	@test -f theme/bitcoin-austria.sty || { \
	  echo "ERROR: theme/bitcoin-austria.sty is missing."; \
	  echo "Run: git submodule update --init --recursive"; \
	  exit 1; }

# 16:9 — the default build, fast for iteration.
build: check-theme $(SVG_PDFS)
	$(LATEXMK) $(TEX)
	@echo "Built $(PDF) (16:9)"

# 4:3 — same source, aspect ratio injected via -usepretex (\baAspect=43).
# A separate -jobname keeps its aux files from colliding with the 16:9 build.
pdf-43: check-theme $(SVG_PDFS)
	$(LATEXMK) -jobname=$(NAME)-4x3 -usepretex='\def\baAspect{43}' $(TEX)
	@echo "Built $(PDF_43) (4:3)"

# Ship both ratios (release artifacts).
both: build pdf-43

# SVG -> PDF (vector). inkscape preferred; rsvg-convert as fallback.
pix/%.pdf: pix/%.svg
ifdef INKSCAPE
	$(INKSCAPE) --export-type=pdf --export-filename=$@ $<
else ifdef RSVG
	$(RSVG) -f pdf -o $@ $<
else
	@echo "ERROR: no SVG converter (install inkscape or rsvg-convert) for $<"; exit 1
endif

view: build
	@xdg-open $(PDF) >/dev/null 2>&1 || open $(PDF) 2>/dev/null || echo "Open $(PDF) manually"

view-43: pdf-43
	@xdg-open $(PDF_43) >/dev/null 2>&1 || open $(PDF_43) 2>/dev/null || echo "Open $(PDF_43) manually"

watch: check-theme $(SVG_PDFS)
	latexmk -xelatex -pvc -interaction=nonstopmode $(TEX)

clean:
	latexmk -c $(TEX)
	latexmk -c -jobname=$(NAME)-4x3 $(TEX)
	rm -f $(NAME).nav $(NAME).snm $(NAME).vrb \
	      $(NAME)-4x3.nav $(NAME)-4x3.snm $(NAME)-4x3.vrb build.log

clean-all: clean
	latexmk -C $(TEX)
	latexmk -C -jobname=$(NAME)-4x3 $(TEX)
	rm -f $(SVG_PDFS)
