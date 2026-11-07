#!/apps/anaconda/bin/python
"""Preserve compressed raw waveforms and hash the final deliverables."""
from pathlib import Path
import json,gzip,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent
summary=json.loads((ROOT/'results/validation_summary.json').read_text())
names=summary['functional_cases']+['array_timing','array_extracted_tt_27']
names+=['unit_'+r['cell'] for r in json.loads((ROOT/'results/unit_summary.json').read_text())]
for name in names:
 src=ROOT/'results'/name/'psf/tran.tran.tran';dst=Path(str(src)+'.gz')
 if src.exists() and (not dst.exists() or dst.stat().st_mtime<src.stat().st_mtime):
  with src.open('rb') as inf,dst.open('wb') as outf:
   with gzip.GzipFile(filename=src.name,mode='wb',fileobj=outf,mtime=0,compresslevel=6) as z:shutil.copyfileobj(inf,z)
  print('Archived',name,flush=True)
files=[REPO/'Final_Project_Report.pdf',REPO/'Final_Project_Report.docx',REPO/'Full_Array_Layout.png']
files+=list((ROOT/'cadence').rglob('*.oa'))+list((ROOT/'netlists').glob('*.cdl'))
files+=[ROOT/'results/validation_summary.json',ROOT/'results/full_metrics.json',ROOT/'results/address_validation.csv']
for name in names:
 out=ROOT/'results'/name
 files += [p for p in [out/'spectre.log',out/'checks.json',out/'unit_checks.json',out/'psf/tran.tran.tran.gz'] if p.exists()]
for cn in summary['physical']:
 out=ROOT/'results/physical'/cn['cell']
 files += [out/n for n in ['layout.gds','checks.json','drc_summary.txt','lvs_report.txt.cls','extracted.spice']]
manifest={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
(ROOT/'results/evidence_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Hashed',len(manifest),'final artifacts',flush=True)
