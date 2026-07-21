#!/usr/bin/env bash
# Build the arXiv source submission (LaTeX + figures) from PAPER.md.
# arXiv requires TeX source, not a compiled PDF, and compiles with pdfLaTeX.
# Output: arxiv/{main.tex,fig1.png,fig2.png,fig3.png} and arxiv-submission.tar.gz
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf arxiv && mkdir -p arxiv

# Standalone LaTeX. The glyph header (scripts/arxiv-header.tex) declares every
# non-ASCII character via newunicodechar so the source compiles under pdfLaTeX.
pandoc PAPER.md -s -o arxiv/main.tex \
  -H scripts/arxiv-header.tex \
  -V documentclass=article -V geometry:margin=1in -V fontsize=11pt \
  -V colorlinks=true -V linkcolor=blue -V urlcolor=blue

# Flatten figure paths (arXiv is case-sensitive; flat names are safest).
cp runs/judge_panel/panel_single_vs_loo.png   arxiv/fig1.png
cp runs/judge_panel/panel_self_preference.png arxiv/fig2.png
cp runs/final/forest_mcq_abstention.png       arxiv/fig3.png
sed -i '' \
  -e 's#runs/judge_panel/panel_single_vs_loo.png#fig1.png#' \
  -e 's#runs/judge_panel/panel_self_preference.png#fig2.png#' \
  -e 's#runs/final/forest_mcq_abstention.png#fig3.png#' \
  arxiv/main.tex

# Optional local compile check (tectonic; arXiv itself uses pdfLaTeX).
if command -v tectonic >/dev/null 2>&1; then
  ( cd arxiv && tectonic main.tex >/dev/null 2>&1 && rm -f main.pdf ) \
    && echo "local tectonic compile OK" || echo "WARNING: local compile failed"
fi

# Source-only tarball with files at the archive root.
( cd arxiv && tar --disable-copyfile -czf ../arxiv-submission.tar.gz \
    main.tex fig1.png fig2.png fig3.png )
echo "wrote arxiv-submission.tar.gz:"; tar -tzf arxiv-submission.tar.gz
