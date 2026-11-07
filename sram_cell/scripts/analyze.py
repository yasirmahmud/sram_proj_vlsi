#!/apps/anaconda/bin/python
"""Check measured states, extract 50%-50% delays and largest-square margins."""
from pathlib import Path
import re, json, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parents[1]; RES=ROOT/'results'; FIG=RES/'figures'; FIG.mkdir(exist_ok=True)
plt.rcParams.update({'figure.dpi':150,'axes.grid':True,'grid.alpha':.2,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})

def read(name,dc=False):
    p=RES/name/'psf'/('dc1.dc' if dc else 'tran.tran.tran')
    content=p.read_text().split('VALUE\n',1)[1].split('\nEND',1)[0]
    out={}
    for sig,value in re.findall(r'^"([^"\n]+)"\s+([-+\deE.]+)\s*$',content,re.M): out.setdefault(sig,[]).append(float(value))
    return {k:np.array(v) for k,v in out.items()}

def at(d,node,t): return float(np.interp(t,d['time'],d[node]))
def cross(d,node,level,start,end,rise):
    t=d['time'];v=d[node]; idx=np.where((t[:-1]>=start)&(t[1:]<=end)&((v[:-1]<level)&(v[1:]>=level) if rise else (v[:-1]>level)&(v[1:]<=level)))[0]
    if not len(idx): return None
    i=idx[0];return float(t[i]+(level-v[i])*(t[i+1]-t[i])/(v[i+1]-v[i]))

def delays(name,src,dst):
    d=read(name); out={}
    for bit,t0,rise in [(1,100e-9,True),(0,150e-9,False)]:
        a=cross(d,src,.55,t0-1e-9,t0+3e-9,rise);b=cross(d,dst,.55,t0-1e-9,t0+3e-9,rise)
        out[str(bit)]={'trigger_s':a,'response_s':b,'delay_ps':(b-a)*1e12 if a is not None and b is not None else None}
    return out

def check_functional(name):
    d=read(name);rows=[];bits=[1,0,1,1,0,0,1,0]
    for i,bit in enumerate(bits):
        t=i*20e-9; vals={}
        for label,dt in [('write',4.8),('hold',8),('read',14.8),('after_read',19)]:
            q=at(d,'Q',t+dt*1e-9); qb=at(d,'Q_bar',t+dt*1e-9)
            vals[label]={'Q':q,'Q_bar':qb,'pass':bool(q>.9*1.1 and qb<.1*1.1) if bit else bool(q<.1*1.1 and qb>.9*1.1)}
        low='Q_bar' if bit else 'Q';mask=(d['time']>=t+12.2e-9)&(d['time']<t+15e-9)
        disturb=float(np.max(d[low][mask])); diff=at(d,'BL',t+14.8e-9)-at(d,'BL_bar',t+14.8e-9)
        precharge=min(at(d,'BL',t+11.5e-9),at(d,'BL_bar',t+11.5e-9))
        okay=precharge>1.089 and disturb<.55 and all(v['pass'] and -.055<=v['Q']<=1.155 and -.055<=v['Q_bar']<=1.155 for v in vals.values()) and (diff>.1 if bit else diff<-.1)
        rows.append({'cycle':i,'bit':bit,'pass':bool(okay),'read_low_node_max_V':disturb,'precharged_bitline_min_V':precharge,'BL_minus_BLbar_V':diff,'states':vals})
    return {'pass':all(r['pass'] for r in rows),'cycles':rows}

def square(x,upper,lower):
    # For decreasing boundaries, an inscribed axis-aligned square touches
    # lower(a) at bottom-left and upper(a+s) at top-right.
    xx=np.linspace(x[0],x[-1],6001);lo_y=np.interp(xx,x,lower)
    lo=np.zeros_like(xx);hi=x[-1]-xx
    for _ in range(35):
        ss=(lo+hi)/2; fits=np.interp(xx+ss,x,upper)-lo_y>=ss
        lo=np.where(fits,ss,lo);hi=np.where(fits,hi,ss)
    j=int(np.argmax(lo));return float(lo[j]),float(xx[j]),float(lo_y[j])

def margins():
    rows=[]
    for kind in ['read','write']:
        fig,axs=plt.subplots(1,4,figsize=(15,3.6))
        for k,name in enumerate(['default','access2','pulldown2' if kind=='read' else 'pullup2','final']):
            d=read(f'{kind}_snm_{name}',True);x=d['dc']; ax=axs[k]
            if kind=='read':
                a=d['VOUT']; b=np.interp(x,a[::-1],x[::-1]); s1=square(x,a,b);s2=square(x,b,a);sq=s1 if s1[0]<s2[0] else s2
                ax.plot(x,a,label='VOUT(VIN)');ax.plot(a,x,label='Mirrored VTC');value=min(s1[0],s2[0])
            else:
                a=d['VOUT1'];b=d['VOUT2'];sq=square(x,a,b);value=sq[0]
                ax.plot(x,a,label='BL = VDD');ax.plot(x,b,label='BL = 0')
            size,px,py=sq; ax.add_patch(Rectangle((px,py),size,size,fill=False,color='#d53e4f',lw=1.5))
            ax.set(xlim=(0,1.1),ylim=(0,1.1),xlabel='VIN (V)',ylabel='Voltage (V)',title=f'{name}: {value*1000:.1f} mV');ax.set_aspect('equal'); ax.legend(fontsize=7)
            rows.append({'kind':kind,'sizing':name,'margin_mV':value*1000,'square_x_V':px,'square_y_V':py,'square_side_V':size})
        fig.suptitle(('Read butterfly SNM' if kind=='read' else 'Write margin: assignment two-VTC square method')+' — 1.1 V, TT, 27°C');fig.tight_layout();fig.savefig(FIG/f'{kind}_snm.png');plt.close(fig)
    return rows

def plot_traces(name,title):
    d=read(name);sig=['WL','BL','BL_bar','Q','Q_bar'];fig,axs=plt.subplots(len(sig),1,sharex=True,figsize=(10,7))
    for ax,s in zip(axs,sig): ax.plot(d['time']*1e9,d[s],lw=.9);ax.set_ylabel(s+' (V)');ax.set_ylim(-.1,1.2)
    axs[-1].set_xlabel('Time (ns)');fig.suptitle(title);fig.tight_layout();fig.savefig(FIG/f'{name}.png');plt.close(fig)

def plot_markers(name,src,dst,metrics):
    d=read(name);fig,axs=plt.subplots(1,2,figsize=(11,3.5))
    for ax,bit,t0 in zip(axs,['1','0'],[100,150]):
        ax.plot(d['time']*1e9,d[src],label=src);ax.plot(d['time']*1e9,d[dst],label=dst)
        m=metrics[bit];a=m['trigger_s'];b=m['response_s']
        if a is not None and b is not None:
            ax.plot([a*1e9,b*1e9],[.55,.55],'o',ms=5)
            ax.annotate('',(b*1e9,.55),(a*1e9,.55),arrowprops={'arrowstyle':'<->','color':'black'})
            ax.text(.03,.12,f"Δt = {m['delay_ps']:.2f} ps",transform=ax.transAxes)
        ax.axhline(.55,color='gray',ls='--');ax.set(xlim=(t0-.05,t0+.5),ylim=(-.05,1.2),xlabel='Time (ns)',ylabel='Voltage (V)',title=f'{name}: {bit}, 50% → 50%');ax.legend()
    fig.tight_layout();fig.savefig(FIG/f'{name}_markers.png');plt.close(fig)

def reliability():
    rows=[]
    for p in sorted(RES.glob('vdd_*/psf/tran.tran.tran'))+sorted(RES.glob('mismatch_*/psf/tran.tran.tran')):
        name=p.parents[1].name;parts=name.split('_');v=float(parts[-1]);off=float(parts[-2]) if name.startswith('mismatch') else 0
        d=read(name);scores=[]
        for t,bit in [(25,1),(75,0),(125,1),(175,0),(225,1),(325,1),(425,1),(525,1),(575,0),(625,1),(675,0),(725,1)]:
            q=at(d,'Q',t*1e-9);qb=at(d,'Q_bar',t*1e-9);high,low=(q,qb) if bit else (qb,q)
            scores.append((high/v,(v-low)/v) if v>0 else (0,0))
        margin=float(np.min(scores));rows.append({'run':name,'vdd_V':v,'offset_V':off,'minimum_rail_fraction':margin,'pass':margin>=.9 and v>0})
    if rows:
        with (RES/'reliability.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
        fig,ax=plt.subplots(figsize=(8,4))
        for off in [0,.1,.2,.3,.4]:
            rr=sorted([r for r in rows if r['offset_V']==off],key=lambda r:r['vdd_V']);ax.plot([r['vdd_V'] for r in rr],[r['minimum_rail_fraction'] for r in rr],'o-',label=f'Gate offset {off:.1f} V')
        ax.axhline(.9,color='black',ls='--',label='90% rail criterion');ax.set(xlabel='VDD (V)',ylabel='Worst normalized rail quality',ylim=(-.1,1.1),title='Write + retention reliability; 800 ns sweeps');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(FIG/'reliability.png');plt.close(fig)
    return rows

def main():
    out={'write_50pct':delays('write_nominal','BL','Q'),'write_default_50pct':delays('write_default','BL','Q'),'extracted_write_50pct':delays('extracted_write','BL','Q'),'read_forced_50pct':delays('read_forced','Q','BL')}
    out['functional']={p.name:check_functional(p.name) for p in list(RES.glob('functional*'))+list(RES.glob('extracted_functional')) if (p/'psf/tran.tran.tran').exists()}
    out['margins']=margins();out['reliability']=reliability()
    for n,title in [('write_nominal','Final cell write stimulus: WL 2 MHz, BL 10 MHz, 100 ps edges'),('write_default','Assignment baseline: all six widths 120 nm'),('read_forced','Assignment read experiment: Q/Q_bar driven, 20 fF bitlines'),('extracted_functional','Extracted devices: write / hold / precharge / read; 20 fF bitlines'),('functional','Physical write / hold / precharge / read; 20 fF bitlines')]: plot_traces(n,title)
    plot_markers('write_nominal','BL','Q',out['write_50pct']);plot_markers('read_forced','Q','BL',out['read_forced_50pct'])
    (RES/'metrics.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k not in ['functional','reliability']},indent=2))
    fails=[n for n,v in out['functional'].items() if not v['pass']];print('Functional runs:',len(out['functional']),'failures:',fails)
    if fails: raise SystemExit(1)
if __name__=='__main__': main()
