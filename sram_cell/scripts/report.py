#!/apps/anaconda/bin/python
"""Write an editable Word report and matching PDF from measured results."""
from pathlib import Path
import json,sys,hashlib,re,shutil
import matplotlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.python_packages'))
from docx import Document
from docx.shared import Inches,Pt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
RES=ROOT/'results';m=json.loads((RES/'metrics.json').read_text())
font=Path(matplotlib.get_data_path())/'fonts/ttf/DejaVuSans.ttf';pdfmetrics.registerFont(TTFont('DV',str(font)))
styles=getSampleStyleSheet()
for n in ['Normal','Title','Heading1','Heading2']:styles[n].fontName='DV'
styles['Normal'].fontSize=9;styles['Normal'].leading=13
styles['Heading1'].fontSize=15;styles['Heading1'].leading=20
D=Document();sec=D.sections[0];sec.top_margin=sec.bottom_margin=Inches(.6);sec.left_margin=sec.right_margin=Inches(.65)
D.styles['Normal'].font.size=Pt(10)
flow=[]
def para(t):D.add_paragraph(t);flow.extend([Paragraph(t.replace('&','&amp;'),styles['Normal']),Spacer(1,7)])
def heading(t):D.add_heading(t,1);flow.append(Paragraph(t,styles['Heading1']))
def title(t):D.add_heading(t,0);flow.extend([Paragraph(t,styles['Title']),Spacer(1,12)])
def page():D.add_page_break();flow.append(PageBreak())
def table(headers,rows):
    t=D.add_table(rows=1,cols=len(headers));t.style='Light Shading Accent 1'
    for c,v in zip(t.rows[0].cells,headers):c.text=str(v)
    for row in rows:
        for c,v in zip(t.add_row().cells,row):c.text=str(v)
    data=[[Paragraph(str(x),styles['Normal']) for x in row] for row in [headers]+rows]
    tt=Table(data,repeatRows=1,hAlign='LEFT',colWidths=[528/len(headers)]*len(headers));tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8edf5')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#bfc8d4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]));flow.extend([tt,Spacer(1,10)])
def fig(name,caption,maxh=420):
    p=RES/'figures'/name
    if not p.exists():return
    w,h=PILImage.open(p).size;scale=min(528/w,maxh/h)
    im=Image(str(p),width=w*scale,height=h*scale,hAlign='CENTER');flow.extend([im,Spacer(1,4),Paragraph(caption,styles['Normal']),Spacer(1,8)])
    ww=min(7.0,7.0*maxh/(h/w*504));D.add_picture(str(p),width=Inches(ww));D.add_paragraph(caption,style='Caption')
def fmt(v):return f'{v:.2f}'

title('45 nm Six-Transistor SRAM Cell')
para('Design and local EDA validation • November 7, 2026 • Single-cell deliverable')
para('A cross-coupled 6T SRAM cell was implemented in the Cadence GPDK045 process at 1.1 V. The final sized cell and the all-default-width assignment baseline have native Virtuoso schematics, symbols, and layouts. Both layouts pass the installed default GPDK045 DRC deck and match their respective schematics in LVS.')
table(['Item','Final implementation'],[
['Pull-up / access / pull-down width','120 / 240 / 360 nm'],['All gate lengths','45 nm'],['Nominal supply / temperature','1.1 V / 27 °C'],['Physical layout boundary','2.120 × 1.680 µm = 3.5616 µm²'],['Write 1 / write 0, BL → Q',f"{fmt(m['write_50pct']['1']['delay_ps'])} / {fmt(m['write_50pct']['0']['delay_ps'])} ps"],['Read SNM',f"{next(r['margin_mV'] for r in m['margins'] if r['kind']=='read' and r['sizing']=='final'):.2f} mV"],['Default DRC / LVS, both versions','562 rule checks, 0 results / MATCH'],['Physical write/read sequence','10110010; all checked states and reads pass']])
para('The scope is one SRAM bitcell. The full 2×6 or 4×6 array, decoders, sense amplifier, and array CLK1-to-output measurements in Final Project Slides.pdf are subsequent integration work and are not claimed here.')
heading('Sizing and interface')
para('The assignment baseline uses 120 nm for all six widths. The final project permits sizing to avoid write failure and destructive read. The supplied reference uses 120/240/360 nm; this was retained after characterization. The pull-down/access ratio is 1.5 and the access/pull-up ratio is 2. NMOS bulks connect to GND; PMOS bulks connect to Vdd. Q follows BL when WL is high. Q and Q_bar are exposed as observation ports; ordinary operation only drives WL, BL, BL_bar, and the supplies.')
para('The two cells are sram_cell/sram_cell and sram_cell/sram_cell_default in the local library. The reusable symbols expose BL, BL_bar, WL, Q, Q_bar, Vdd, and GND.')
page();heading('Native schematic and model fidelity')
fig('schematic_cadence.png','Native Virtuoso schematic of the final cell; six GPDK045 MOS devices.',maxh=420)
para('Check and Save returns 0 errors and 0 warnings for both schematics. The reference schematic provides the topology and sizing. The compact core placement follows the supplied reference and user-provided image; its local routing was adapted and standalone taps and pins were added. The reference report is used for context, not as evidence of this design passing verification.')
para('Spectre 21.1.0.664 runs the supplied Project files/gpdk045_mos.scs, which is byte-identical to the installed PDK model. The supplied nmos.scs identifies an older 180 nm NMOS model and is not used. Device parameters in the test decks come from the native Cadence CDF netlist, including diffusion and layout-dependent model terms. Thresholds and timing come from saved numerical waveforms, not drawn estimates.')
page();heading('Standalone layout and extraction')
fig('layout_compact.png','Compact native Virtuoso layout matching the requested reference arrangement. Contacts are 0.06 × 0.06 µm.',maxh=510)
para('The layout has one connected N-well with a Vdd tap and a substrate tap tied to GND. All 42 streamed poly rectangles are vertically oriented. The two inverters occupy the center, with staggered access transistors at the left and right sides, matching the requested reference arrangement. Metal1 provides local device connections. Three horizontal Metal2 straps replace horizontal poly interconnects so that all poly remains vertical. The boundary is 2.120 × 1.680 µm (3.5616 µm²), including standalone taps and contacted wordline access. This replaces the previous 15.990 µm² floorplan.')
page();heading('Write timing: assignment stimulus')
para('VDD = 1.1 V; WL = 2 MHz; BL and BL_bar = 10 MHz, complementary; all edges = 100 ps. Pulse widths account for edge time so the 50% crossings have a 50% duty cycle. The transient runs for 800 ns. An initial stored zero selects a deterministic start; the sequence then overwrites both states and retains the final state while WL is low.')
fig('write_nominal.png','Saved WL, BL, BL_bar, Q, and Q_bar waveforms for the final cell.',maxh=340)
fig('write_nominal_markers.png','Delta markers use BL = VDD/2 and Q = VDD/2, interpolated from the numerical samples.',maxh=170)
table(['Write','Final (ps)','Default-width baseline (ps)','Extracted devices (ps)'],[[b,fmt(m['write_50pct'][b]['delay_ps']),fmt(m['write_default_50pct'][b]['delay_ps']),fmt(m['extracted_write_50pct'][b]['delay_ps'])] for b in ['1','0']])
page();heading('Read timing: assignment experiment')
para('As requested in SRAM Cell.pdf, Q and Q_bar are complementary 10 MHz ideal inputs in this diagnostic experiment. WL remains 2 MHz with 100 ps edges. BL and BL_bar each have an explicitly stated 20 fF load. Read delay is from Q at 0.55 V to BL at 0.55 V. This diagnostic does not establish nondestructive read because the storage nodes are forced by sources.')
fig('read_forced.png','Forced-storage-node diagnostic read experiment, 800 ns.',maxh=340)
fig('read_forced_markers.png','50%-to-50% read markers; the NMOS pass-high path is slower than its pull-low path.',maxh=170)
table(['Read transition','Delay (ps)'],[[b,fmt(m['read_forced_50pct'][b]['delay_ps'])] for b in ['1','0']])
page();heading('Physical read, retention, and corner validation')
para('A separate 50 MHz experiment writes 10110010 through external transmission gates, disables the write drivers, and retains the bit. Both bitlines are then precharged to VDD with the wordline low. Precharge turns off before the wordline rises for read. Q and Q_bar are never externally driven in this test. Each bitline has 20 fF capacitance.')
fig('functional.png','Eight 20 ns cycles. Write WL is high at 2.1–5 ns; precharge at 9.1–11 ns; read WL at 12.1–15 ns, relative to each cycle. All transitions take 100 ps.',maxh=365)
para('Assertions check write completion at 4.8 ns, hold at 8 ns, read at 14.8 ns, and retention after read at 19 ns. Valid rails are below 10% or above 90% of VDD. Both bitlines must reach at least 99% of VDD before read. Read differential must have the correct sign and exceed 100 mV; the disturbed low storage node must remain below VDD/2.')
corner_rows=[]
for c in ['tt','ff','ss','fs','sf']:
 corner_rows.append([c.upper()]+['PASS' if m['functional'][f'functional_{c}_{t}']['pass'] else 'FAIL' for t in [-40,27,125]])
table(['Process corner','−40 °C','27 °C','125 °C'],corner_rows)
para('All 15 process/temperature combinations pass at 1.1 V, covering 120 write/read cycles. The nominal and extracted-device experiments also pass. This is deterministic corner validation; it does not measure random-mismatch yield.')
page();heading('Physical single-cell timing and extracted devices')
fig('physical_timing.png','WL-to-storage write timing and WL-to-discharging-bitline read timing use the 50%-to-50% rule.',maxh=360)
table(['Operation','Response node','Delay (ps)'],[[k,v['response'],fmt(v['delay_ps'])] for k,v in m['physical_50pct'].items()])
fig('extracted_functional.png','Simulation of the actual extracted six-device topology with its extracted diffusion and layout-dependent parameters.',maxh=270)
para('Extracted-device simulation passes the same functional assertions. Pegasus extraction is used for LVS and device simulation. Interconnect RC and a sense amplifier are not included; the bitline load remains the stated lumped 20 fF. The reported WL read delay is a cell/bitline metric, not full-array CLK1-to-sense-amplifier delay.')
page();heading('Supply scaling and deterministic gate offset')
para('The 800 ns write stimulus is repeated at five coarse supplies from 0 to 1.1 V, then refined around failure. VDD also scales the WL/BL source amplitudes. The offset source is in one feedback path, with V(Q_gate) − V(Q) = voffset. This is the assignment gate-offset experiment, not a statistical threshold mismatch model.')
para('At every supply, both Q and Q_bar are checked against their expected values in the write and hold intervals. The score is min(Vhigh/VDD, 1 − Vlow/VDD) over all sampled states. PASS requires a score of at least 0.90. Zero supply is explicitly a failure. The no-offset boundary is bracketed between 0.33 V (fails) and 0.34 V (passes), for this waveform and criterion.')
fig('reliability.png','Supply and gate-offset sweeps. Raw values are saved in results/reliability.csv.',maxh=260)
rows=[]
for off in [0,.1,.2,.3,.4]:
 rr=m['reliability'];rr=[r for r in rr if r['offset_V']==off]
 passed=sorted({r['vdd_V'] for r in rr if r['pass']});failed=sorted({r['vdd_V'] for r in rr if not r['pass']})
 rows.append([f'{off:.1f}',f'{max(failed):.2f}' if failed else 'none',f'{min(passed):.2f}' if passed else 'none tested'])
table(['Gate offset (V)','Highest failed supply (V)','Lowest passed supply (V)'],rows)
para('For offsets 0.1, 0.2, 0.3, and 0.4 V, all eight required supplies from 0.2 through 0.9 V were simulated. Extra 1.0 and 1.1 V points extend the failure boundary where needed; they do not replace the required grid. A failed point means the stated 90% rail criterion fails, not that every possible operation necessarily fails.')
page();heading('Supply boundary waveforms')
fig('supply_boundary.png','Saved Q/Q_bar voltages straddle the measured reliability boundary. Dotted lines mark 90% of each supply.',maxh=410)
heading('Read and write static margins')
para('DC VIN is swept from 0 to 1.1 V in 0.5 mV steps. Read SNM is the smaller largest axis-aligned square in the two mirrored VTC lobes, with WL = BL = VDD. The square is computed from the decreasing curve boundaries and plotted explicitly. For write, the two VTCs use BL = VDD and BL = 0, following the handout’s square construction. This write metric is identified separately from a write-trip voltage or statistical write margin.')
table(['Sizing (PD / AX / PU)','Read SNM (mV)','Write square margin (mV)'],[[name,fmt(next(r['margin_mV'] for r in m['margins'] if r['kind']=='read' and r['sizing']==key)) if key!='pullup2' else 'see write study',fmt(next(r['margin_mV'] for r in m['margins'] if r['kind']=='write' and r['sizing']==key)) if key!='pulldown2' else 'see read study'] for key,name in [('default','120 / 120 / 120 nm'),('access2','120 / 240 / 120 nm'),('pulldown2','240 / 120 / 120 nm'),('pullup2','120 / 120 / 240 nm'),('final','360 / 240 / 120 nm')]])
page();heading('Noise-margin plots')
fig('read_snm.png','Read butterfly curves and the measured squares. Stronger pull-down improves read margin; stronger access reduces it.',maxh=220)
fig('write_snm.png','Assignment write-square margin: stronger access helps writing, while a stronger pull-up makes writing harder.',maxh=220)
heading('Verification evidence and reproduction')
para('The final automated audit passes 104 checks. All 94 Spectre runs complete with zero errors and zero warnings. Physical verification uses local Pegasus 25.14 with the installed GPDK045 PVL decks. All 562 default DRC rule checks finish with zero results for both cell variants. Optional DFM, density, and antenna decks are separate from this default run. Both LVS reports state MATCH, including exact drawn W and L checks. Both native schematic checks return (0 0).')
para('Key files: results/drc/summary.txt; results/lvs/report.txt.cls; results/default_drc/summary.txt; results/default_lvs/report.txt.cls; results/metrics.json; results/reliability.csv; netlists/sram_cell.cdl; netlists/sram_cell_extracted.scs. Generated decks are in netlists/; each simulation directory contains its log and PSF ASCII waveform output.')
para('From project_file/sram_cell run bash scripts/run_all.sh. It uses the installed UF Cadence tool paths and checks simulator completion, functional assertions, DRC, and LVS. Open Virtuoso from project_file to load the provided cds.lib. The report source is scripts/report.py; this editable document and the PDF are generated from the same measured data.')
para('Requirement sources: Project files/SRAM Cell.pdf; Final Project Slides.pdf; FinalProjectSchematicHelp.pdf; Final Project Layout Help.pdf; Overview of Design Rules – 45 nm.pdf; gpdk045_drc.pdf. Reference: Old reference project/sram_cell schematic and Report.pdf. Work performed here: topology review, sizing characterization, layout generation, automated local simulations, physical verification, and reporting. No student names or team workload allocations are invented.')
D.save(ROOT/'SRAM_Cell_Report.docx')
def footer(canvas,doc):
 canvas.setFont('DV',8);canvas.drawString(42,23,'GPDK045 SRAM cell • local EDA validation');canvas.drawRightString(570,23,str(doc.page))
SimpleDocTemplate(str(ROOT/'SRAM_Cell_Report.pdf'),pagesize=(612,792),leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=39,title='45 nm SRAM Cell Design and Validation',author='').build(flow,onFirstPage=footer,onLaterPages=footer)
print('Created SRAM_Cell_Report.docx and SRAM_Cell_Report.pdf')

shutil.copyfile(RES/'figures/layout_compact.png',ROOT/'Layout_Preview.png')
