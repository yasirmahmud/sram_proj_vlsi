#!/apps/anaconda/bin/python
from pathlib import Path
import subprocess,os,json
ROOT=Path(__file__).resolve().parents[1]
fig=ROOT/'results/figures';fig.mkdir(exist_ok=True)
names=['inv','nand2','nand3','and3','bitcell','row_decoder','column_decoder','rw_control','write_driver','column_mux','precharge_unit','precharge','sense_amp','read_latch','bit_array','sram_4x6']
code=[]
for c in names:
 code += [f'w=deOpenCellView("sram_project" "{c}" "schematic" "schematic" nil "r")',f'hiExportImage(?fileName "{fig/(c+"_schematic.png")}" ?window w ?exportRegion \'entireDesign ?width 2400)',f'w=deOpenCellView("sram_project" "{c}" "symbol" "schematicSymbol" nil "r")',f'hiExportImage(?fileName "{fig/(c+"_symbol.png")}" ?window w ?exportRegion \'entireDesign ?width 1000)',f'w=deOpenCellView("sram_project" "{c}" "layout" "maskLayout" nil "r")','geSetAreaViewLevel(w w~>cellView~>bBox 0 32)','foreach(layer \'("Metal1" "Metal2" "Metal3" "Metal4" "Metal5" "Metal6" "Metal7") leSetLayerVisible(list(layer "pin") nil) leSetLayerVisible(list(layer "label") nil))',f'hiExportImage(?fileName "{fig/(c+"_layout.png")}" ?window w ?exportRegion \'entireDesign ?width 2400)']
code += ['exit()'];p=ROOT/'scripts/screenshots_generated.il';p.write_text('\n'.join(code)+'\n')
env=os.environ.copy();env.setdefault('CDS_LIC_FILE','5280@ece-itop-licsvr.ece.ufl.edu');env['PATH']='/apps/cds/IC618/tools/dfII/bin:/apps/cds/IC618/tools/bin:'+env['PATH'];env['CDSHOME']='/apps/cds/IC618'
with (ROOT/'results/screenshots.stdout').open('w') as f:r=subprocess.run(['xvfb-run','-a','-s','-screen 0 2560x1600x24','virtuoso','-nocdsinit','-replay',str(p),'-log',str(ROOT/'results/screenshots.log')],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0
assert all((fig/(n+'_'+v+'.png')).exists() for n in names for v in ['schematic','symbol','layout'])
print('Saved 48 native Cadence screenshots')
