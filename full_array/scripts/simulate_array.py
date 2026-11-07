#!/apps/anaconda/bin/python
"""Run transistor-level validation of every SRAM address and protection case."""
from pathlib import Path
import sys,os,json,subprocess,argparse,concurrent.futures
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from design import C,model_file
SP='/apps/cds/spectre211/bin/spectre'
VDD=1.1

def operations(selected=None,scans=2):
 ops=[];state=[0]*24; patterns={'ones':'1'*24,'zeros':'0'*24,'mixed':'100110101001011001110010'}
 for phase,bits in patterns.items():
  if selected and phase not in selected:continue
  for addr,bit in enumerate(bits):
   state[addr]=int(bit);ops.append(dict(kind='write',phase=phase,addr=addr,bit=int(bit),expected=state.copy()))
  for scan in range(scans):
   for addr,bit in enumerate(bits):ops.append(dict(kind='read',phase=phase,scan=scan,addr=addr,bit=int(bit),expected=state.copy()))
 for row in range(4):
  for col in [6,7]:
   for k in ['invalid_write','invalid_read']:ops.append(dict(kind=k,phase='invalid',addr=row*8+col,row=row,col=col,bit=1,expected=state.copy()))
 for addr in range(8):ops.append(dict(kind='conflict',phase='interlock',addr=addr,bit=1,expected=state.copy()))
 for addr in range(4):ops.append(dict(kind='overlap',phase='clock_interlock',addr=addr,bit=1,expected=state.copy()))
 return ops,patterns

def wave(name,node,points):return f'V{name} ({node} 0) vsource type=pwl wave=['+' '.join(f'{t:g}n ({v:g}*vdd)' for t,v in points)+']\n'

def make_deck(corner='tt',temp=27,vdd=1.1,include=None,selected=None,scans=2,strobe=True,custom_ops=None):
 ops,patterns=operations(selected,scans)
 if custom_ops is not None:ops=custom_ops
 sigs=['R1','R0','C2','C1','C0','WR','RD','DIN','CLK1','CLK2'];seq={s:[(0,0)] for s in sigs}
 def setv(sig,t,v):
  old=seq[sig][-1][1]
  if old!=v:seq[sig].extend([(t,old),(t+.1,v)])
 for i,op in enumerate(ops):
  t=50*i;row=op.get('row',op['addr']//6);col=op.get('col',op['addr']%6)
  for sig,value in [('R1',(row>>1)&1),('R0',row&1),('C2',(col>>2)&1),('C1',(col>>1)&1),('C0',col&1),('WR',int(op['kind'] in ['write','invalid_write','conflict','overlap'])),('RD',int(op['kind'] in ['read','invalid_read','conflict'])),('DIN',op['bit'])]:setv(sig,t+.2,value)
  setv('CLK1',t+20,1);setv('CLK1',t+40,0)
  setv('CLK2',t+2,1);setv('CLK2',t+(42 if op['kind']=='overlap' else 12),0)
 stop=len(ops)*50
 for sig in sigs:seq[sig].append((stop,seq[sig][-1][1]))
 d=f'simulator lang=spectre\ninclude "{model_file()}" section={corner}\ninclude "{include or ROOT/"netlists/design.scs"}"\nparameters vdd={vdd}\nsimOptions options temp={temp} reltol=1e-3 vabstol=1e-7 iabstol=1e-14 gmin=1e-14\nVDD (VDD 0) vsource dc=vdd\n'
 d+=''.join(wave(s,s,seq[s]) for s in sigs)
 d+='Xchip (R1 R0 C2 C1 C0 CLK1 CLK2 WR RD DIN DOUT VDD 0) sram_4x6\nCOUT (DOUT 0) capacitor c=10f\n'
 for c in range(6):d+=f'CBL{c} (Xchip.BL{c} 0) capacitor c=20f\nCBLB{c} (Xchip.BLB{c} 0) capacitor c=20f\n'
 d+='CG0 (Xchip.GBL 0) capacitor c=5f\nCG1 (Xchip.GBLB 0) capacitor c=5f\n'
 d+='ic '+' '.join(f'Xchip.XMEM.Q{r}_{c}=0 Xchip.XMEM.QB{r}_{c}=vdd' for r in range(4) for c in range(6))+'\n'
 d+=f'tran tran stop={stop}n maxstep=500p errpreset=moderate{" strobeperiod=500p strobeoutput=strobeonly" if strobe else ""}\n'
 save=sigs+['DOUT']+[f'Xchip.{s}' for s in ['WEN','REN','ROWEN','PCB','GBL','GBLB','SENSE']]+[f'Xchip.WL{r}' for r in range(4)]+[f'Xchip.CS{c}' for c in range(6)]+[f'Xchip.BL{c}' for c in range(6)]+[f'Xchip.BLB{c}' for c in range(6)]+[f'Xchip.XMEM.Q{r}_{c}' for r in range(4) for c in range(6)]+[f'Xchip.XMEM.QB{r}_{c}' for r in range(4) for c in range(6)]
 d+='save '+' '.join(save)+'\n'
 return d

def run(name,deck,selected=None,scans=2,custom_ops=None):
 out=ROOT/'results'/name;out.mkdir(exist_ok=True)
 for fn in ['waveforms.npz','checks.json','unit_checks.json']:
  old=out/fn
  if old.exists():old.unlink()
 (out/'operations.json').write_text(json.dumps({'operations':operations(selected,scans)[0] if custom_ops is None else custom_ops,'patterns':operations()[1],'period_ns':50},indent=2));net=ROOT/'netlists'/f'{name}.scs';net.write_text(deck)
 env=os.environ.copy();env.setdefault('CDS_LIC_FILE','5280@ece-itop-licsvr.ece.ufl.edu')
 with (out/'stdout.log').open('w') as f:r=subprocess.run([SP,'+aps','+mt=4',str(net),'-raw',str(out/'psf'),'-format','psfascii','+log',str(out/'spectre.log')],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError(name+' failed; see '+str(out/'stdout.log'))
 print('SIMULATOR PASS',name,flush=True)
 return name
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--corners',action='store_true');args=p.parse_args()
 (ROOT/'results/operations.json').write_text(json.dumps({'operations':operations()[0],'patterns':operations()[1],'period_ns':50},indent=2))
 jobs=[('array_tt_27',make_deck())]
 if args.corners:jobs += [(f'array_{c}_{t}',make_deck(c,t,selected=['mixed'],scans=1),['mixed'],1) for c,t in [('ff',27),('ss',27),('fs',27),('sf',27),('tt',-40),('tt',125),('ff',-40),('ss',125)]]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda j:run(*j),jobs))
