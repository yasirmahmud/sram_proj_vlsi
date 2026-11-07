"""Generate native, hierarchy-preserving layouts with Manhattan routing."""
from pathlib import Path
import sys,json,math
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from design import C
L={}; CODE=[]
def fmt(x):return f'{x:.6f}'.rstrip('0').rstrip('.') if x else '0.0'
def pt(x,y):return f'list({fmt(x)} {fmt(y)})'
def rect(layer,x1,y1,x2,y2):CODE.append(f'rect(cv "{layer}" {fmt(x1)} {fmt(y1)} {fmt(x2)} {fmt(y2)})')
def wire(layer,x1,y1,x2,y2,w=.08):
 assert abs(x1-x2)<1e-6 or abs(y1-y2)<1e-6
 rect(layer,min(x1,x2)-w/2,min(y1,y2)-w/2,max(x1,x2)+w/2,max(y1,y2)+w/2)
def via(n,x,y):
 # Via1..Via6 are 70 nm square; narrow vertical and horizontal landings.
 rect('Via'+str(n),x-.035,y-.035,x+.035,y+.035)
 for k in [n,n+1]:
  rect('Metal'+str(k),x-(.125 if k%2==0 else .045),y-(.045 if k%2==0 else .125),x+(.125 if k%2==0 else .045),y+(.045 if k%2==0 else .125))
def v12(x,y,gate=False):
 rect('Via1',x-.035,y-.035,x+.035,y+.035)
 rect('Metal1',x-.07 if gate else x-.04,y-.075 if gate else y-.065,x+.07 if gate else x+.04,y+.075 if gate else y+.065)
 rect('Metal2',x-.065,y-.04,x+.065,y+.04)
def v23(x,y):
 rect('Via2',x-.035,y-.035,x+.035,y+.035)
 rect('Metal2',x-.065,y-.04,x+.065,y+.04)
 rect('Metal3',x-.04,y-.065,x+.04,y+.065)
def port(name,layer,x,y):CODE.append(f'port(cv "{name}" "{layer}" {fmt(x)} {fmt(y)})')
def start(name):CODE.append(f'cv=dbOpenCellViewByType("sram_project" "{name}" "layout" "maskLayout" "w")')
def finish(name,w,h,ports):
 rect('prBoundary',0,0,w,h)
 CODE.append(f'dbSave(cv) printf("LAYOUT {name} %L\\n" cv~>bBox) dbClose(cv)')
 L[name]={'width':w,'height':h,'ports':ports}
def flatten(cn,prefix='',mapping=None):
 c=C[cn];mapping=mapping or {p:p for p in c['ports']}
 def node(n):return mapping.get(n,prefix+n)
 out=[]
 for n,d,g,s,b,k,w,l in c['mos']:out.append([prefix+n,node(d),node(g),node(s),node(b),k,w,l])
 for name,child,ns in c['inst']:
  out+=flatten(child,prefix+name+'_',{p:node(n) for p,n in zip(C[child]['ports'],ns)})
 return out

def primitive(name):
 ms=flatten(name);nets=list(C[name]['ports'])
 for m in ms:
  for n in m[1:5]:
   if n not in nets:nets.append(n)
 nx={n:.25+.32*i for i,n in enumerate(nets)}
 nn=[m for m in ms if m[5]=='n'];pp=[m for m in ms if m[5]=='p'];wn=max([m[6]/1000 for m in nn] or [0]);wp=max([m[6]/1000 for m in pp] or [0])
 xd=.32*len(nets)+.40;yn=.45+.32*len(nn);gn=yn+wn+.23;gp=gn+.16*len(nn)+.32;yp=gp+.16*max(len(pp)-1,0)+.30
 sp=yp+wp+.25;end=sp+.32*max(len(pp)-1,0)+.16;H=end+.70;tapx=xd+.7*max(len(nn),len(pp))+.55;W=tapx+.30
 start(name)
 for n,xp in nx.items():wire('Metal3',xp,.10,xp,H-.08,.14)
 def route(xp,sy,ty,net,gate=False):
  wire('Metal1',xp,sy,xp,ty,.14 if gate else .08);v12(xp,ty,gate);wire('Metal2',xp,ty,nx[net],ty);v23(nx[net],ty)
 for bank,arr in [('n',nn),('p',pp)]:
  for i,m in enumerate(arr):
   mn,d,g,s,b,k,ww,ll=m;w=ww/1000;x=xd+.7*i+(.35 if k=='p' else 0);y=yn if k=='n' else yp
   CODE.append(f'dev(cv "{mn}" "{"nmos1v" if k=="n" else "pmos1v"}" {fmt(x)} {fmt(y)} {ww} {ll})')
   ts=.35+.32*i if k=='n' else sp+.32*i;td=ts+.16
   route(x-.08,y+w/2,ts,s);route(x+.125,y+w/2,td,d)
   gy=gn if k=='n' else yp-.23;gt=gn+.16*i if k=='n' else gp+.16*i
   if k=='n':rect('Poly',x,y+w+.05,x+.045,gy+.10)
   else:rect('Poly',x,gy-.10,x+.045,y-.05)
   rect('Poly',x-.05,gy-.10,x+.09,gy+.10);rect('Cont',x-.01,gy-.03,x+.05,gy+.03)
   # The contact must satisfy minimum area even when its routing via is remote.
   rect('Metal1',x-.05,gy-.075,x+.09,gy+.075)
   route(x+.02,gy,gt,g,True)
 if pp:
  rect('Nwell',xd-.25,yp-.20,tapx+.22,yp+max(wp,.35)+.20)
  cy=yp+.17;rect('Oxide',tapx-.1,cy-.1,tapx+.1,cy+.1);rect('Nimp',tapx-.16,cy-.16,tapx+.16,cy+.16);rect('Cont',tapx-.03,cy-.03,tapx+.03,cy+.03)
  rect('Metal1',tapx-.04,cy-.065,tapx+.04,cy+.065)
  route(tapx,cy,H-.30,'VDD')
 cy=yn+.17;rect('Oxide',tapx-.1,cy-.1,tapx+.1,cy+.1);rect('Pimp',tapx-.16,cy-.16,tapx+.16,cy+.16);rect('Cont',tapx-.03,cy-.03,tapx+.03,cy+.03)
 rect('Metal1',tapx-.04,cy-.065,tapx+.04,cy+.065)
 route(tapx,cy,.12,'GND')
 ports={p:[nx[p],H-.08,'Metal3'] for p in C[name]['ports']}
 for p,(x,y,l) in ports.items():port(p,l,x,y)
 finish(name,W,H,ports)

def inst(name,child,x,y):CODE.append(f'dbCreateInst(cv dbOpenCellViewByType("sram_project" "{child}" "layout" "" "r") "{name}" {pt(x,y)} "R0")')
def macro(name,top=False):
 c=C[name];children=c['inst'];ports=c['ports'];bank=.32*len(ports)+.55
 nets=list(ports)
 for _,ch,ns in children:
  for n in ns:
   if n not in nets:nets.append(n)
 placements=[]
 if not top:
  xx=bank
  for n,ch,ns in children:placements.append((n,ch,ns,xx,.35));xx+=L[ch]['width']+.40
  W=xx;maxH=max(y+L[ch]['height'] for _,ch,ns,x,y in placements)
 else:
  # Enumerate shelf counts; choose the smallest legal boundary with unique
  # global routing columns for all child ports.
  candidates=[]
  for nr in [1,2,3,4]:
   shelves=[[] for _ in range(nr)];end=[bank]*nr;used=set();assign=[]
   for n,ch,ns in sorted(children,key=lambda z:L[z[1]]['width'],reverse=True):
    options=[]
    for r in range(nr):
     xx=math.ceil(end[r]/.32)*.32
     while any(round((xx+L[ch]['ports'][p][0])/.32) in used for p in C[ch]['ports']):xx+=.32
     options.append((max(max(end),xx+L[ch]['width']+.4),xx,r))
    _,xx,r=min(options);shelves[r].append((n,ch,ns,xx));end[r]=xx+L[ch]['width']+.4
    used.update(round((xx+L[ch]['ports'][p][0])/.32) for p in C[ch]['ports'])
   yy=.35;pl=[]
   for shelf in shelves:
    if not shelf:continue
    for n,ch,ns,xx in shelf:pl.append((n,ch,ns,xx,yy))
    yy+=max(L[ch]['height'] for n,ch,ns,xx in shelf)+.55
   h=yy+.16*len(nets)+.8;w=max(end);candidates.append((w*h,w,h,pl))
  _,W,_,placements=min(candidates,key=lambda a:a[0]);maxH=max(y+L[ch]['height'] for _,ch,ns,x,y in placements)
 tracks={n:maxH+.40+.16*i for i,n in enumerate(nets)};H=max(tracks.values())+.50
 start(name)
 for n,ch,ns,xx,yy in placements:inst(n,ch,xx,yy)
 sites={n:[] for n in nets}
 for n,ch,ns,xx,yy in placements:
  for pin,net in zip(C[ch]['ports'],ns):
   px,py,ly=L[ch]['ports'][pin];assert ly=='Metal3'
   px+=xx;py+=yy;ty=tracks[net];sites[net].append((px,py))
   if top:
    for level in [3,4,5,6]:via(level,px,py)
    wire('Metal7',px,py,px,ty,.08);via(6,px,ty)
   else:
    via(3,px,py);via(4,px,py)
    wire('Metal5',px,py,px,ty,.08);via(4,px,ty)
 outports={}
 for net,ss in sites.items():
  xs=[x for x,y in ss]
  if net in ports:xs.append(.25+.32*ports.index(net))
  if not xs:continue
  yy=tracks[net];wire('Metal6' if top else 'Metal4',min(xs),yy,max(xs),yy,.08)
  if net in ports:
   px=.25+.32*ports.index(net);outports[net]=[px,H-.08,'Metal3']
   if top:
    via(5,px,yy);via(4,px,yy);via(3,px,yy)
   else:via(3,px,yy)
   wire('Metal3',px,yy,px,H-.08,.14);port(net,'Metal3',px,H-.08)
 finish(name,W,H,outports)
 L[name]['placements']=[{'name':n,'cell':ch,'x':x,'y':y} for n,ch,ns,x,y in placements]

def bitcell():
 CODE.extend(['src=dbOpenCellViewByType("sram_cell" "sram_cell" "layout" "" "r")','cv=dbCopyCellView(src "sram_project" "bitcell" "layout" nil nil t)','foreach(te cv~>terminals when(te~>name=="Vdd" te~>name="VDD" dbRenameNet(te~>net "VDD")))','foreach(s cv~>shapes when(s~>objType=="label" && s~>theLabel=="Vdd" s~>theLabel="VDD"))','dbSave(cv) dbClose(cv)'])
 L['bitcell']={'width':2.12,'height':1.68,'ports':{}}

def memory():
 name='bit_array';ports=C[name]['ports'];bank=.32*len(ports)+.55;ox=bank;oy=.35;pitchx=2.30;pitchy=2.02;bodyH=oy+3*pitchy+1.68
 start(name)
 for r in range(4):
  for c in range(6):inst(f'B{r}_{c}','bitcell',ox+c*pitchx,oy+r*pitchy)
 def access(x,y,vertical=False):
  rect('Via1',x-.035,y-.035,x+.035,y+.035)
  rect('Metal1',x-.04 if vertical else x-.065,y-.065 if vertical else y-.04,x+.04 if vertical else x+.065,y+.065 if vertical else y+.04)
  rect('Metal2',x-.125,y-.045,x+.125,y+.045);v23(x,y)
 sites={p:[] for p in ports};tracks={p:bodyH+.35+.16*i for i,p in enumerate([p for p in ports if not p.startswith('WL')])}
 for r in range(4):
  yy=oy+r*pitchy+.105;px=.25+.32*ports.index(f'WL{r}')
  wire('Metal2',px,yy,ox+5*pitchx+1.945,yy);v23(px,yy);sites[f'WL{r}'].append((px,yy))
 for c in range(6):
  for p,rx,ry,v in [(f'BLB{c}',.135,.81,True),(f'BL{c}',1.99,1.14,True),('VDD',.89,1.62,False),('GND',.70,.37,False)]:
   xx=ox+c*pitchx+rx
   for r in range(4):access(xx,oy+r*pitchy+ry,v)
   yy=tracks[p];wire('Metal3',xx,oy+ry,xx,yy,.08);v23(xx,yy);sites[p].append((xx,yy))
 H=max(tracks.values())+.5;W=ox+5*pitchx+2.3;out={}
 for p in ports:
  px=.25+.32*ports.index(p);ss=sites[p]
  if not p.startswith('WL'):
   yy=tracks[p];wire('Metal2',px,yy,max(x for x,y in ss),yy);v23(px,yy)
  else:yy=ss[0][1]
  wire('Metal3',px,yy,px,H-.08,.14);port(p,'Metal3',px,H-.08);out[p]=[px,H-.08,'Metal3']
 finish(name,W,H,out)

HEADER='''procedure(rect(cv layer x1 y1 x2 y2) dbCreateRect(cv list(layer "drawing") list(list(x1 y1) list(x2 y2))))
procedure(dev(cv name kind x y w l)
 dbCreateParamInst(cv dbOpenCellViewByType("gpdk045" kind "layout" "" "r") name list(x y) "R0" 1 list(list("fw" "float" w*1e-9) list("l" "float" l*1e-9))))
procedure(port(cv name layer x y)
 let((net fig)
 net=dbCreateNet(cv name) dbCreateTerm(net name "inputOutput")
 fig=dbCreateRect(cv list(layer "pin") list(list(x-.065 y-.065) list(x+.065 y+.065))) dbCreatePin(net fig name)
 dbCreateLabel(cv list(layer "label") list(x y) name "centerCenter" "R0" "roman" .06)))
'''
if __name__=='__main__':
 for n in ['inv','nand3','nand2','and3','tg','precharge_unit','sense_amp']:primitive(n)
 bitcell();memory()
 for n in ['read_latch','row_decoder','column_decoder','rw_control','write_driver','column_mux','precharge']:macro(n)
 macro('sram_4x6',True)
 (ROOT/'scripts/build_layout_generated.il').write_text(HEADER+'\n'.join(CODE)+'\nexit()\n')
 (ROOT/'results/layout_metadata.json').write_text(json.dumps(L,indent=2))
 print('Generated layouts:',{n:[round(x['width'],2),round(x['height'],2)] for n,x in L.items()})
