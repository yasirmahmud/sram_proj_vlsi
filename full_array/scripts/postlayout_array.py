#!/apps/anaconda/bin/python
"""Simulate the actual layout-extracted array through its external interface."""
from pathlib import Path
import sys,re,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from simulate_array import make_deck,run,operations
from analyze_array import read
source=ROOT/'results/physical/sram_4x6/extracted.spice'
lines=[];ports=None
logical=[]
for line in source.read_text().splitlines():
 line=line.split('$',1)[0].strip()
 if not line or line.startswith('*'):continue
 if line.startswith('+'):logical[-1]+=' '+line[1:].strip()
 else:logical.append(line)
for line in logical:
 t=line.split()
 if t[0].lower()=='.subckt':
  cn=t[1]
  if cn=='sram_4x6':ports=t[2:];cn='physical_sram_4x6'
  lines.append('subckt '+cn+' ('+' '.join(t[2:])+')')
 elif t[0].lower()=='.ends':lines.append('ends')
 elif t[0][0].upper()=='M':lines.append(t[0]+' ('+' '.join(t[1:5])+') '+t[5]+' '+' '.join(a.lower() for a in t[6:] if not a.lower().startswith('fw=')))
 elif t[0][0].upper()=='X':lines.append(t[0]+' ('+' '.join(t[1:-1])+') '+t[-1])
 else:raise ValueError('Unexpected extracted line: '+line)
assert ports
public='R1 R0 C2 C1 C0 CLK1 CLK2 WR RD DIN DOUT VDD GND'.split()
assert set(p.upper() for p in ports)==set(public),ports
lines+=['subckt sram_4x6 ('+' '.join(public)+')','Xphysical ('+' '.join(p.upper() for p in ports)+') physical_sram_4x6','ends']
converted=ROOT/'netlists/extracted_design.scs';converted.write_text('simulator lang=spectre\n'+'\n'.join(lines)+'\n')
ops,patterns=operations();state=ops[-1]['expected'].copy()
ops += [{'kind':'read','phase':'post_interlock_readback','addr':a,'bit':b,'expected':state.copy()} for a,b in enumerate(state)]
d=make_deck(include=converted,custom_ops=ops)
d='\n'.join(l for l in d.splitlines() if not l.startswith(('CBL','CG0','CG1','ic ','save ')))+'\nsave '+' '.join(public[:-2])+'\n'
run('array_extracted_tt_27',d,custom_ops=ops)
data=read(ROOT/'results/array_extracted_tt_27/psf/tran.tran.tran');rows=[]
for i,op in enumerate(ops):
 v=float(np.interp((50*i+37)*1e-9,data['time'],data['DOUT']))
 okay=(v>.99 if op['bit'] else v<.11) if op['kind']=='read' else True
 if op['kind'] in ['invalid_read','invalid_write','conflict','overlap']:
  old=float(np.interp((50*i+1)*1e-9,data['time'],data['DOUT']));okay=abs(old-v)<.11
 rows.append({'operation':i,'kind':op['kind'],'phase':op['phase'],'address':op['addr'],'expected_bit':op['bit'],'DOUT_V':v,'pass':bool(okay)})
result={'pass':all(r['pass'] for r in rows),'operations':len(rows),'reads':sum(op['kind']=='read' for op in ops),'writes':sum(op['kind']=='write' for op in ops),'internal_nodes_observed':False,'bitline_load':'intrinsic extracted devices','output_load_fF':10,'rows':rows,'patterns':patterns}
(ROOT/'results/array_extracted_tt_27/checks.json').write_text(json.dumps(result,indent=2))
print('EXTRACTED ARRAY',result['pass'],result['operations'],'operations',result['reads'],'reads',flush=True)
assert result['pass'],[r for r in rows if not r['pass']][:8]
