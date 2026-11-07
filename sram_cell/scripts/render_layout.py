#!/apps/anaconda/bin/python
from pathlib import Path
import sys,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.python_packages'))
import gdstk
lib=gdstk.read_gds(str(ROOT/'results/sram_cell.gds')); top=next(c for c in lib.cells if c.name=='sram_cell')
colors={2:('#d9c9ed','N-well'),1:('#b5d6ac','Active'),3:('#ec8b83','Poly'),4:('#c4ecd4','N implant'),5:('#f1d7b8','P implant'),6:('#292929','Contact'),7:('#466bc7','Metal1'),8:('#151515','Via1'),9:('#d79a2a','Metal2'),10:('#151515','Via2'),11:('#46a883','Metal3')}
fig,ax=plt.subplots(figsize=(10,7))
polys=top.get_polygons()
for layer in [2,4,5,1,3,7,9,11,6,8,10]:
 for p in polys:
  if p.layer==layer and p.datatype==0:ax.add_patch(Polygon(p.points,facecolor=colors[layer][0],edgecolor=colors[layer][0],alpha=.40 if layer in [2,4,5,11] else .85,lw=.5))
for label in top.labels:
 ax.text(*label.origin,label.text,va='bottom',ha='center',fontsize=7)
for name,x,y in [('PM0',.80,1.355),('PM1',1.36,1.355),('NM0',.80,.46),('NM1',1.315,.46),('NM2',.215,.73),('NM3',1.86,1.065)]:ax.text(x+.08,y+.06,name,fontsize=7)
ax.set(xlim=(-.06,2.18),ylim=(-.06,1.74),xlabel='x (µm)',ylabel='y (µm)',title='6T SRAM: flattened GDS, explicit well and substrate taps')
ax.set_aspect('equal');ax.legend(handles=[Patch(color=v[0],label=v[1]) for v in colors.values()],loc='center left',bbox_to_anchor=(1,.5),fontsize=8);fig.tight_layout();fig.savefig(ROOT/'results/figures/layout_layers.png',dpi=180)
# Check single poly orientation on the actual streamed polygons.
poly=[]
for p in polys:
 if p.layer==3 and p.datatype==0:
  size=np.ptp(p.points,axis=0); poly.append(bool(size[1]>=size[0]))
assert poly and all(poly),'Nonvertical poly shape found in GDS'
print('PASS: all',len(poly),'poly rectangles have vertical orientation')

# Capture geometric evidence from the same streamed layout used for verification.
boundary=next(p for p in polys if p.layer==99 and p.datatype==0).bounding_box()
size=np.subtract(boundary[1],boundary[0]);assert np.allclose(size,[2.12,1.68])
(ROOT/'results/layout_geometry.json').write_text(json.dumps({'boundary_um':[list(boundary[0]),list(boundary[1])],'dimensions_um':size.tolist(),'area_um2':float(np.prod(size)),'vertical_poly_rectangles':len(poly),'all_poly_vertical':all(poly),'gds_sha256':hashlib.sha256((ROOT/'results/sram_cell.gds').read_bytes()).hexdigest()},indent=2))
