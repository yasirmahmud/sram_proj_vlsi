#!/apps/anaconda/bin/python
"""Generate and run reproducible GPDK045 Spectre cell characterization."""
from pathlib import Path
import os, subprocess, json, concurrent.futures, argparse
ROOT=Path(__file__).resolve().parents[1]
from project_paths import model_file
MODEL=model_file()
SP='/apps/cds/spectre211/bin/spectre'

def mos(name,d,g,s,b,kind,w):
    templates=json.loads((ROOT/'netlists/native_device_templates.json').read_text())
    t=templates[kind]
    args=t['args'].replace(f"({t['width']}n)",f"({w}n)")
    return f'{name} ({d} {g} {s} {b}) g45{kind}1svt {args}\n'

def cell(pd=360,ax=240,pu=120,offset=False):
    return ('subckt sram_cell (BL BL_bar WL Q Q_bar Vdd GND)\n'+
        mos('PM0','Q_bar','Q_gate' if offset else 'Q','Vdd','Vdd','p',pu)+
        mos('PM1','Q','Q_bar','Vdd','Vdd','p',pu)+
        mos('NM0','Q_bar','Q_gate' if offset else 'Q','GND','GND','n',pd)+
        mos('NM1','Q','Q_bar','GND','GND','n',pd)+
        mos('NM2','Q_bar','WL','BL_bar','GND','n',ax)+
        mos('NM3','BL','WL','Q','GND','n',ax)+
        ('Voffset (Q_gate Q) vsource dc=voffset\n' if offset else '')+'ends sram_cell\n')

def header(vdd=1.1,corner='tt',temp=27,off=0):
    return f'simulator lang=spectre\ninclude "{MODEL}" section={corner}\nparameters vdd={vdd:g} voffset={off:g}\nsimOptions options reltol=1e-5 vabstol=1e-7 iabstol=1e-14 temp={temp} gmin=1e-14\nVdd (Vdd 0) vsource dc=vdd\n'

def pulse(name,node,inv=False,wl=False):
    a,b=('vdd','0') if inv else ('0','vdd')
    return f'{name} ({node} 0) vsource type=pulse val0={a} val1={b} delay=0 rise=100p fall=100p width={"249.9n" if wl else "49.9n"} period={"500n" if wl else "100n"}\n'

def write(vdd=1.1,pd=360,ax=240,pu=120,off=0,corner='tt',temp=27):
    return (header(vdd,corner,temp,off)+cell(pd,ax,pu,off!=0)+
        'Xcell (BL BL_bar WL Q Q_bar Vdd 0) sram_cell\n'+pulse('Vwl','WL',wl=True)+pulse('Vbl','BL')+pulse('Vblb','BL_bar',True)+
        'ic Q=0 Q_bar=vdd\ntran tran stop=800n maxstep=1n errpreset=conservative\nsave WL BL BL_bar Q Q_bar\n')

def forced_read(pd=360,ax=240,pu=120):
    return (header()+cell(pd,ax,pu)+'Xcell (BL BL_bar WL Q Q_bar Vdd 0) sram_cell\n'+pulse('Vwl','WL',wl=True)+pulse('Vq','Q')+pulse('Vqb','Q_bar',True)+
        'Cbl (BL 0) capacitor c=20f\nCblb (BL_bar 0) capacitor c=20f\nRbl (BL 0) resistor r=1e12\nRblb (BL_bar 0) resistor r=1e12\nic BL=0 BL_bar=1.1\ntran tran stop=800n maxstep=1n errpreset=conservative\nsave WL BL BL_bar Q Q_bar\n')

def pwl(name,node,points):
    return f'{name} ({node} 0) vsource type=pwl wave=['+' '.join(f'{t:g}n ({v:g}*vdd)' for t,v in points)+']\n'

def functional(pd=360,ax=240,pu=120,corner='tt',temp=27,vdd=1.1):
    bits=[1,0,1,1,0,0,1,0]
    d=header(vdd,corner,temp)+cell(pd,ax,pu)+'Xcell (BL BL_bar WL Q Q_bar Vdd 0) sram_cell\n'
    schedules={s:[(0,0)] for s in ['WL','WEN','DIN']}
    schedules['PREb']=[(0,0)]
    for i,bit in enumerate(bits):
        t=20*i
        for signal,edges in {'WL':[(2,1),(5,0),(12,1),(15,0)],'WEN':[(1,1),(5,0)],'PREb':[(0.5,1),(9,0),(11,1)],'DIN':[(0.2,bit)]}.items():
            for dt,val in edges:
                seq=schedules[signal]; old=seq[-1][1]; time=t+dt
                if val!=old: seq.extend([(time,old),(time+.1,val)])
    for sig,seq in schedules.items():
        seq.append((160,seq[-1][1])); d+=pwl('V'+sig,sig,seq)
    d+='Ewenb (WENb 0 Vdd WEN) vcvs gain=1\nEdinb (DINb 0 Vdd DIN) vcvs gain=1\n'
    for sig,inp in [('BL','DIN'),('BL_bar','DINb')]:
        d+=mos('Wn'+sig,sig,'WEN',inp,'0','n',1000)+mos('Wp'+sig,sig,'WENb',inp,'Vdd','p',1000)
        d+=mos('Pre'+sig,sig,'PREb','Vdd','Vdd','p',1000)
        d+=f'C{sig} ({sig} 0) capacitor c=20f\n'
    d+=mos('Equalize','BL','PREb','BL_bar','Vdd','p',1000)
    d+='ic Q=0 Q_bar=vdd\ntran tran stop=160n maxstep=100p errpreset=conservative\nsave WL WEN PREb DIN BL BL_bar Q Q_bar\n'
    return d

def snm(pd=120,ax=120,pu=120,write=False):
    d=header()+ 'Vin (VIN 0) vsource dc=0\n'
    for out,bl in [('VOUT1','Vdd'),('VOUT2','0')] if write else [('VOUT','Vdd')]:
        d+=mos('P'+out,out,'VIN','Vdd','Vdd','p',pu)+mos('N'+out,out,'VIN','0','0','n',pd)+mos('A'+out,out,'Vdd',bl,'0','n',ax)
    return d+'dc1 dc dev=Vin param=dc start=0 stop=1.1 step=0.0005\nsave VIN '+('VOUT1 VOUT2' if write else 'VOUT')+'\n'

def run_job(item):
    name,deck=item
    net=ROOT/'netlists'/f'{name}.scs'; net.write_text(deck)
    out=ROOT/'results'/name; out.mkdir(exist_ok=True)
    env=os.environ.copy(); env.setdefault('CDS_LIC_FILE','5280@ece-itop-licsvr.ece.ufl.edu')
    with (out/'stdout.log').open('w') as f:
        r=subprocess.run([SP,str(net),'-raw',str(out/'psf'),'-format','psfascii','+log',str(out/'spectre.log')],stdout=f,stderr=subprocess.STDOUT,env=env,cwd=out)
    if r.returncode: raise RuntimeError(f'{name} failed; see {out}/stdout.log')
    print(f'PASS simulator: {name}',flush=True)
    return name

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--quick',action='store_true'); args=parser.parse_args()
    (ROOT/'netlists/sram_cell.scs').write_text('simulator lang=spectre\n'+cell())
    jobs={'write_nominal':write(),'write_default':write(pd=120,ax=120),'read_forced':forced_read(),'functional':functional()}
    for name,pd,ax,pu in [('default',120,120,120),('access2',120,240,120),('pulldown2',240,120,120),('pullup2',120,120,240),('final',360,240,120)]:
        jobs['read_snm_'+name]=snm(pd,ax,pu)
        jobs['write_snm_'+name]=snm(pd,ax,pu,True)
    if not args.quick:
        for v in [0,.275,.55,.825,1.1]: jobs[f'vdd_coarse_{v:.3f}']=write(vdd=v)
        for v in [.10,.15,.20,.25,.30,.31,.32,.33,.34,.35,.40,.45,.50,.60,.70,.80,.90,1.0]: jobs[f'vdd_refine_{v:.3f}']=write(vdd=v)
        for off in [.1,.2,.3,.4]:
            for v in [.2,.3,.4,.5,.6,.7,.8,.9,1.0,1.1]: jobs[f'mismatch_{off:.1f}_{v:.1f}']=write(vdd=v,off=off)
        for corner in ['tt','ff','ss','fs','sf']:
            for temp in [-40,27,125]: jobs[f'functional_{corner}_{temp}']=functional(corner=corner,temp=temp)
    (ROOT/'results/run_manifest.json').write_text(json.dumps({'jobs':list(jobs),'model':str(MODEL),'spectre':SP},indent=2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(run_job,jobs.items()))
if __name__=='__main__': main()
