#!/apps/anaconda/bin/python
"""Functional transistor-level tests of the individual building blocks."""
from pathlib import Path
import sys,itertools,json,concurrent.futures
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from simulate_array import run,wave
from design import C,model_file
from analyze_array import read

def testcases(cell):
 if cell=='inv':return [({'IN':i},{'OUT':1-i}) for i in [0,1,0,1]]
 if cell in ['nand2','nand3','and3']:
  ins=['A','B'] if cell=='nand2' else ['A','B','E'];return [(dict(zip(ins,b)),{'Y':int(all(b)) if cell=='and3' else 1-int(all(b))}) for b in itertools.product([0,1],repeat=len(ins))]
 if cell=='row_decoder':return [({'R1':r>>1,'R0':r&1,'EN':en},{f'WL{i}':int(en and i==r) for i in range(4)}) for en in [0,1] for r in range(4)]
 if cell=='column_decoder':return [({'C2':c>>2,'C1':(c>>1)&1,'C0':c&1},{f'CS{i}':int(i==c) for i in range(6)}) for c in range(8)]
 if cell=='rw_control':
  out=[]
  for b in itertools.product([0,1],repeat=6):
   clk,pre,wr,rd,c2,c1=b;valid=not(c2 and c1);we=int(clk and not pre and wr and not rd and valid);re=int(clk and not pre and rd and not wr and valid)
   out.append((dict(zip(['CLK1','CLK2','WR','RD','C2','C1'],b)),{'WEN':we,'WENB':1-we,'REN':re,'RENB':1-re,'ROWEN':we|re,'PCB':1-pre}))
  return out
 if cell=='sense_amp':return [({'BIT':a/1.1,'BIT_bar':b/1.1,'RE':1},{'AMP_OUT':int(a>b)}) for a,b in [(1.1,0),(0,1.1),(1.1,1.0),(1.0,1.1),(.8,.7),(.7,.8)]]
 raise ValueError(cell)
def unit(cell):
 cases=testcases(cell);inputs=list(cases[0][0]);outs=list(cases[0][1]);seq={p:[(0,cases[0][0][p])] for p in inputs}
 for i,(iv,ov) in enumerate(cases[1:],1):
  for p in inputs:
   old=seq[p][-1][1];val=iv[p]
   if val!=old:seq[p].extend([(10*i,old),(10*i+.1,val)])
 for p in seq:seq[p].append((10*len(cases),seq[p][-1][1]))
 d=f'simulator lang=spectre\ninclude "{model_file()}" section=tt\ninclude "{ROOT/"netlists/design.scs"}"\nparameters vdd=1.1\nVDD (VDD 0) vsource dc=vdd\nsimOptions options reltol=1e-3 temp=27\n'
 d+=''.join(wave(p,p,s) for p,s in seq.items())
 d+='Xunit ('+' '.join('0' if p=='GND' else p for p in C[cell]['ports'])+') '+cell+'\n'
 for p in outs:d+=f'CL{p} ({p} 0) capacitor c=5f\n'
 d+=f'tran tran stop={10*len(cases)}n maxstep=100p errpreset=moderate strobeperiod=100p\nsave '+' '.join(inputs+outs)+'\n'
 name='unit_'+cell;run(name,d);data=read(ROOT/'results'/name/'psf/tran.tran.tran');checks=[]
 for i,(iv,ov) in enumerate(cases):
  t=(10*i+8)*1e-9;measured={p:float(np.interp(t,data['time'],data[p])) for p in outs};ok=all(measured[p]>.99 if bit else measured[p]<.11 for p,bit in ov.items());checks.append({'inputs':iv,'expected':ov,'measured_V':measured,'pass':bool(ok)})
 result={'cell':cell,'pass':all(r['pass'] for r in checks),'checks':checks}
 (ROOT/'results'/name/'unit_checks.json').write_text(json.dumps(result,indent=2));print('UNIT',cell,result['pass'],flush=True)
 return result
if __name__=='__main__':
 cells=['inv','nand2','nand3','and3','row_decoder','column_decoder','rw_control','sense_amp']
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(unit,cells))
 (ROOT/'results/unit_summary.json').write_text(json.dumps(results,indent=2))
 assert all(r['pass'] for r in results)
