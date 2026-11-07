# GPDK045 SRAM cell

Completed single-bit SRAM design and local EDA validation. Start with
[SRAM_Cell_Report.pdf](SRAM_Cell_Report.pdf) or the editable
[Word report](SRAM_Cell_Report.docx).

## Design

- Native Cadence library: `cadence/`, library name `sram_cell`.
- Cell `sram_cell`: six MOSFETs, L = 45 nm; PMOS pull-up W = 120 nm,
  NMOS access W = 240 nm, NMOS pull-down W = 360 nm; VDD = 1.1 V.
- Cell `sram_cell_default`: assignment baseline, all widths 120 nm.
- Both cells contain `schematic`, `symbol`, and `layout` views.
- Ports: `BL BL_bar WL Q Q_bar Vdd GND`. Q/Q_bar are observation ports.
- Layout boundary: 2.120 × 1.680 µm (3.5616 µm²), including standalone taps.
- Both schematics: Check and Save, 0 errors / 0 warnings.
- Both layouts: 562 default GPDK045 DRC checks, zero results; LVS MATCH.

Open Virtuoso from `project_file/` using its `cds.lib`, or from this folder.
The PDK is `/apps/cds/local/GPDK045/gpdk045`. Tool environment:

```bash
cd project_file/sram_cell
source scripts/local_env.sh
virtuoso
```

## Measured validation

The final audit passes 104 checks; all 94 Spectre runs finish with zero errors
and zero warnings.

- Write 1 / write 0: approximately 45.65 / 35.99 ps, BL-to-Q at 50% VDD.
- Diagnostic forced-node read 1 / read 0: 1.633 ns / 63.62 ps, Q-to-BL,
  20 fF bitline load, 50% crossings.
- Physical nondestructive-read test: 10110010 at 50 MHz; both bitlines
  precharged to VDD, write drivers disconnected during read.
- All 15 TT/FF/SS/FS/SF × −40/27/125 °C combinations pass at 1.1 V.
- The actual extracted device topology passes the physical sequence.
- Read SNM: 223.58 mV. Assignment write two-VTC square margin: 513.57 mV.
- Supply and deterministic gate-offset sweeps include all required points.
  The no-offset 90%-rail boundary lies between 0.33 V and 0.34 V for this
  stimulus and sampling criterion.

`results/metrics.json` contains exact values and individual state assertions;
`results/reliability.csv` contains the supply/offset classifications.
`results/validation_summary.json` records the final automated audit.
Waveforms are PSF ASCII under each `results/<test>/psf/`, with the matching
Spectre logs. All decks are in `netlists/` and figures in `results/figures/`.

This is a single-cell deliverable. Array decoders, sense amplifier, and
full-array validation are outside this folder's implemented scope.
Extracted-device simulations include device geometry and layout-dependent
parameters, but not extracted wiring RC. Read delays depend on the stated
20 fF load. Gate-offset sweeps are deterministic, not Monte Carlo yield.

## Reproduce

```bash
bash scripts/run_all.sh
```

This reruns local Spectre simulations, both physical checks, assertions,
plots, and reports. It requires the local Cadence license server.
`bash scripts/run_all.sh --rebuild` also regenerates the native cellviews
from the documented reference topology and the new layout generators.
This option replaces the generated views, so preserve manual edits first.

Python uses `/apps/anaconda/bin/python` for NumPy/SciPy/Matplotlib. The local
`.python_packages/` contains GDS, Word, and PDF rendering dependencies.
The report generator loads those dependencies after system plotting modules
so it does not replace the installed scientific Python environment.

## Evidence

- `results/drc/summary.txt`, `results/default_drc/summary.txt`: clean DRC.
- `results/lvs/report.txt.cls`, `results/default_lvs/report.txt.cls`: LVS MATCH.
- `results/finalize_native.log`: native schematic checks.
- `results/layout_render.log`: all 42 poly rectangles vertical.
- `results/sram_cell.gds`, `results/sram_cell_default.gds`: streamed layouts.
- `netlists/sram_cell.cdl`: exported from the native schematic.
- `netlists/sram_cell_extracted.scs`: converted actual Pegasus extraction.
- `netlists/native_schematic.scs`: Cadence-generated CDF reference netlist.

The supplied `Project files/gpdk045_mos.scs` is used directly and matches the
installed PDK model byte for byte. The unrelated 180 nm `nmos.scs` is unused.
The old schematic and sizing informed this design; its report's results are
not reused as validation evidence. The compact placement follows the user-provided reference image. Local routing
was adapted, horizontal poly replaced with Metal2, and standalone taps and ports
were added. The revised layouts were revalidated for this deliverable. DRC uses the installed default PVL deck; optional DFM,
density, and antenna decks are separate checks.
