"""Canonical transistor and hierarchical circuits for the 4x6 SRAM project."""
from pathlib import Path
import json,sys,re
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'sram_cell/scripts'))
from project_paths import model_file
from simulate import mos as cdf_mos
C={}
def circuit(name,ports,mos=(),inst=(),directions=None):
 C[name]={'ports':ports.split(),'mos':list(mos),'inst':list(inst),'directions':directions or {}}
 return C[name]
def m(name,d,g,s,kind,w,l=45):return [name,d,g,s,'VDD' if kind=='p' else 'GND',kind,w,l]
def x(name,cell,*nodes):return [name,cell,list(nodes)]
circuit('inv','IN OUT VDD GND',[m('NM0','OUT','IN','GND','n',360),m('PM0','OUT','IN','VDD','p',360)],directions={'OUT':'output'})
circuit('nand3','A B E Y VDD GND',[
 m('NM0','Y','A','n1','n',1080),m('NM1','n1','B','n2','n',1080),m('NM2','n2','E','GND','n',1080),
 m('PM0','Y','A','VDD','p',360),m('PM1','Y','B','VDD','p',360),m('PM2','Y','E','VDD','p',360)],directions={'Y':'output'})
circuit('and3','A B E Y VDD GND',inst=[x('NAND','nand3','A','B','E','nb','VDD','GND'),x('BUF','inv','nb','Y','VDD','GND')],directions={'Y':'output'})
circuit('nand2','A B Y VDD GND',[m('N0','Y','A','n0','n',720),m('N1','n0','B','GND','n',720),m('P0','Y','A','VDD','p',360),m('P1','Y','B','VDD','p',360)],directions={'Y':'output'})
circuit('tg','A B EN ENB VDD GND',[m('N','B','EN','A','n',1080),m('P','B','ENB','A','p',1080)],directions={'A':'inputOutput','B':'inputOutput'})
circuit('precharge_unit','BL BLB PCB VDD GND',[
 m('P0','BL','PCB','VDD','p',1080),m('P1','BLB','PCB','VDD','p',1080),m('PEQ','BL','PCB','BLB','p',1080)],directions={'BL':'inputOutput','BLB':'inputOutput'})
circuit('sense_amp','BIT BIT_bar RE VDD GND AMP_OUT',[
 m('PM6','nd','nd','VDD','p',1440),m('PM5','ns','nd','VDD','p',1440),m('PM7','AMP_OUT','ns','VDD','p',360),
 m('NM41','ns','BIT','tail','n',240),m('NM40','nd','BIT_bar','tail','n',240),m('NM39','AMP_OUT','ns','GND','n',360),m('NM38','tail','RE','GND','n',360)],directions={'AMP_OUT':'output'})
circuit('read_latch','D EN ENB Q VDD GND',inst=[x('INPUT','tg','D','n0','EN','ENB','VDD','GND'),x('I0','inv','n0','nb','VDD','GND'),x('I1','inv','nb','Q','VDD','GND'),x('FEEDBACK','tg','Q','n0','ENB','EN','VDD','GND')],directions={'Q':'output'})
circuit('row_decoder','R1 R0 EN WL0 WL1 WL2 WL3 VDD GND',inst=[x('I0','inv','R0','R0B','VDD','GND'),x('I1','inv','R1','R1B','VDD','GND')]+[x(f'R{i}','and3','R1' if i&2 else 'R1B','R0' if i&1 else 'R0B','EN',f'WL{i}','VDD','GND') for i in range(4)],directions={f'WL{i}':'output' for i in range(4)})
circuit('column_decoder','C2 C1 C0 CS0 CS1 CS2 CS3 CS4 CS5 VDD GND',inst=[x(f'I{i}','inv',f'C{i}',f'C{i}B','VDD','GND') for i in range(3)]+[x(f'C{i}','and3',*['C'+str(k)+('' if i&(1<<k) else 'B') for k in [2,1,0]],f'CS{i}','VDD','GND') for i in range(6)],directions={f'CS{i}':'output' for i in range(6)})
ctrl=[x('IRD','inv','RD','NRD','VDD','GND'),x('IWR','inv','WR','NWR','VDD','GND'),x('IPRE','inv','CLK2','PCB','VDD','GND'),x('BAD','and3','C2','C1','VDD','BADCOL','VDD','GND'),x('VALID','inv','BADCOL','VALID','VDD','GND'),x('WA','and3','WR','NRD','CLK1','WA','VDD','GND'),x('RA','and3','RD','NWR','CLK1','RA','VDD','GND'),x('WE','and3','WA','VALID','PCB','WEN','VDD','GND'),x('RE','and3','RA','VALID','PCB','REN','VDD','GND'),x('IWE','inv','WEN','WENB','VDD','GND'),x('IRE','inv','REN','RENB','VDD','GND'),x('IDLE','and3','WENB','RENB','VDD','IDLE','VDD','GND'),x('ACTIVE','inv','IDLE','ROWEN','VDD','GND')]
circuit('rw_control','CLK1 CLK2 WR RD C2 C1 WEN WENB REN RENB ROWEN PCB VDD GND',inst=ctrl,directions={s:'output' for s in ['WEN','WENB','REN','RENB','ROWEN','PCB']})
circuit('write_driver','DIN WEN WENB GBL GBLB VDD GND',inst=[x('ID','inv','DIN','DINB','VDD','GND'),x('W0','tg','DIN','GBL','WEN','WENB','VDD','GND'),x('W1','tg','DINB','GBLB','WEN','WENB','VDD','GND')],directions={'GBL':'inputOutput','GBLB':'inputOutput'})
circuit('column_mux',' '.join([f'CS{i}' for i in range(6)]+[f'BL{i}' for i in range(6)]+[f'BLB{i}' for i in range(6)]+['GBL','GBLB','VDD','GND']),inst=sum(([x(f'I{i}','inv',f'CS{i}',f'CSB{i}','VDD','GND'),x(f'M{i}P','tg',f'BL{i}','GBL',f'CS{i}',f'CSB{i}','VDD','GND'),x(f'M{i}N','tg',f'BLB{i}','GBLB',f'CS{i}',f'CSB{i}','VDD','GND')] for i in range(6)),[]),directions={s:'inputOutput' for s in [f'BL{i}' for i in range(6)]+[f'BLB{i}' for i in range(6)]+['GBL','GBLB']})
circuit('precharge',' '.join([f'BL{i}' for i in range(6)]+[f'BLB{i}' for i in range(6)]+['PCB','VDD','GND']),inst=[x(f'P{i}','precharge_unit',f'BL{i}',f'BLB{i}','PCB','VDD','GND') for i in range(6)],directions={f'{s}{i}':'inputOutput' for s in ['BL','BLB'] for i in range(6)})
# Observation ports remain internal to the top-level macro.
circuit('bitcell','BL BL_bar WL Q Q_bar VDD GND',[m('PM0','Q_bar','Q','VDD','p',120),m('PM1','Q','Q_bar','VDD','p',120),m('NM0','Q_bar','Q','GND','n',360),m('NM1','Q','Q_bar','GND','n',360),m('NM2','Q_bar','WL','BL_bar','n',240),m('NM3','BL','WL','Q','n',240)],directions={'BL':'inputOutput','BL_bar':'inputOutput','Q':'inputOutput','Q_bar':'inputOutput'})
circuit('bit_array',' '.join([f'WL{i}' for i in range(4)]+[f'BL{i}' for i in range(6)]+[f'BLB{i}' for i in range(6)]+['VDD','GND']),inst=[x(f'B{r}_{c}','bitcell',f'BL{c}',f'BLB{c}',f'WL{r}',f'Q{r}_{c}',f'QB{r}_{c}','VDD','GND') for r in range(4) for c in range(6)],directions={f'{s}{i}':'inputOutput' for s in ['BL','BLB'] for i in range(6)})
top=[x('CTRL','rw_control','CLK1','CLK2','WR','RD','C2','C1','WEN','WENB','REN','RENB','ROWEN','PCB','VDD','GND'),x('ROW','row_decoder','R1','R0','ROWEN',*[f'WL{i}' for i in range(4)],'VDD','GND'),x('COL','column_decoder','C2','C1','C0',*[f'CS{i}' for i in range(6)],'VDD','GND'),x('PRE','precharge',*[f'BL{i}' for i in range(6)],*[f'BLB{i}' for i in range(6)],'PCB','VDD','GND'),x('MUX','column_mux',*[f'CS{i}' for i in range(6)],*[f'BL{i}' for i in range(6)],*[f'BLB{i}' for i in range(6)],'GBL','GBLB','VDD','GND'),x('WRITE','write_driver','DIN','WEN','WENB','GBL','GBLB','VDD','GND'),x('MEM','bit_array',*[f'WL{i}' for i in range(4)],*[f'BL{i}' for i in range(6)],*[f'BLB{i}' for i in range(6)],'VDD','GND'),x('SENSE','sense_amp','GBL','GBLB','REN','VDD','GND','SENSE'),x('LATCH','read_latch','SENSE','REN','RENB','DOUT','VDD','GND')]
circuit('sram_4x6','R1 R0 C2 C1 C0 CLK1 CLK2 WR RD DIN DOUT VDD GND',inst=top,directions={'DOUT':'output'})

def spice_spectre():
 lines=['simulator lang=spectre']
 for name,c in C.items():
  lines.append('subckt '+name+' ('+' '.join(c['ports'])+')')
  for name,d,g,s,b,kind,w,l in c['mos']:
   line=cdf_mos(name,d,g,s,b,kind,w).rstrip()
   if l!=45:line=re.sub(r'(?<![A-Za-z0-9_])45n\b',f'{l}n',line)
   lines.append(line)
  for name,child,nodes in c['inst']:lines.append('X'+name+' ('+' '.join(nodes)+') '+child)
  lines.append('ends '+name if False else 'ends')
 return '\n'.join(lines)+'\n'

def cdl():
 lines=['* Canonical 45nm CMOS SRAM circuits']
 for cn,c in C.items():
  lines.append('.SUBCKT '+cn+' '+' '.join(c['ports']))
  for n,d,g,s,b,k,w,l in c['mos']:lines.append(f'M{n} {d} {g} {s} {b} g45{k}1svt W={w}n L={l}n')
  for n,ch,ns in c['inst']:lines.append('X'+n+' '+' '.join(ns)+' '+ch)
  lines.append('.ENDS '+cn)
 return '\n'.join(lines)+'\n'
if __name__=='__main__':
 (ROOT/'netlists/catalog.json').write_text(json.dumps(C,indent=2))
 (ROOT/'netlists/design.scs').write_text(spice_spectre())
 (ROOT/'netlists/design.cdl').write_text(cdl())
 print('Generated',len(C),'hierarchical cells')
