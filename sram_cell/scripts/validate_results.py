#!/apps/anaconda/bin/python
"""Fail if the saved design evidence is incomplete or inconsistent."""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results'
m=json.loads((RES/'metrics.json').read_text());checks={}
geometry=json.loads((RES/'layout_geometry.json').read_text())
assert geometry['all_poly_vertical'] and geometry['dimensions_um']==[2.12,1.68]
assert geometry['gds_sha256']==hashlib.sha256((RES/'sram_cell.gds').read_bytes()).hexdigest()
for label,folder in [('final','drc'),('default','default_drc')]:
 s=(RES/folder/'summary.txt').read_text()
 checks[label+'_drc']=bool(re.search(r'Total DRC RuleChecks\s*:\s*562',s) and re.search(r'Total DRC Results\s*:\s*0 \(0\)',s))
for label,folder in [('final','lvs'),('default','default_lvs')]:checks[label+'_lvs']=bool(re.search(r'Run Result\s*:\s*MATCH',(RES/folder/'report.txt.cls').read_text()))
s=(RES/'finalize_native.log').read_text()
for name in ['sram_cell','sram_cell_default']:checks[name+'_native_check']=f'NATIVE_CHECK {name} (0 0)' in s
assert len(m['functional'])==17,len(m['functional'])
checks['all_physical_functional_runs']=all(v['pass'] for v in m['functional'].values())
checks['single_orientation_poly']='PASS: all 42 poly rectangles have vertical orientation' in (RES/'layout_render.log').read_text()
checks['all_timing_crossings_found']=all(v['delay_ps'] is not None and v['delay_ps']>0 for k in ['write_50pct','read_forced_50pct','write_default_50pct','extracted_write_50pct','physical_50pct'] for v in m[k].values())
from project_paths import model_file, INSTALLED_MODEL
required=model_file();installed=INSTALLED_MODEL
checks['supplied_model_matches_installed_pdk']=required.read_bytes()==installed.read_bytes()
runs=[];warnings={}
for p in sorted(RES.glob('*/spectre.log')):
 s=p.read_text();match=re.search(r'spectre completes with (\d+) errors, (\d+) warnings',s)
 checks['sim_'+p.parent.name]=bool(match and int(match[1])==0 and int(match[2])==0)
 if match and int(match[2]):warnings[p.parent.name]=int(match[2])
 runs.append(p.parent.name)
for off in [.1,.2,.3,.4]:
 for v in [.2,.3,.4,.5,.6,.7,.8,.9]:assert f'mismatch_{off:.1f}_{v:.1f}' in runs
for v in [0,.275,.55,.825,1.1]:assert f'vdd_coarse_{v:.3f}' in runs
summary={'pass':all(checks.values()),'checks':checks,'simulation_runs':len(runs),'functional_runs':17,'corner_combinations':15,'corner_write_read_cycles':120,'poly_rectangles_vertical':42,'layout_boundary_um':geometry['dimensions_um'],'layout_area_um2':geometry['area_um2'],'model_sha256':hashlib.sha256(required.read_bytes()).hexdigest(),'simulator_warnings':warnings}
(RES/'validation_summary.json').write_text(json.dumps(summary,indent=2))
(RES/'run_manifest.json').write_text(json.dumps({'jobs':runs,'model':str(required),'spectre':'/apps/cds/spectre211/bin/spectre'},indent=2))
print('PASS' if summary['pass'] else 'FAIL',len(checks),'checks;',len(runs),'Spectre runs;',len(warnings),'runs with warnings')
assert summary['pass'],[k for k,v in checks.items() if not v]
