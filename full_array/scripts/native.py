"""Generate readable hierarchical Virtuoso schematics and reusable symbols."""
from pathlib import Path
import sys,math
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from design import C

def q(s):return '"'+str(s).replace('\\','\\\\').replace('"','\\"')+'"'
def sx(x):
 if isinstance(x,list):return 'list('+' '.join(sx(v) for v in x)+')'
 if isinstance(x,str):return q(x)
 return str(x)
symbol_h={}
code=['''procedure(stub(cv inst pinName netName)
 let((te pos end delta wires)
 te=dbFindTermByName(inst~>master pinName)
 unless(te error("Missing pin %s/%s" inst~>cellName pinName))
 pos=dbTransformPoint(centerBox(car(te~>pins)~>fig~>bBox) inst~>transform)
 delta=cond((pinName=="D" list(0.0 .35)) (pinName=="S" list(0.0 -.35)) (pinName=="B" list(.40 0.0)) (t list(-.40 0.0)))
 when(inst~>cellName=="pmos1v"
  when(pinName=="D" delta=list(0.0 -.35))
  when(pinName=="S" delta=list(0.0 .35)))
 when(inst~>libName=="sram_project"
   delta=if(te~>direction=="output" || member(pinName '("Q" "Q_bar")) then list(.40 0.0) else list(-.40 0.0))
   when(pinName=="VDD" delta=list(0.0 .40))
   when(pinName=="GND" delta=list(0.0 -.40)))
 end=list(car(pos)+car(delta) cadr(pos)+cadr(delta))
 wires=schCreateWire(cv "draw" "direct" list(pos end) .0625 .0625 0.0)
 schCreateWireLabel(cv car(dbGetOverlaps(cv list(end end) '("wire" "drawing"))) end netName "lowerLeft" "R0" "stick" .10 nil) end))
''']
for name,c in C.items():
 ports=c['ports'];dirs=c['directions']
 left=[p for p in ports if p not in ['VDD','GND'] and dirs.get(p)!='output' and not p.startswith('Q')]
 right=[p for p in ports if p not in ['VDD','GND'] and p not in left]
 H=max(len(left),len(right),2)*.5+1
 symbol_h[name]=H
 code.append(f's=dbOpenCellViewByType("sram_project" "{name}" "symbol" "schematicSymbol" "w")')
 code.append(f'dbCreateRect(s \'("device" "drawing") list(list(0.0 0.0) list(4.0 {H})))')
 code.append(f'dbCreateLabel(s \'("device" "drawing") list(2.0 {H/2}) "{name}" "centerCenter" "R0" "roman" .18)')
 for side,pp in [('left',left),('right',right),('top',['VDD']),('bottom',['GND'])]:
  for j,p in enumerate(pp):
   if side=='left':x,y=-.25,H-.5-j*.5;lx,ly=.1,y;align='centerLeft';ex,ey=0,y
   elif side=='right':x,y=4.25,H-.5-j*.5;lx,ly=3.9,y;align='centerRight';ex,ey=4,y
   elif side=='top':x,y=2,H+.25;lx,ly=2,H-.2;align='centerCenter';ex,ey=2,H
   else:x,y=2,-.25;lx,ly=2,.2;align='centerCenter';ex,ey=2,0
   direction=dirs.get(p,'input');stype='power' if p=='VDD' else 'ground' if p=='GND' else 'signal'
   code.append(f'schCreateSymbolPin(s dbOpenCellViewByType("basic" "sympin" "symbol" "" "r") "{p}" "{direction}" list({x} {y}) "R0" t nil nil "{stype}")')
   code.append(f'dbCreateLine(s \'("device" "drawing") list(list({x} {y}) list({ex} {ey})))')
   code.append(f'dbCreateLabel(s \'("device" "drawing") list({lx} {ly}) "{p}" "{align}" "R0" "roman" .14)')
 code.append('dbSave(s) dbClose(s)')
for name,c in C.items():
 code.append(f'cv=dbOpenCellViewByType("sram_project" "{name}" "schematic" "schematic" "w")')
 for j,m in enumerate(c['mos']):
  mn,d,g,s,b,k,w,l=m;xx=4+(j%4)*5;yy=-3-(j//4)*5
  code.append(f'i=schCreateInst(cv dbOpenCellViewByType("gpdk045" "{"nmos1v" if k=="n" else "pmos1v"}" "symbol" "" "r") "{mn}" list({xx} {yy}) "R0")')
  code.append(f'dbReplaceProp(i "w" "string" "{w}n") dbReplaceProp(i "l" "string" "{l}n")')
  for pn,net in zip(['D','G','S','B'],[d,g,s,b]):code.append(f'stub(cv i "{pn}" "{net}")')
 row_y={}
 yy0=-3
 for r in range((len(c['inst'])+2)//3):
  hh=max(symbol_h[z[1]] for z in c['inst'][r*3:r*3+3]);yy0-=hh;row_y[r]=yy0;yy0-=3
 for j,(mn,ch,ns) in enumerate(c['inst']):
  if name=='bit_array':xx=5+(j%6)*8;yy=-4-(j//6)*8
  else:xx=5+(j%3)*10;yy=row_y[j//3]
  code.append(f'i=schCreateInst(cv dbOpenCellViewByType("sram_project" "{ch}" "symbol" "" "r") "X{mn}" list({xx} {yy}) "R0")')
  for pin,net in zip(C[ch]['ports'],ns):
   code.append(f'end=stub(cv i "{pin}" "{net}")')
   if name=='bit_array' and pin in ['Q','Q_bar']:
    code.append(f'schCreateInst(cv dbOpenCellViewByType("basic" "noConn" "symbol" "" "r") "NC_{mn}_{pin}" end "R0")')
 for j,p in enumerate(c['ports']):
  dr=c['directions'].get(p,'input');master='ipin' if dr=='input' else 'opin' if dr=='output' else 'iopin';stype='power' if p=='VDD' else 'ground' if p=='GND' else 'signal'
  xx=-3;yy=2-j*.5
  code.append(f'schCreatePin(cv dbOpenCellViewByType("basic" "{master}" "symbol" "" "r") "{p}" "{dr}" nil list({xx} {yy}) "R0" nil nil "{stype}")')
 if name=='precharge_unit':
  code.append('schCreateInst(cv dbOpenCellViewByType("basic" "noConn" "symbol" "" "r") "NC_GND" list(-3.0 0.0) "R0")')
 code.append('dbSave(cv) dbClose(cv)')
# Connectivity extraction requires children to be checked before their parents.
for name in C:
 code.append(f'cv=dbOpenCellViewByType("sram_project" "{name}" "schematic" "" "a") printf("CHECK {name} %L\\n" schCheck(cv)) dbSave(cv) dbClose(cv)')
code.append('exit()')
(ROOT/'scripts/build_native_generated.il').write_text('\n'.join(code)+'\n')
print('Native schematic/symbol generator ready')
