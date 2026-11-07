#!/apps/anaconda/bin/python
from pathlib import Path
import re,json,gzip,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def read(path):
 p=Path(path)
 cache=p.parent.parent/'waveforms.npz'
 if cache.exists():
  with np.load(cache) as z:return {k:z[k] for k in z.files}
 if not p.exists():p=Path(str(p)+'.gz')
 op=gzip.open if p.suffix=='.gz' else open
 d={};active=False;rx=re.compile(r'^"([^"\n]+)"\s+([-+\deE.]+)\s*$')
 with op(p,'rt') as f:
  for line in f:
   if not active:
    if line.strip()=='VALUE':active=True
    continue
   if line.strip()=='END':break
   m=rx.match(line)
   if m:d.setdefault(m[1],[]).append(float(m[2]))
 data={k:np.asarray(v) for k,v in d.items()}
 np.savez_compressed(cache,**data)
 return data

def analyze(name,vdd=1.1):
 d=read(ROOT/'results'/name/'psf/tran.tran.tran');opfile=ROOT/'results'/name/'operations.json'
 if not opfile.exists():opfile=ROOT/'results/operations.json'
 spec=json.loads(opfile.read_text());ops=spec['operations'];time=d['time']
 def at(s,t):return float(np.interp(t,time,d[s]))
 rows=[];fails=[]
 for i,op in enumerate(ops):
  t=(i*50+37)*1e-9;wrong=[];levels=[]
  for a,bit in enumerate(op['expected']):
   r,c=divmod(a,6);q=at(f'Xchip.XMEM.Q{r}_{c}',t);qb=at(f'Xchip.XMEM.QB{r}_{c}',t)
   good=(q>.9*vdd and qb<.1*vdd) if bit else (q<.1*vdd and qb>.9*vdd)
   if not good:wrong.append({'address':a,'expected':bit,'Q':q,'QB':qb})
   levels.append(q)
  out=at('DOUT',t);outpass=not(op['kind']=='read') or (out>.9*vdd if op['bit'] else out<.1*vdd)
  wl=[at(f'Xchip.WL{r}',t) for r in range(4)];cs=[at(f'Xchip.CS{c}',t) for c in range(6)]
  inactive=op['kind'] in ['invalid_read','invalid_write','conflict','overlap']
  ctrlpass=(max(wl)<.1*vdd and at('Xchip.WEN',t)<.1*vdd and at('Xchip.REN',t)<.1*vdd) if inactive else (sum(x>.9*vdd for x in wl)==1)
  colpass=(max(cs)<.1*vdd) if op['kind'].startswith('invalid') else (sum(x>.9*vdd for x in cs)==1)
  okay=not wrong and outpass and ctrlpass and colpass
  row={'operation':i,'kind':op['kind'],'phase':op['phase'],'address':op['addr'],'expected_bit':op['bit'],'DOUT_V':out,'storage_pass':not wrong,'read_pass':bool(outpass),'control_pass':bool(ctrlpass and colpass),'pass':bool(okay),'wrong_cells':wrong}
  rows.append(row)
  if not okay:fails.append(row)
 result={'name':name,'pass':not fails,'operations':len(rows),'valid_write_operations':sum(x['kind']=='write' for x in ops),'valid_read_operations':sum(x['kind']=='read' for x in ops),'patterns':spec['patterns'],'rows':rows,'failures':fails}
 (ROOT/'results'/name/'checks.json').write_text(json.dumps(result,indent=2))
 print(name,'PASS' if result['pass'] else 'FAIL',len(rows),'operations;',len(fails),'failures',flush=True)
 for r in fails[:8]:print({k:v for k,v in r.items() if k!='wrong_cells'},r['wrong_cells'][:2],flush=True)
 return result
if __name__=='__main__':
 name=sys.argv[1] if len(sys.argv)>1 else 'array_tt_27';r=analyze(name)
 if not r['pass']:raise SystemExit(1)
