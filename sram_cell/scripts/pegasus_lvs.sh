#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/local_env.sh
cell="${1:-sram_cell}"
case "$cell" in sram_cell) out=results/lvs;; sram_cell_default) out=results/default_lvs;; *) exit 2;; esac
mkdir -p "$out"
SRAM_CELL_NAME="$cell" dbAccess -load scripts/export_schematic.il > "$out/export_schematic.log" 2>&1
cat > "$out/run.pvl" <<PVL
layout_path "results/$cell.gds" gdsii;
layout_primary "$cell";
schematic_path "netlists/$cell.cdl" spice;
schematic_primary "$cell";
lvs_report_file "$out/report.txt";
lvs_write_netlist -layout "$out/compared_layout.cdl";
include "/apps/cds/local/GPDK045/pvs/pvlLVS.rul"
PVL
cp /apps/cds/local/GPDK045/pvs/pvs_control_file ./pvs_control_file
/apps/cds/pegasus251/tools/bin/pegasus -lvs -spice "$out/extracted.spice" -log "$out/pegasus.log" "$out/run.pvl" > "$out/stdout.log" 2>&1
cp result.sum "$out/summary.txt"
rg -q 'Run Result +: +MATCH' "$out/report.txt.cls"
