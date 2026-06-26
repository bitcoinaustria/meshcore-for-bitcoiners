# MeshCore for Bitcoiners — build the presentation.
#
# Requires the Bitcoin Austria beamer style in ./theme (git submodule):
#   git submodule update --init --recursive
#
# Content figures in pix/ may be authored as SVG; they are converted to PDF
# before the build (inkscape, or rsvg-convert as a fallback).

NAME    := meshcore-for-bitcoiners
TEX     := $(NAME).tex
PDF     := $(NAME).pdf

# pix/*.svg -> pix/*.pdf
SVGS    := $(wildcard pix/*.svg)
SVG_PDFS := $(SVGS:.svg=.pdf)

# Pick an available SVG converter.
INKSCAPE := $(shell command -v inkscape 2>/dev/null)
RSVG     := $(shell command -v rsvg-convert 2>/dev/null)

.PHONY: all build clean clean-all view watch check-theme

all: build

check-theme:
	@test -f theme/bitcoin-austria.sty || { \
	  echo "ERROR: theme/bitcoin-austria.sty is missing."; \
	  echo "Run: git submodule update --init --recursive"; \
	  exit 1; }

build: check-theme $(SVG_PDFS)
	latexmk -xelatex -interaction=nonstopmode -halt-on-error $(TEX)
	@echo "Built $(PDF)"

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

watch: check-theme $(SVG_PDFS)
	latexmk -xelatex -pvc -interaction=nonstopmode $(TEX)

clean:
	latexmk -c $(TEX)
	rm -f $(NAME).nav $(NAME).snm $(NAME).vrb build.log

clean-all: clean
	latexmk -C $(TEX)
	rm -f $(SVG_PDFS)
