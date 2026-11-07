#!/apps/anaconda/bin/python
"""Run independent GPDK045 DRC and LVS jobs in isolated working directories."""
from pathlib import Path
import os,sys,re,json,subprocess,concurrent.futures,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from design import C
PG='/apps/cds/pegasus251/tools/bin/pegasus';ST='/apps/cds/IC618/tools/dfII/bin/strmout'
ENV=os.environ.copy();ENV.setdefault('CDS_LIC_FILE','5280@ece-itop-licsvr.ece.ufl.edu');ENV['CDSHOME']='/apps/cds/IC618'
ENV['CDS_Netlisting_Mode']='Analog'

def export_native():
 lines=['f=outfile("netlists/native.cdl")']
 for cn,c in C.items():
  lines += [f'cv=dbOpenCellViewByType("sram_project" "{cn}" "schematic" "" "r")',f'fprintf(f ".SUBCKT {cn} '+ ' '.join(c['ports'])+'\\n")']
  for mn,*rest in c['mos']:
   lines+= [f'i=dbFindAnyInstByName(cv "{mn}")',f'fprintf(f "M{mn}")','foreach(pn \'("D" "G" "S" "B") ti=car(setof(xx i~>instTerms xx~>name==pn)) fprintf(f " %s" ti~>net~>name))',f'fprintf(f " g45{rest[4]}1svt W=%s L=%s\\n" cdfGetInstCDF(i)~>w~>value cdfGetInstCDF(i)~>l~>value)']
  for mn,ch,ns in c['inst']:
   lines+=[f'i=dbFindAnyInstByName(cv "X{mn}")',f'fprintf(f "X{mn}")', 'foreach(pn \'('+ ' '.join('"'+p+'"' for p in C[ch]['ports'])+') ti=car(setof(xx i~>instTerms xx~>name==pn)) fprintf(f " %s" ti~>net~>name))',f'fprintf(f " {ch}\\n")']
  lines+=[f'fprintf(f ".ENDS {cn}\\n")','dbClose(cv)']
 lines+=['close(f)','exit()'];p=ROOT/'scripts/export_native_generated.il';p.write_text('\n'.join(lines)+'\n')
 with (ROOT/'results/export_native.log').open('w') as f:r=subprocess.run(['/apps/cds/IC618/tools/dfII/bin/dbAccess','-load',str(p)],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT)
 text=(ROOT/'results/export_native.log').read_text()
 if r.returncode or '*Error*' in text:raise RuntimeError('Native schematic export failed: results/export_native.log')
 print('Native CDL exported',flush=True)

def stream(cn):
 out=ROOT/'results/physical'/cn;out.mkdir(parents=True,exist_ok=True);gds=out/'layout.gds'
 with (out/'streamout.stdout').open('w') as f:r=subprocess.run([ST,'-library','sram_project','-topCell',cn,'-view','layout','-strmFile',str(gds),'-logFile',str(out/'streamout.log')],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError(cn+' streamout failed')
 return out,gds

def verify(cn,lvs=True):
 out,gds=stream(cn)
 deck=Path('/apps/cds/local/GPDK045/pvs/pvlDRC.rul').read_text().replace('"CELLNAME.gds"','"'+str(gds)+'"').replace('"CELLNAME"','"'+cn+'"').replace('"CELLNAME.db"','"'+str(out/'drc.db')+'"')
 (out/'drc.pvl').write_text(deck)
 with (out/'drc.stdout').open('w') as f:r=subprocess.run([PG,'-drc','-log',str(out/'drc.log'),str(out/'drc.pvl')],cwd=out,env=ENV,stdout=f,stderr=subprocess.STDOUT)
 ds=(out/'result.sum').read_text() if (out/'result.sum').exists() else ''
 (out/'drc_summary.txt').write_text(ds)
 count=re.search(r'Total DRC Results\s*:\s*(\d+)',ds);drc=int(count[1]) if count else -1
 result={'cell':cn,'drc_results':drc,'drc_pass':r.returncode==0 and drc==0}
 print(cn,'DRC',drc,flush=True)
 if not lvs or not result['drc_pass']:
  (out/'checks.json').write_text(json.dumps(result,indent=2));return result
 (out/'pvs_control_file').write_text('lvs_netlist yes -allow_inconsistent_model\n')
 source=ROOT/'netlists/native.cdl'
 pvl=f'''layout_path "{gds}" gdsii;
layout_primary "{cn}";
schematic_path "{source}" spice;
schematic_primary "{cn}";
lvs_report_file "{out/'lvs_report.txt'}";
lvs_write_netlist -layout "{out/'compared_layout.cdl'}";
include "/apps/cds/local/GPDK045/pvs/pvlLVS.rul"
'''
 (out/'lvs.pvl').write_text(pvl)
 old=out/'lvs_report.txt.cls'
 if old.exists():old.unlink()
 with (out/'lvs.stdout').open('w') as f:r=subprocess.run([PG,'-lvs','-spice',str(out/'extracted.spice'),'-log',str(out/'lvs.log'),str(out/'lvs.pvl')],cwd=out,env=ENV,stdout=f,stderr=subprocess.STDOUT)
 text=old.read_text() if old.exists() else ''
 result['lvs_pass']=r.returncode==0 and bool(re.search(r'Run Result\s*:\s*MATCH',text));print(cn,'LVS',result['lvs_pass'],flush=True)
 (out/'checks.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('cells',nargs='*');p.add_argument('--drc-only',action='store_true');p.add_argument('--skip-export',action='store_true');a=p.parse_args()
 if not a.drc_only and not a.skip_export:export_native()
 cells=a.cells or list(C)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda cn:verify(cn,not a.drc_only),cells))
 print(json.dumps(results,indent=2))
 if not all(r['drc_pass'] and (a.drc_only or r.get('lvs_pass')) for r in results):raise SystemExit(1)
