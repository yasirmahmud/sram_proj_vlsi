#!/apps/anaconda/bin/python
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from analyze import *
m=json.loads((RES/'metrics.json').read_text());d=read('functional');timing={}
fig,axes=plt.subplots(2,2,figsize=(11,7))
for row,bit,i in [(0,1,0),(1,0,1)]:
    t0=i*20e-9
    for col,op,ts,te,node,rise in [(0,'write',t0+2e-9,t0+5e-9,'Q',bool(bit)),(1,'read',t0+12e-9,t0+15e-9,'BL_bar' if bit else 'BL',False)]:
        a=cross(d,'WL',.55,ts-.1e-9,te,True);b=cross(d,node,.55,ts-.1e-9,te,rise)
        timing[f'{op}_{bit}']={'trigger_s':a,'response_s':b,'delay_ps':(b-a)*1e12 if a is not None and b is not None else None,'response':node}
        ax=axes[row,col];ax.plot(d['time']*1e9,d['WL'],label='WL');ax.plot(d['time']*1e9,d[node],label=node);ax.axhline(.55,color='gray',ls='--')
        if a is not None and b is not None:
            ax.plot([a*1e9,b*1e9],[.55,.55],'o');ax.text(.04,.15,f'Δt = {(b-a)*1e12:.2f} ps',transform=ax.transAxes)
        ax.set(xlim=(ts*1e9-.1,ts*1e9+.8),ylim=(-.05,1.2),title=f'Physical {op} {bit}: WL → {node}',xlabel='Time (ns)',ylabel='Voltage (V)');ax.legend()
fig.suptitle('Single-cell WL timing, 50% → 50%; 20 fF per bitline');fig.tight_layout();fig.savefig(FIG/'physical_timing.png');plt.close(fig)
m['physical_50pct']=timing
(RES/'metrics.json').write_text(json.dumps(m,indent=2))
fig,axs=plt.subplots(2,2,figsize=(11,6),sharex=True)
for ax,v in zip(axs.flat,[.32,.33,.34,.35]):
    name=f'vdd_refine_{v:.3f}';d=read(name);r=next(r for r in m['reliability'] if r['run']==name)
    for sig in ['Q','Q_bar']:ax.plot(d['time']*1e9,d[sig],label=sig,lw=.8)
    ax.axhline(v*.9,color='gray',ls='--',label='90% VDD');ax.set(title=f'VDD {v:.2f} V: {"PASS" if r["pass"] else "FAIL"}',xlabel='Time (ns)',ylabel='Node voltage (V)',ylim=(-.01,v*1.1));ax.legend(fontsize=8)
fig.suptitle('Supply boundary: same 800 ns write/hold experiment');fig.tight_layout();fig.savefig(FIG/'supply_boundary.png');plt.close(fig)
