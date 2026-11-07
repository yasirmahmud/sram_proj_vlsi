#!/apps/anaconda/bin/python
"""Build matching editable Word and PDF reports from measured evidence."""
from pathlib import Path
import json,sys,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parent
sys.path.insert(0,str(REPO/'sram_cell/.python_packages'))
from PIL import Image as PILImage
from docx import Document
from docx.shared import Inches,Pt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape
M=json.loads((ROOT/'results/full_metrics.json').read_text()); A=json.loads((ROOT/'results/validation_summary.json').read_text())
assert A['pass']
F=ROOT/'results/figures'; blocks=[]; number=0

def h(s):blocks.append(('heading',s))
def p(s):blocks.append(('paragraph',s))
def table(rows):blocks.append(('table',rows))
def page():blocks.append(('page',None))
def fig(name,caption,height=6.5):
 global number
 number+=1;blocks.append(('figure',(F/name,f'Fig. {number}. {caption}',height)))
def native(c,caption):
 fig(c+'_schematic.png',caption+' Schematic.',3.4)
 fig(c+'_layout.png',caption+' Layout.',2.9)
def panel(names,labels,out,cols=2):
 rows=(len(names)+cols-1)//cols
 f,aa=plt.subplots(rows,cols,figsize=(14,4.2*rows),squeeze=False)
 for ax in aa.flat:ax.axis('off')
 for ax,name,label in zip(aa.flat,names,labels):
  ax.imshow(PILImage.open(F/name));ax.set_title(label,fontsize=12)
 f.tight_layout();f.savefig(F/out,dpi=170,bbox_inches='tight');plt.close(f)

panel(['inv_schematic.png','inv_layout.png','nand2_schematic.png','nand2_layout.png','nand3_schematic.png','nand3_layout.png','and3_schematic.png','and3_layout.png'],['Inverter schematic','Inverter layout','NAND2 schematic','NAND2 layout','NAND3 schematic','NAND3 layout','AND3 schematic','AND3 layout'],'primitive_views.png')
panel(['bitcell_schematic.png','bitcell_symbol.png','bitcell_layout.png'],['6T schematic','Hierarchical symbol','Compact layout'],'bitcell_views.png')
panel(['row_decoder_schematic.png','row_decoder_symbol.png','row_decoder_layout.png'],['2-to-4 schematic','Row symbol','Row layout'],'row_views.png')
panel(['column_decoder_schematic.png','column_decoder_symbol.png','column_decoder_layout.png'],['3-to-6 schematic','Column symbol','Column layout'],'column_views.png')
panel(['precharge_unit_schematic.png','precharge_unit_layout.png','precharge_schematic.png','precharge_layout.png'],['Three-PMOS precharge/equalizer','Unit layout','Six bitline pairs','Bank layout'],'precharge_views.png')
panel(['rw_control_schematic.png','rw_control_layout.png','write_driver_schematic.png','write_driver_layout.png'],['Clock/command interlock','Control layout','Differential write driver','Write-driver layout'],'rw_views.png')
panel(['sense_amp_schematic.png','sense_amp_layout.png','read_latch_schematic.png','read_latch_layout.png'],['Differential OTA and buffer','Sense amplifier layout','Read holding latch','Latch layout'],'sense_views.png')
panel(['column_mux_schematic.png','column_mux_layout.png'],['Six differential transmission-gate selections','Column multiplexer layout'],'mux_views.png')
# Architecture is drawn from the actual nine top-level instances.
f,ax=plt.subplots(figsize=(13,6));ax.set(xlim=(0,13),ylim=(0,6));ax.axis('off')
from matplotlib.patches import Rectangle
for x,y,w,hh,txt in [(0.2,4.6,3,1,'CTRL: clocks + WR/RD\nvalid-column interlock'),(4.1,4.6,3,1,'PRE: six precharge\n+ equalization units'),(.2,2.4,3,1,'ROW: R[1:0] → WL[3:0]'),(4.1,2.2,4.3,1.5,'MEM: 4 rows × 6 columns\n24 six-transistor cells'),(.2,.3,3,1,'COL: C[2:0] → CS[5:0]'),(4.1,.3,4.3,1,'MUX: BL[5:0] / BLB[5:0]\n→ GBL / GBLB'),(9.1,.3,3.6,1,'WRITE: DIN / DINB'),(9.1,2.4,3.6,1,'SENSE: OTA + buffer'),(9.1,4.6,3.6,1,'LATCH → DOUT')]:
 ax.add_patch(Rectangle((x,y),w,hh,fc='#e9f2fa',ec='#23577c',lw=1.5));ax.text(x+w/2,y+hh/2,txt,ha='center',va='center',fontsize=10)
for a,b in [((3.2,2.9),(4.1,2.9)),((5.6,4.6),(5.6,3.7)),((6.2,2.2),(6.2,1.3)),((3.2,.8),(4.1,.8)),((9.1,.8),(8.4,.8)),((8.4,.9),(10.7,2.4)),((10.7,3.4),(10.7,4.6))]:ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',lw=1.6))
f.tight_layout();f.savefig(F/'architecture.png',dpi=170);plt.close(f)

blocks.append(('title','Design, Simulation, and Layout of a 4 × 6 SRAM Array in 45 nm CMOS Technology'))
p('EEE5322 • Fall 2026 • University of Florida')
p('Authors: __________________________________________________________')
p('Abstract—A 24-bit individually addressable SRAM was implemented with GPDK045 CMOS at 1.1 V using native Cadence Virtuoso schematic, symbol, and layout views. The circuit integrates 371 MOS transistors and operates at 20 MHz. All 24 cells pass write-one, write-zero, and mixed-pattern readback; repeated reads preserve the stored data. Nine process/temperature cases pass 852 schematic-level operations, and a device-extracted netlist passes a further 268 operations. Nominal 50%-to-50% write-one/write-zero delays are 0.4152/0.2187 ns; read-one/read-zero delays are 0.3693/0.3859 ns. All 17 implemented cells and blocks have zero DRC violations and matching LVS. The complete layout measures 131.84 × 42.05 µm, or 5543.872 µm².')
p('Index Terms—SRAM, 6T bitcell, decoder, precharge, differential sense amplifier, GPDK045, Spectre, DRC, LVS.')
h('I. INTRODUCTION')
p('The EEE5322 assignment requires four rows and six columns with individually addressed bits [1]. A pair of cross-coupled CMOS inverters stores each bit, and two access devices connect it to complementary bitlines. The project includes the transistor design, reusable logic cells, memory peripherals, full-array simulation, physical layout, and independent layout verification. This report follows the section structure of the supplied reference report [5]; its measurements and verification results come from the new 4 × 6 implementation.')
h('II. DESIGN OVERVIEW')
p('R1:R0 selects one of four rows. C2:C1:C0 selects columns 0–5; 110 and 111 select no column. The logical address used in the validation tables is a = 6r + c, with r = 2R1 + R0 and c = 4C2 + 2C1 + C0. CLK2 controls precharge; CLK1 enables the requested read or write after precharge ends. DIN is the write input and DOUT is the latched read output. All blocks use explicit VDD and GND connections.')
table([['Interface','Meaning'],['R1, R0 / C2, C1, C0','2 row bits / 3 column bits'],['CLK1 / CLK2','Access clock / active-high precharge phase'],['WR / RD','Exclusive write / read request'],['DIN / DOUT','Single-bit input / held single-bit output'],['VDD / GND','1.1 V supply / explicit ground']])
fig('architecture.png','Architecture of the nine blocks instantiated by sram_4x6.',3.6)
page();h('III. IMPLEMENTATION')
h('A. SRAM Bitcell and Reusable Logic')
p('The 6T cell uses 120 nm PMOS pull-ups, 240 nm NMOS access devices, and 360 nm NMOS pull-downs; all channel lengths are 45 nm. The width ratios PD/access = 1.5 and access/PU = 2 strengthen the pull-down against read disturbance while retaining write ability. A minimum-width all-120 nm baseline is retained in the separate single-cell study. That study measures a nominal read static-noise margin of 223.58 mV for the final sized cell [6]. Full-array nondestructive readback is verified separately here.')
p('The compact layout preserves the supplied arrangement: cross-coupled inverter devices in the center and staggered access devices on either side. Its boundary is 2.12 × 1.68 µm (3.5616 µm²), including explicit body taps. Poly runs vertically; metal interconnect closes the feedback loop. The cell is repeated on a 2.30 × 2.02 µm placement pitch in the array.')
fig('bitcell_views.png','Final bitcell schematic, symbol, and physical layout.',6.0)
page();p('Inverter, NAND2, NAND3, AND3, and transmission-gate cells provide reusable schematic symbols. Series NMOS devices are widened to maintain drive: NAND2 uses 720 nm NMOS; NAND3 uses 1080 nm NMOS. Their PMOS devices and the basic inverter devices are 360 nm. Transmission gates use 1080 nm devices. Every device has L = 45 nm. AND3 is a NAND3 followed by an inverter; the layout contains the same eight transistors.')
fig('primitive_views.png','Primitive schematic and layout views used by the hierarchy.',8.0)
page();h('B. Row Decoder')
p('The enabled 2-to-4 row decoder contains two address inverters and four AND3 minterms. WLr = ROWEN AND the row-address minterm for r. Thus exactly one wordline is high during a valid access, and all wordlines are low during idle, precharge, invalid columns, or conflicting commands. Eight unit vectors cover both enable values and every row address.')
fig('row_views.png','Row decoder native schematic, symbol, and layout.',5.3)
fig('row_decoder_simulation.png','Spectre verification of all row addresses with enable low and high.',3.0)
page();h('C. Column Decoder and Selection')
p('The 3-to-6 column decoder contains three input inverters and six AND3 minterms. CS0–CS5 decode 000–101. No minterm exists for 110 or 111, so both unused addresses produce six low outputs. Each CS controls two transmission gates joining one physical bitline pair to GBL/GBLB. Unit simulation covers all eight codes; array tests exercise both invalid codes on every row for reads and writes.')
fig('column_views.png','Column decoder schematic, symbol, and layout.',5.3)
fig('column_decoder_simulation.png','One-hot selection for columns 0–5 and no selection for 110/111.',3.0)
page();fig('mux_views.png','Differential column multiplexer; six pairs share GBL and GBLB.',5.6)
h('D. Precharge Circuit')
p('Each column has two 1080 nm PMOS devices charging BL and BLB to VDD and a third PMOS equalizing the pair. PCB = NOT CLK2 is the active-low gate signal. All six pairs precharge together before access. Both bitlines approach 1.1 V, as required; they are not biased to half supply. The measured 10%–90% recharge time for a discharged bitline is 0.1181 ns under the stated schematic testbench load.')
fig('precharge_views.png','Precharge unit and six-column precharge bank.',5.3)
page();fig('precharge_timing.png','Actual BL/BLB precharge waveforms and 10%–90% delta marker.',4.0)
h('E. Read/Write Circuitry and Sense Amplifier')
p('The control logic defines VALID = NOT(C2 AND C1), WEN = CLK1 AND WR AND NOT(RD) AND VALID AND NOT(CLK2), and REN = CLK1 AND RD AND NOT(WR) AND VALID AND NOT(CLK2). ROWEN = WEN OR REN. Therefore precharge and access are interlocked, invalid columns disable access, and simultaneous RD/WR commands disable both paths. Normal stimulus keeps RD and WR exclusive; separate fault tests deliberately assert conflicts to verify the hardware protection.')
p('The write driver inverts DIN and uses complementary-enabled transmission gates to drive GBL/GBLB only when WEN is high. It presents high impedance when disabled. The sense amplifier is a five-transistor NMOS differential OTA with a PMOS mirror load, followed by a CMOS output inverter (seven transistors total). The input devices are 240 nm, mirror devices 1440 nm, and tail/output-inverter devices 360 nm. The polarity is DOUT = 1 when BIT exceeds BIT_bar. Six standalone tests include both polarities of a 100 mV difference at common-mode voltages 1.05 V and 0.75 V, as well as rail-to-rail differential inputs.')
page();fig('rw_views.png','Read/write interlock and differential write-driver implementation.',7.0)
fig('write_driver_simulation.png','Fine-resolution write-path simulation for both data values.',2.2)
page();fig('sense_views.png','Sense amplifier and transmission-gate output holding latch.',6.2)
p('The eight-transistor read latch is transparent during REN and holds the last read value otherwise. This prevents the read output from tracking the disabled sense amplifier during writes or precharge. It has no reset input; an initial DOUT value is not specified before the first valid read. Full-array checking begins output comparisons only when a read result is defined.')
fig('sense_amp_simulation.png','All six sense-amplifier input cases resolve to the expected rail.',3.0)
page();h('F. Top Level Array')
p('The top level instantiates CTRL, ROW, COL, PRE, MUX, WRITE, MEM, SENSE, and LATCH. MEM contains 24 six-transistor cells, sharing four horizontal wordlines and six vertical complementary bitline pairs. The complete flattened circuit contains 371 MOS transistors. Observation nets Qr_c and QBr_c are saved for schematic simulation; they do not add transistors or external top-level pins. All native schematics pass Check and Save with zero errors and zero warnings.')
fig('sram_4x6_schematic.png','Complete hierarchical 4 × 6 SRAM schematic.',5.6)
fig('sram_4x6_symbol.png','Top-level interface symbol.',2.6)
page();fig('bit_array_schematic.png','All 24 bitcells in the four-row, six-column memory bank.',4.9)
fig('bit_array_layout.png','Physical memory bank, 20.11 × 11.02 µm.',3.5)
page();h('IV. WORK DISTRIBUTION AND CHALLENGES')
p('Work distribution: __________________________________________________')
p('________________________________________________________________')
table([['Name','Actual contribution'],['',''],['',''],['',''],['','']])
p('The contribution fields are intentionally blank for the submission authors to complete. The main circuit challenge was resolving a small negative differential near VDD at the sense input. The initially explored sizing did not reliably meet the standalone low-output rail criterion for this case. A sizing sweep and repeat simulation led to the final 240 nm input / 1440 nm mirror / 360 nm tail combination. The final six input cases and all array corner cases pass.')
p('The physical-design challenges were preserving explicit ground connectivity, meeting small metal landing-area rules, and routing hierarchical ports without accidental shorts. Directional via landings and separated routing channels resolved these issues. The full default DRC deck is used, and LVS compares extracted devices against a CDL export of the actual saved native schematics. No DRC or LVS waiver is used.')
h('V. SIMULATION RESULTS')
h('A. Testbench and Timing Setup')
p('Spectre 21.1.0.664 runs the supplied GPDK045 BSIM models at VDD = 1.1 V. The main case is TT, 27 °C. A 50 ns period gives 20 MHz, above the 10 MHz requirement. Inputs settle at 0.2–0.3 ns within each cycle; CLK2 rises at 2.0–2.1 ns and falls at 12.0–12.1 ns. CLK1 rises at 20.0–20.1 ns and falls at 40.0–40.1 ns. Thus nominal precharge and access do not overlap. Address and data are held throughout the access.')
p('The schematic fixture adds 20 fF to each of 12 physical bitlines, 5 fF to each global bitline, and 10 fF at DOUT. Initial conditions set storage nodes only at simulation start; they do not force a stored bit during operation. A complete write phase precedes every read phase. Coverage simulations use a maximum 500 ps timestep and 500 ps saved strobes. Every operation checks all 24 Q/Qbar pairs at 37 ns in its cycle with 0.1VDD/0.9VDD rail limits. DOUT is checked on reads, wordlines and selects are checked for proper enabling, and later read scans verify retained data.')
page();h('B. All-Address Functional Validation')
p('At nominal conditions, the sequence writes all 24 ones and reads every address twice, then writes all 24 zeros and reads every address twice, then writes the explicit mixed sequence 100110101001011001110010 and reads every address twice. The mixed rows are 100110 / 101001 / 011001 / 110010. Two scans after each write phase demonstrate repeated nondestructive readback. Every write also checks that all other cells retain their expected states, including unselected cells on an active row.')
table([['Nominal coverage','Count'],['Valid writes: 3 patterns × 24 addresses','72'],['Valid reads: 3 patterns × 24 × 2 scans','144'],['Invalid read/write addresses','16'],['Simultaneous RD/WR faults','8'],['Overlapping-clock faults','4'],['Total nominal operations','244 (all pass)']])
p('Fault operations require every wordline and both access enables to remain low. Invalid column codes also require all column selects low. The nominal read-low storage voltage reaches at most 0.12085 V at saved samples during reads, and the read-high storage voltage remains at least 1.09959 V at those samples. These are sampled values rather than continuous-time extrema. The storage-state checks and repeated readback provide the functional nondestructive-read evidence. The complete 72-row address/pattern table is supplied in results/address_validation.csv.')
fig('array_overview.png','Entire nominal simulation with all three patterns and protection tests.',5.4)
page();fig('write_ones_24_cells.png','All 24 storage pairs during the write-one phase.',8.2)
page();fig('write_zeros_24_cells.png','All 24 storage pairs during the write-zero phase.',8.2)
page();fig('write_mixed_24_cells.png','All 24 storage pairs during the explicit mixed-pattern write phase.',8.2)
page();fig('readback_coverage.png','Expected patterns and both measured readback scans across all 24 cells.',6.3)
fig('rw_control_simulation.png','Invalid addresses, simultaneous RD/WR, and clock overlap inhibit access.',2.9)
page();h('C. Required 50%-to-50% Timing Measurements')
p('A separate four-operation full-circuit run performs write-one, read-one, write-zero, and read-zero at row 0, column 0. It uses a 5 ps maximum timestep, conservative accuracy, and no saved-data strobing. For each operation, the rising CLK1 threshold is 0.55 V. The response threshold is the corresponding rising or falling 0.55 V crossing of the stored Q for writes and DOUT for reads. Linear interpolation between saved samples gives the delta markers. The same loads and complete transistor circuit are retained.')
table([['Measurement (TT, 27 °C, 1.1 V)','Delay, ns'],['CLK1 → Q, write 1',f"{M['timing']['write_1']['delay_ns']:.4f}"],['CLK1 → Q, write 0',f"{M['timing']['write_0']['delay_ns']:.4f}"],['CLK1 → DOUT, read 1',f"{M['timing']['read_1']['delay_ns']:.4f}"],['CLK1 → DOUT, read 0',f"{M['timing']['read_0']['delay_ns']:.4f}"],['BL precharge, 10% → 90%',f"{M['precharge_10_90_ns']:.4f}"]])
p('The write-one trigger/response times are 20.0500/20.4652 ns; write-zero times are 120.0500/120.2687 ns. Read-one times are 70.0500/70.4193 ns; read-zero times are 170.0500/170.4359 ns. These are measured access delays for the stated fixture, not a characterization of maximum clock frequency or a worst-case address/corner delay. All 12 bitlines reach at least 1.09999988 V at the pre-access sample across the nominal sequence.')
fig('timing_markers.png','Required write/read delta markers, both data polarities, at 50% VDD.',5.1)
page();h('D. Process/Temperature Checks and Extracted Replay')
p('Nine schematic cases use the same 1.1 V supply and 20 MHz clocks. TT/27 °C runs all three patterns and two scans; each additional case writes and reads all 24 mixed-pattern bits once and repeats the 28 protection operations. All nine cases pass 852 operations in total (264 writes, 336 reads, and 252 protection checks). These cases extend the assignment validation; they are not an exhaustive statistical or voltage-corner characterization.')
table([['Process / temperature','Operations','Result']]+[[x['name'].replace('array_','').replace('_',' / ')+' °C',str(x['operations']),'PASS'] for x in M['corner_runs']])
p('The Pegasus-extracted flat netlist contains 371 MOS transistors. It was converted directly into a Spectre subcircuit, preserving extracted device dimensions and source/drain geometry parameters. The nominal replay executes 268 operations, including 72 writes, 168 reads, and 28 protection operations. It adds a final complete read scan after all faults; all outputs match the expected state. No initial storage-node forcing is used in this extracted replay; the initial complete write establishes the contents.')
p('This is a device-extracted topology simulation. It includes intrinsic model/device capacitances and a 10 fF output load, with no added schematic bitline load. It does not contain extracted interconnect resistance/capacitance. Therefore the four reported timing values are schematic-fixture measurements, and are not claimed as full RC post-layout timing. Nineteen final Spectre jobs (nine array, eight unit, one fine timing, and one extracted array) finish with zero simulator errors and zero warnings. The unit jobs cover 110 input vectors.')
h('VI. DRC/LVS RESULTS')
p('Cadence Pegasus 25.14 checks GDS exported from the saved native layouts. All 562 checks in the installed GPDK045 default DRC deck are retained. Each of 17 individual/hierarchical cells has zero reported DRC results and an LVS MATCH against the native schematic CDL. The top-level source and extracted circuit each contain 371 MOS transistors. Explicit ground and supply connectivity are checked with no ground-short exception.')
page();table([['Cell/block','DRC results','LVS','Area (µm²)']]+[[x['cell'],str(x['drc_results']),x['lvs'],f"{M['layout'][x['cell']]['area_um2']:.4f}"] for x in A['physical']])
p('Native Check and Save also reports (0 errors, 0 warnings) for all 17 schematics. A GDS geometry audit confirms vertical poly throughout the top-level hierarchy and the selected metal directions: Metal2 horizontal, Metal3 vertical, Metal4 horizontal, Metal5 vertical, Metal6 horizontal, and Metal7 vertical. Metal1 includes local device/contact connections. Implants and wells follow device/tap geometry. The audit reports 101 passing evidence checks.')
p('The complete boundary is 131.84 × 42.05 µm = 5543.872 µm². The memory bank itself occupies 20.11 × 11.02 µm = 221.6122 µm², and the compact cell is 3.5616 µm². The top level uses the smallest bounding area among four generated shelf-packing candidates. Peripheral channel routing and explicit hierarchy make this a conservative educational macro; the reported area is actual, not a claim of a globally minimum SRAM layout.')
# Captured actual tool output, typeset without altering the verification result.
drc=(ROOT/'results/physical/sram_4x6/drc_summary.txt').read_text();lvs=(ROOT/'results/physical/sram_4x6/lvs_report.txt.cls').read_text()
lines=[s for s in drc.splitlines() if any(t in s for t in ['Total DRC','Total Rule','Total Checks','Total Number'])]
lines += [s for s in lvs.splitlines() if any(t in s for t in ['Run Result','Schematic Primary','Layout Primary'])]
f,ax=plt.subplots(figsize=(12,2.2));ax.axis('off');ax.text(.02,.9,'Captured Pegasus output — sram_4x6\n\n'+'\n'.join(lines),fontfamily='monospace',fontsize=12,va='top');f.tight_layout();f.savefig(F/'physical_tool_output.png',dpi=180);plt.close(f)
fig('physical_tool_output.png','Captured lines from the saved top-level DRC and LVS reports.',1.6)
page();fig('sram_4x6_layout.png','Complete physically connected 4 × 6 SRAM macro, 131.84 × 42.05 µm.',4.1)
p('Raw top-level evidence is retained in full_array/results/physical/sram_4x6/: layout.gds, drc_summary.txt, drc.log, lvs_report.txt, lvs_report.txt.cls, lvs.log, and extracted.spice. Per-cell folders retain equivalent evidence. The model SHA-256 is 4cece5fcde03aa0addfd42d5e06d9c270c42dc91f88cd0ec7e4256c98408fcae; the top-level GDS SHA-256 is '+A['layout_gds_sha256']+'.')
h('VII. CONCLUSION')
p('The 4 × 6 SRAM integrates all required memory and peripheral blocks, writes and reads every valid address at 20 MHz, and preserves data over repeated reads and protection tests. Both data polarities have explicit 50%-to-50% timing markers. All 17 layouts have zero DRC violations and matching LVS, and the extracted transistor circuit reproduces the expected output sequence. Native Cadence views, simulation decks and waveforms, verification logs, scripts, and editable report are supplied for review and reproduction. Further optimization could reduce peripheral routing area and characterize full interconnect-RC timing.')
h('REFERENCES')
for s in ['[1] EEE4310/5322, Final Project Slides, Fall 2026, supplied Project Instruction Files/Final Project Slides.pdf.', '[2] Supplied SRAM Cell.pdf and FinalProjectSchematicHelp.pdf, Project Instruction Files.', '[3] Supplied Final Project Layout Help.pdf, Overview of Design Rules – 45 nm.pdf, and gpdk045_drc.pdf.', '[4] Cadence GPDK045, installed BSIM model gpdk045_mos.scs and default pvs/pvlDRC.rul and pvlLVS.rul decks; local Virtuoso IC6.1.8, Spectre 21.1, and Pegasus 25.14.', '[5] Supplied Old reference project/Report.pdf, used for report organization and circuit reference, not its measurements or verification exceptions.', '[6] Companion single-cell design and measured study, sram_cell/SRAM_Cell_Report.pdf and its saved simulation/verification evidence.']:
 p(s)

styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyCustom',fontName='DV',fontSize=9.8,leading=13.1,spaceAfter=7));styles.add(ParagraphStyle(name='HeadCustom',fontName='DV-Bold',fontSize=12,leading=15,spaceBefore=11,spaceAfter=8));styles.add(ParagraphStyle(name='CapCustom',fontName='DV',fontSize=8.3,leading=10.5,spaceAfter=9));styles.add(ParagraphStyle(name='TitleCustom',fontName='DV-Bold',fontSize=17,leading=21,alignment=1,spaceAfter=16))
for nm,fn in [('DV','DejaVuSerif.ttf'),('DV-Bold','DejaVuSerif-Bold.ttf')]:pdfmetrics.registerFont(TTFont(nm,'/usr/share/fonts/dejavu/'+fn))
doc=Document();doc.core_properties.author='';doc.core_properties.last_modified_by='';sec=doc.sections[0];sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.6);sec.left_margin=sec.right_margin=Inches(.65)
normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(10);normal.paragraph_format.space_after=Pt(7)
sec.header.paragraphs[0].text='EEE5322 • 4 × 6 SRAM • GPDK045'
story=[]
for typ,val in blocks:
 if typ in ['paragraph','heading','title']:
  story.append(Paragraph(escape(val),styles[{'paragraph':'BodyCustom','heading':'HeadCustom','title':'TitleCustom'}[typ]]))
  if typ=='paragraph':doc.add_paragraph(val)
  elif typ=='heading':doc.add_heading(val,level=1 if val[0:1] in 'IVR' else 2)
  else:doc.add_heading(val,0)
 elif typ=='page':story.append(PageBreak());doc.add_page_break()
 elif typ=='table':
  n=len(val[0]); ww=[496/n]*n
  tt=Table([[Paragraph(escape(str(s)),styles['CapCustom']) for s in r] for r in val],colWidths=ww,repeatRows=1,hAlign='LEFT');tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4ecf3')),('GRID',(0,0),(-1,-1),.4,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([tt,Spacer(1,10)])
  dt=doc.add_table(rows=0,cols=n);dt.style='Table Grid'
  for row in val:
   cells=dt.add_row().cells
   for cell,txt in zip(cells,row):cell.text=str(txt)
 elif typ=='figure':
  path,cap,maxh=val
  with PILImage.open(path) as im:w,hh=im.size
  scale=min(496/w,maxh*72/hh);iw,ih=w*scale,hh*scale
  story.append(KeepTogether([Image(str(path),width=iw,height=ih),Paragraph(escape(cap),styles['CapCustom'])]))
  doc.add_picture(str(path),width=Inches(iw/72));doc.add_paragraph(cap,style='Caption')
pdf=REPO/'Final_Project_Report.pdf';word=REPO/'Final_Project_Report.docx'
def footer(canvas,document):
 canvas.setFont('DV',8);canvas.drawString(48,24,'EEE5322 • 4 × 6 SRAM');canvas.drawRightString(564,24,str(document.page))
SimpleDocTemplate(str(pdf),pagesize=(612,792),rightMargin=58,leftMargin=58,topMargin=40,bottomMargin=40,title='4 × 6 SRAM Design and Validation',author='').build(story,onFirstPage=footer,onLaterPages=footer)
doc.save(word)
shutil.copy2(F/'sram_4x6_layout.png',REPO/'Full_Array_Layout.png')
print('Generated',pdf,word,'with',number,'numbered figures')
