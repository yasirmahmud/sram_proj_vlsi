#!/usr/bin/env bash
# Recreate the final 4x6 implementation and all submitted evidence locally.
set -euo pipefail
cd "$(dirname "$0")/.."
source ../sram_cell/scripts/local_env.sh
py=/apps/anaconda/bin/python
mkdir -p results netlists cadence
"$py" scripts/design.py
if [[ "${1:-}" == --rebuild ]]; then
 dbAccess -load scripts/setup_library.il > results/setup_library.log 2>&1
 "$py" scripts/native.py
 virtuoso -nograph -nocdsinit -replay scripts/build_native_generated.il -log results/build_native.cds.log > results/build_native.log 2>&1
 "$py" scripts/layout.py
 dbAccess -load scripts/build_layout_generated.il > results/build_layout.log 2>&1
fi
"$py" scripts/physical.py > results/physical_all.log 2>&1
"$py" scripts/simulate_array.py --corners > results/simulations.log 2>&1
for name in array_tt_27 array_ff_-40 array_ss_125 array_fs_27 array_sf_27 array_tt_-40 array_tt_125 array_ff_27 array_ss_27; do
 "$py" scripts/analyze_array.py "$name"
done
"$py" scripts/unit_tests.py > results/unit_tests.log 2>&1
"$py" scripts/timing.py > results/timing.log 2>&1
"$py" scripts/postlayout_array.py > results/postlayout.log 2>&1
"$py" scripts/figures.py > results/figures.log 2>&1
"$py" scripts/screenshots.py > results/screenshots_run.log 2>&1
"$py" scripts/audit.py | tee results/audit.log
"$py" scripts/report.py > results/report.log 2>&1
"$py" scripts/package_evidence.py
