#!/apps/anaconda/bin/python
"""Audit measured results, native checks, and actual streamed geometries."""
from pathlib import Path
import sys,re,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent/'sram_cell/.python_packages'));sys.path.insert(0,str(Path(__file__).resolve().parent))
import gdstk
from design import C
R=ROOT/'results';checks={};physical=[]
for cn in C:
 out=R/'physical'/cn;r=json.loads((out/'checks.json').read_text());checks['drc_'+cn]=r['drc_pass'];checks['lvs_'+cn]=r.get('lvs_pass',False)
 physical.append({'cell':cn,'drc_results':r['drc_results'],'lvs':'MATCH' if r.get('lvs_pass') else 'FAIL'})
 native=(R/'build_native.log').read_text();checks['native_'+cn]=f'CHECK {cn} (0 0)' in native
cases=['array_tt_27','array_ff_-40','array_ss_125','array_fs_27','array_sf_27','array_tt_-40','array_tt_125','array_ff_27','array_ss_27']
ops=0
for n in cases:
 r=json.loads((R/n/'checks.json').read_text());checks[n]=r['pass'];ops+=r['operations']
units=json.loads((R/'unit_summary.json').read_text())
for r in units:checks['unit_'+r['cell']]=r['pass']
pex=json.loads((R/'array_extracted_tt_27/checks.json').read_text());checks['extracted_array']=pex['pass'];assert pex['reads']==168
metrics=json.loads((R/'full_metrics.json').read_text());checks['timing_markers']=all(m['delay_ns']>0 for m in metrics['timing'].values());checks['precharge_to_vdd']=metrics['precharge_all_bitlines_min_V']>1.089;checks['output_hold']=metrics['latch_hold_pass']
logs=cases+['array_extracted_tt_27','array_timing']+['unit_'+r['cell'] for r in units]
for n in logs:
 text=(R/n/'spectre.log').read_text();ma=re.search(r'spectre completes with (\d+) errors, (\d+) warnings',text);checks['simulator_'+n]=bool(ma and ma[1]=='0' and ma[2]=='0')
gds=R/'physical/sram_4x6/layout.gds';lib=gdstk.read_gds(str(gds));top=next(c for c in lib.cells if c.name=='sram_4x6');pp=top.get_polygons();poly=[p for p in pp if p.layer==3 and p.datatype==0]
checks['single_orientation_poly']=bool(poly) and all(np.ptp(p.points,axis=0)[1]>=np.ptp(p.points,axis=0)[0] for p in poly)
metal={}
for layer,number in [(9,2),(11,3),(31,4),(33,5),(35,6),(38,7)]:
 shapes=[p for p in pp if p.layer==layer and p.datatype==0];horizontal=number%2==0
 metal['Metal'+str(number)]=all((np.ptp(p.points,axis=0)[0]>=np.ptp(p.points,axis=0)[1]) if horizontal else (np.ptp(p.points,axis=0)[1]>=np.ptp(p.points,axis=0)[0]) for p in shapes)
 # Via landings are deliberately aligned with each layer's routing direction.
 checks['orientation_Metal'+str(number)]=metal['Metal'+str(number)]
boundary=next(p for p in top.polygons if p.layer==99 and p.datatype==0).bounding_box();wh=np.subtract(boundary[1],boundary[0]);lm=json.loads((R/'layout_metadata.json').read_text())['sram_4x6'];checks['layout_boundary']=bool(np.allclose(wh,[lm['width'],lm['height']]))
raw=(R/'physical/sram_4x6/extracted.spice').read_text();nmos=len(re.findall(r'^M\S+ ',raw,re.M));checks['extracted_transistor_count']=nmos==metrics['transistors']==371
checks['address_coverage']=json.loads((R/'array_tt_27/checks.json').read_text())['valid_read_operations']==144
summary={'pass':all(checks.values()),'checks':checks,'physical':physical,'functional_cases':cases,'nominal_operations':244,'corner_operations':ops,'extracted_operations':pex['operations'],'extracted_read_operations':pex['reads'],'unit_vectors':sum(len(r['checks']) for r in units),'simulator_runs':len(logs),'transistors':nmos,'layout_dimensions_um':wh.tolist(),'layout_area_um2':float(np.prod(wh)),'vertical_poly_shapes':len(poly),'metal_orientation':metal,'layout_gds_sha256':hashlib.sha256(gds.read_bytes()).hexdigest()}
(R/'validation_summary.json').write_text(json.dumps(summary,indent=2))
print('PASS' if summary['pass'] else 'FAIL',len(checks),'checks;',len(logs),'Spectre runs;',len(physical),'DRC/LVS cells;',ops,'schematic operations;',pex['operations'],'extracted operations')
assert summary['pass'],[k for k,v in checks.items() if not v]
