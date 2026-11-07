#!/apps/anaconda/bin/python
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from simulate_array import make_deck,run
state=[0]*24;ops=[]
for kind,bit in [('write',1),('read',1),('write',0),('read',0)]:
 state[0]=bit;ops.append(dict(kind=kind,phase='timing',addr=0,bit=bit,expected=state.copy()))
d=make_deck(custom_ops=ops,strobe=False).replace('maxstep=500p errpreset=moderate','maxstep=5p errpreset=conservative')
d='\n'.join(l for l in d.splitlines() if not l.startswith('save '))+'\nsave CLK1 CLK2 WR RD DIN DOUT Xchip.GBL Xchip.GBLB Xchip.BL0 Xchip.BLB0 Xchip.WL0 Xchip.WEN Xchip.REN Xchip.SENSE Xchip.XMEM.Q0_0 Xchip.XMEM.QB0_0\n'
d=d.replace('ic Xchip.', 'ic DOUT=0 Xchip.XLATCH.n0=0 Xchip.XLATCH.nb=vdd Xchip.',1)
run('array_timing',d,custom_ops=ops)
