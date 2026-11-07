from pathlib import Path
import sys,itertools,json,re,subprocess,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent/'sram_cell/scripts'))
from simulate import mos
from project_paths import model_file
cases=list(itertools.product([120,240],[45,90,180],[120,360,720,1440],[45,90],[120,360]))
pairs=[(1.1,0),(0,1.1),(1.1,1.0),(1.0,1.1),(.8,.7),(.7,.8)]
d=f'simulator lang=spectre\ninclude "{model_file()}" section=tt\nVDD (VDD 0) vsource dc=1.1\nsimOptions options reltol=1e-5\n'
for j,(a,b) in enumerate(pairs):d+=f'VA{j} (A{j} 0) vsource dc={a}\nVB{j} (B{j} 0) vsource dc={b}\n'
for i,(wn,ln,wp,lp,tail) in enumerate(cases):
 d+=f'subckt S{i} (A B O VDD)\n'
 for n,ds,g,ss,k,w,l in [('PL','nd','nd','VDD','p',wp,lp),('PR','ns','nd','VDD','p',wp,lp),('NL','nd','B','tail','n',wn,ln),('NR','ns','A','tail','n',wn,ln),('NT','tail','VDD','0','n',tail,45),('BP','O','ns','VDD','p',360,45),('BN','O','ns','0','n',360,45)]:
  line=mos(n,ds,g,ss,'VDD' if k=='p' else '0',k,w)
  if l!=45:line=re.sub(r'(?<![A-Za-z0-9_])45n\b',f'{l}n',line)
  d+=line
 d+='ends\n'
 for j,(a,b) in enumerate(pairs):d+=f'X{i}_{j} (A{j} B{j} Y{i}_{j} VDD) S{i}\n'
d+='dc1 dc\nsave '+' '.join(f'Y{i}_{j}' for i in range(len(cases)) for j in range(len(pairs)))+'\n'
p=ROOT/'netlists/tune_sense.scs';p.write_text(d);out=ROOT/'results/tune_sense';out.mkdir(exist_ok=True)
env=os.environ.copy();env.setdefault('CDS_LIC_FILE','5280@ece-itop-licsvr.ece.ufl.edu')
with (out/'stdout.log').open('w') as f:r=subprocess.run(['/apps/cds/spectre211/bin/spectre','+aps','+mt=4',str(p),'-raw',str(out/'psf'),'-format','psfascii'],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0
s=(out/'psf/dc1.dc').read_text().split('VALUE\n')[1]
vals={k:float(v) for k,v in re.findall(r'^"(Y[^"\n]+)"\s+(?:"V"\s+)?([-+\deE.]+)',s,re.M)}
rank=[]
for i,case in enumerate(cases):
 ys=[vals[f'Y{i}_{j}'] for j in range(6)];quality=min(y/1.1 if a>b else 1-y/1.1 for y,(a,b) in zip(ys,pairs));rank.append({'sizes':case,'quality':quality,'outputs':ys})
rank.sort(key=lambda x:x['quality'],reverse=True)
(out/'ranking.json').write_text(json.dumps(rank,indent=2))
for r in rank[:12]:print(r,flush=True)
