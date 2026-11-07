# Complete EEE5322 4 × 6 SRAM

This is the completed 24-bit, individually addressed SRAM project in GPDK045,
with native Cadence schematic, symbol, and layout views. The report follows
`Old reference project/Report.pdf`'s I–VII section structure. Author and workload
fields are left blank as requested.

- [Final report (PDF)](../Final_Project_Report.pdf)
- [Editable report (Word)](../Final_Project_Report.docx)
- [Complete layout](../Full_Array_Layout.png)
- [Machine-readable validation summary](results/validation_summary.json)
- [Measured results](results/full_metrics.json)
- [Every address and pattern, both readback scans](results/address_validation.csv)

## Verified results

| Item | Actual result |
| --- | --- |
| Supply / process / nominal temperature | 1.1 V / GPDK045 / TT, 27 °C |
| Array / interface | 4 rows × 6 columns; R1:R0 and C2:C0 |
| Clock | 20 MHz (50 ns); nonoverlapping precharge/access |
| Nominal coverage | 72 writes + 144 reads + 28 protection operations; all pass |
| Nine process/temperature cases | 852 total operations; all pass |
| Extracted-device array replay | 268 operations, including 168 reads; all pass |
| Unit tests | 110 input vectors across eight blocks; all pass |
| Final Spectre jobs | 19; zero errors and warnings |
| Native schematic Check and Save | All 17 cells: zero errors and warnings |
| Full default DRC | All 17 cells: zero violations, 562 checks per cell |
| LVS | All 17 cells MATCH; top circuit has 371 MOS transistors |
| Complete layout | 131.84 × 42.05 µm = 5543.872 µm² |
| Bitcell layout | 2.12 × 1.68 µm = 3.5616 µm² |
| Poly / preferred metal orientation | Vertical poly; M2 H, M3 V, M4 H, M5 V, M6 H, M7 V |

Nominal 50%-to-50% delays, measured with a 5 ps maximum simulation timestep:

| Path | Delay (ns) |
| --- | ---: |
| CLK1 → stored Q, write 1 | 0.4152 |
| CLK1 → stored Q, write 0 | 0.2187 |
| CLK1 → DOUT, read 1 | 0.3693 |
| CLK1 → DOUT, read 0 | 0.3859 |
| Precharge 10% → 90% | 0.1181 |

Timing uses a schematic fixture with 20 fF per physical bitline, 5 fF per global
bitline, and 10 fF output load. The extracted replay verifies the actual extracted
transistor topology and device geometry, with intrinsic device capacitances and
10 fF output load. It does **not** contain interconnect RC and is not presented as
full RC post-layout timing. The top layout uses conservative hierarchical routing;
it is the smallest of four generated shelf arrangements, not a global area optimum.

## Architecture and operation

`cadence/` is library **sram_project**, with 17 cells. Open **sram_4x6** for the
complete schematic, symbol, or layout. The nine top-level instances are control,
row decoder, column decoder, precharge bank, column mux, write driver, bit array,
sense amplifier, and output holding latch. The 6T widths are PU/access/PD =
120/240/360 nm, L = 45 nm. The compact bitcell follows the supplied layout image.

CLK2 high precharges both bitlines to VDD; access occurs on CLK1 high after
CLK2 falls. WR and RD are exclusive in normal operation. An interlock disables
access during clock overlap, simultaneous WR/RD, and unused column codes 110/111.
DOUT holds the last valid read value outside reads; its value before the first
read is unspecified. Input addresses/data settle before access and remain stable.
The explicit mixed pattern is **100110101001011001110010**, row-major:
`100110 / 101001 / 011001 / 110010`. Logical address is `6*row+column`.

## Evidence locations

- `results/physical/<cell>/`: streamed GDS, full DRC summary, LVS reports,
  extracted SPICE, comparison CDL, tool logs, `checks.json`.
- [Top DRC](results/physical/sram_4x6/drc_summary.txt),
  [top LVS](results/physical/sram_4x6/lvs_report.txt.cls),
  [top GDS](results/physical/sram_4x6/layout.gds).
- `results/array_tt_27/`: all-pattern run, all 24 storage pairs checked each cycle.
- Eight other `results/array_<corner>_<temperature>/` folders: mixed pattern,
  all addresses and protection tests. FF/SS/TT at 27 °C; FS/SF at 27 °C;
  TT at −40/125 °C; FF at −40 °C; SS at 125 °C.
- `results/array_timing/`: unstrobbed 5 ps maximum-step timing run.
- `results/array_extracted_tt_27/`: actual extracted array replay, with a final
  all-address read scan after protection tests; no storage initialization forces.
- `results/unit_*/`: exhaustive logic/decoder/control cases and six differential
  sense-amplifier cases (including both polarities at 100 mV difference).
- `results/figures/`: native Cadence screenshots, all 24-cell waveforms, readback
  matrices, required delta markers, block waveforms, and verification output.
- `netlists/native.cdl`: connectivity exported from actual saved native schematics;
  this independent export is the source for LVS.
- `netlists/design.scs`: transistor-level schematic simulation hierarchy.
- `netlists/extracted_design.scs`: conversion of the actual extracted flat circuit.
- `results/evidence_sha256.json`: hashes of submitted evidence and native views.

## Open and reproduce locally

Launch Virtuoso from this folder, or from the repository root using its `cds.lib`.
The checked-in native cellviews can be opened directly. GPDK045 and the licensed
EDA installations remain external dependencies under `/apps/cds/`.

```bash
cd full_array
source ../sram_cell/scripts/local_env.sh
virtuoso &

# Rerun validation, plots, screenshots, and reports using saved native views:
bash scripts/run_project.sh

# Also regenerate the native schematics, symbols, and layouts first:
bash scripts/run_project.sh --rebuild
```

The rebuild uses the validated compact layout in sibling `sram_cell/cadence/`.
It does not require the old reference library. All results already exist; rerunning
requires local Cadence licenses. Three independent physical/simulation jobs run at
once. Python uses `/apps/anaconda/bin/python`; report/GDS processing additionally
needs `gdstk`, `python-docx`, `Pillow`, and `reportlab==4.2.5` in the ignored sibling
`sram_cell/.python_packages/` cache. Base numpy/scipy/matplotlib come from Anaconda.
Install missing report dependencies with the environment's pip using
`--target ../sram_cell/.python_packages`; do not shadow base numpy with a newer ABI.

The model resolver honors `SRAM_MODEL_FILE`, then the supplied instruction folder,
then the installed GPDK model. Generated simulation decks contain their execution
paths; regenerate after moving the checkout. Root `cds.lib` paths are relative.

ASCII PSF waveforms are preserved locally for ViVA. Git stores lossless `.gz`
copies to keep individual files below normal Git hosting limits. To restore one:

```bash
gzip -dk results/array_tt_27/psf/tran.tran.tran.gz
```

Python analysis reads compressed waveforms directly when an uncompressed file is
absent. `scripts/package_evidence.py` creates the compressed files and hash manifest.
The exploratory sizing generator and its ranking are retained for traceability;
exploratory runs are excluded from the final 19-run validation summary.
