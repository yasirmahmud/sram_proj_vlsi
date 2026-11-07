#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/local_env.sh
py=/apps/anaconda/bin/python
# Rebuild resets the generated cellviews to the documented implementation.
if [[ "${1:-}" == --rebuild ]]; then
 dbAccess -load scripts/build_cadence.il > results/build_cadence.log 2>&1
 virtuoso -nograph -nocdsinit -replay scripts/finalize_native.il -log results/finalize_native.log > results/finalize_native.stdout 2>&1
 dbAccess -load scripts/build_layout.il > results/build_layout.log 2>&1
fi
for cell in sram_cell sram_cell_default; do
 strmout -library sram_cell -topCell "$cell" -view layout -strmFile "results/$cell.gds" -logFile "results/streamout_$cell.log" > "results/streamout_$cell.stdout" 2>&1
 scripts/pegasus_drc.sh "$cell"
 scripts/pegasus_lvs.sh "$cell"
done
"$py" scripts/simulate.py > results/simulate.log 2>&1
"$py" scripts/postlayout.py > results/postlayout.log 2>&1
"$py" scripts/analyze.py > results/analysis.log 2>&1
"$py" scripts/extra_plots.py > results/extra_plots.log 2>&1
"$py" scripts/render_layout.py > results/layout_render.log 2>&1
"$py" scripts/validate_results.py
xvfb-run -a -s '-screen 0 1920x1200x24' virtuoso -nocdsinit -replay scripts/screenshots.il -log results/screenshots.cds.log > results/screenshots.stdout 2>&1
"$py" scripts/report.py
