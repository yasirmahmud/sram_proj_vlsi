#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/local_env.sh
cell="${1:-sram_cell}"
case "$cell" in sram_cell) out=results/drc;; sram_cell_default) out=results/default_drc;; *) exit 2;; esac
mkdir -p "$out"
sed -e "s|\"CELLNAME.gds\"|\"results/$cell.gds\"|" -e "s|\"CELLNAME\"|\"$cell\"|" -e "s|\"CELLNAME.db\"|\"$out/sram_cell.db\"|" /apps/cds/local/GPDK045/pvs/pvlDRC.rul > "$out/run.pvl"
/apps/cds/pegasus251/tools/bin/pegasus -drc -log "$out/pegasus.log" "$out/run.pvl" > "$out/stdout.log" 2>&1
cp result.sum "$out/summary.txt"
rg -q 'Total DRC Results +: 0 \(0\)' "$out/summary.txt"
