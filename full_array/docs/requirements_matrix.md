# EEE5322 requirement-to-evidence mapping

Source: supplied **Project Instruction Files/Final Project Slides.pdf**, Fall 2026.
Report sections follow **Old reference project/Report.pdf**, with new measurements.
Names and workload contributions are intentionally blank at the user's request.

| Assignment requirement | Implementation and saved evidence |
| --- | --- |
| Four rows, six columns; every bit individually addressed | `cadence/bit_array`, `cadence/sram_4x6`; report II and III.F |
| 45 nm process | GPDK045 MOS models; all MOS L = 45 nm; `netlists/design.scs` |
| SRAM sizing avoids write failure and destructive reads | PU/access/PD = 120/240/360 nm; report III.A and V.B; companion `../../sram_cell/SRAM_Cell_Report.pdf` |
| Primitive schematics, symbols, and layouts | Native `inv`, `nand2`, `nand3`, `and3`, `tg`; report Fig. 3 and `../cadence/` |
| Two row address bits and three column address bits | Top symbol R1:R0, C2:C0; report Fig. 16 |
| Unused column codes 110/111 select none | Eight-vector column unit test; 16 invalid-address operations per array case; `../results/unit_column_decoder/unit_checks.json` |
| Precharge both bitlines to VDD | Three PMOS per pair, six pairs; report Figs. 9–10; `precharge_all_bitlines_min_V` in measured metrics |
| Read/write circuitry with exclusive commands | Actual transistor interlock and transmission-gate driver; report III.E; 64 unit control vectors |
| CLK1 at least 10 MHz; CLK2 precharge | 20 MHz, 50 ns period, nonoverlapping clocks; report V.A and complete-array waveform |
| Differential sense amplifier | 5T OTA plus output inverter; six measured voltage pairs including ±100 mV; report Figs. 13–14 |
| Write/read ones from all 24 bits | 24 writes and two 24-address read scans; report Fig. 20 and `../results/address_validation.csv` |
| Write/read zeros from all 24 bits | 24 writes and two 24-address read scans; report Fig. 21 and address CSV |
| Explicit random sequence at all 24 bits | `100110101001011001110010`; report Fig. 22 and address CSV |
| Nondestructive read proof | Two read scans per pattern; all 48 storage nodes checked after every operation; report Fig. 23 and `../results/array_tt_27/checks.json` |
| Four delta markers using 50%-to-50% rule | CLK1→Q writes and CLK1→DOUT reads, both values; 5 ps max step; report Fig. 25 |
| Explain timing and simulation setup | Report V.A–D; actual source decks in `../netlists/` |
| Screenshots: bitcell, sense amp, decoders, R/W, full array | Native Cadence exports in `../results/figures/`; report III and VI |
| Full-array DRC and LVS clean | All 562 default DRC checks: zero violations; LVS MATCH; actual tool output in report Fig. 26 and `../results/physical/sram_4x6/` |
| Compact layout and actual final area | 131.84 × 42.05 µm = 5543.872 µm²; chosen from four shelf packings; report VI |
| Single orientation poly | Actual top GDS geometry audit: all vertical; `../results/validation_summary.json` |
| Preferred metal orientations | M2/M4/M6 horizontal, M3/M5/M7 vertical; geometry audit; local M1 contacts |
| Work distribution and challenges | Report IV: blank name/contribution fields, actual circuit/layout challenges described |
| Word report submitted as PDF | `../../Final_Project_Report.docx` and matching `../../Final_Project_Report.pdf` |
| Validate physical circuit | Additional extracted 371-MOS replay: 268 operations, 168 reads, all pass; intrinsic devices only, no interconnect RC |
| Reproducible local EDA work | `../scripts/run_project.sh`, raw logs, compressed PSF, hashes, and native views |

The required nominal array case is supplemented by eight process/temperature
cases. Nineteen final Spectre jobs and 101 evidence checks pass. The supplied old
report's ground-short waiver is not used in this project.
