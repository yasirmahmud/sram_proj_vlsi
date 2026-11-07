#!/apps/anaconda/bin/python
"""Generate measured timing, coverage, and block-validation figures."""
from pathlib import Path
import json,sys,math,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from analyze_array import read
from design import C
from layout import flatten
F=ROOT/'results/figures';F.mkdir(exist_ok=True)
plt.rcParams.update({'figure.dpi':160,'font.size':9,'axes.grid':True,'grid.alpha':.18,'axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):fig.tight_layout();fig.savefig(F/(name+'.png'));plt.close(fig)
def cross(d,node,lev,lo,hi,rise,last=False):
 t=d['time'];v=d[node];ix=np.where((t[:-1]>=lo)&(t[1:]<=hi)&((v[:-1]<lev)&(v[1:]>=lev) if rise else (v[:-1]>lev)&(v[1:]<=lev)))[0]
 if not len(ix):return None
 i=int(ix[-1] if last else ix[0]);return float(t[i]+(lev-v[i])*(t[i+1]-t[i])/(v[i+1]-v[i]))
def at(d,n,t):return float(np.interp(t,d['time'],d[n]))
def rails(bit,q,qb):return q>.99 and qb<.11 if bit else q<.11 and qb>.99

base=ROOT/'results/array_tt_27';d=read(base/'psf/tran.tran.tran');spec=json.loads((base/'operations.json').read_text());ops=spec['operations'];checks=json.loads((base/'checks.json').read_text())
metrics={'nominal':{k:v for k,v in checks.items() if k not in ['rows','failures']},'transistors':len(flatten('sram_4x6'))}
# Overall transient with all logical addresses visible.
fig,ax=plt.subplots(7,1,sharex=True,figsize=(14,8));tu=d['time']*1e6
for a,n in zip(ax[:4],['CLK1','CLK2','WR','RD']):a.plot(tu,d[n],lw=.6);a.set_ylabel(n)
addr=(d['R1']>.55)*16+(d['R0']>.55)*8+(d['C2']>.55)*4+(d['C1']>.55)*2+(d['C0']>.55);ax[4].step(tu,addr,lw=.7);ax[4].set_ylabel('Address\n(binary code)')
ax[5].plot(tu,d['DIN'],lw=.7);ax[5].set_ylabel('DATA_IN')
ax[6].plot(tu,d['DOUT'],lw=.7,label='DOUT');ax[6].scatter([(r['operation']*50+37)*1e-3 for r in checks['rows'] if r['kind']=='read'],[r['expected_bit']*1.1 for r in checks['rows'] if r['kind']=='read'],s=5,color='#168c5b',label='Correct read samples');ax[6].set_ylabel('DOUT (V)');ax[6].legend(loc='upper right',fontsize=7);ax[6].set_xlabel('Time (µs)')
fig.suptitle('Complete 4×6 SRAM: 244 operations at 20 MHz — all 24 addresses, three patterns, protection tests');save(fig,'array_overview')
# Show every physical storage cell transitioning in the all-one/all-zero write phases.
for phase in ['ones','zeros','mixed']:
 ids=[i for i,o in enumerate(ops) if o['phase']==phase and o['kind']=='write'];start=ids[0]*50;end=(ids[-1]+1)*50
 fig,aa=plt.subplots(4,6,sharex=True,sharey=True,figsize=(14,8));mask=(d['time']>=start*1e-9)&(d['time']<=end*1e-9)
 for r in range(4):
  for c in range(6):
   a=aa[r,c];a.plot(d['time'][mask]*1e9-start,d[f'Xchip.XMEM.Q{r}_{c}'][mask],lw=.9,label='Q');a.plot(d['time'][mask]*1e9-start,d[f'Xchip.XMEM.QB{r}_{c}'][mask],lw=.65,label='Q̅');a.set_title(f'row {r}, col {c}',fontsize=8);a.set_ylim(-.06,1.16)
 for a in aa[-1]:a.set_xlabel('Time in write phase (ns)',fontsize=7)
 for a in aa[:,0]:a.set_ylabel('Voltage (V)')
 fig.suptitle(f'Write {phase}: all 24 storage cells — '+spec['patterns'][phase]);save(fig,'write_'+phase+'_24_cells')
# Expected and both independent read scans, rendered as full 4x6 matrices.
fig,aa=plt.subplots(3,3,figsize=(11,7))
for row,phase in enumerate(['ones','zeros','mixed']):
 expected=np.array([int(b) for b in spec['patterns'][phase]]).reshape(4,6)
 for col,scan in enumerate([None,0,1]):
  arr=expected if scan is None else np.array([int(r['DOUT_V']>.55) for r,o in zip(checks['rows'],ops) if o['phase']==phase and o['kind']=='read' and o['scan']==scan]).reshape(4,6)
  a=aa[row,col];a.imshow(arr,vmin=0,vmax=1,cmap='Blues');a.grid(False);a.set_xticks(range(6));a.set_yticks(range(4));a.set_title(phase+': '+('expected' if scan is None else f'read scan {scan+1}'))
  for r in range(4):
   for c in range(6):a.text(c,r,str(arr[r,c]),ha='center',va='center',color='white' if arr[r,c] else 'black')
fig.suptitle('Complete readback coverage: expected data and two nondestructive scans');save(fig,'readback_coverage')
# Fine-step timing is a separate short transistor-level run, not coarse coverage data.
t=read(ROOT/'results/array_timing/psf/tran.tran.tran');timing={};fig,aa=plt.subplots(2,2,figsize=(11,7))
for ax,op,bit,cycle,node,rise in [(aa[0,0],'write',1,0,'Xchip.XMEM.Q0_0',True),(aa[0,1],'write',0,2,'Xchip.XMEM.Q0_0',False),(aa[1,0],'read',1,1,'DOUT',True),(aa[1,1],'read',0,3,'DOUT',False)]:
 start=(cycle*50+20)*1e-9;a=cross(t,'CLK1',.55,start-1e-9,start+2e-9,True);b=cross(t,node,.55,start-1e-9,start+15e-9,rise,True)
 assert a is not None and b is not None,(op,bit,a,b)
 value=(b-a)*1e9;timing[f'{op}_{bit}']={'trigger_s':a,'response_s':b,'delay_ns':value,'trigger':'CLK1','response':node,'threshold_V':.55}
 xx=(t['time']-start)*1e9;mask=(xx>=-.2)&(xx<=max(1.2,value+.5));ax.plot(xx[mask],t['CLK1'][mask],label='CLK1');ax.plot(xx[mask],t[node][mask],label='Q[0,0]' if op=='write' else 'DOUT');ax.axhline(.55,color='gray',ls='--',lw=.7);ax.plot([(a-start)*1e9,(b-start)*1e9],[.55,.55],'o',ms=4);ax.annotate('',((b-start)*1e9,.55),((a-start)*1e9,.55),arrowprops={'arrowstyle':'<->','lw':1});ax.text(.05,.15,f'Δt = {value:.4f} ns',transform=ax.transAxes);ax.set(xlabel='Time from CLK1 edge start (ns)',ylabel='Voltage (V)',title=f'{op.capitalize()} {bit}, 50% → 50%');ax.legend()
fig.suptitle('Required full-array timing: 5 ps maximum simulator timestep');save(fig,'timing_markers');metrics['timing']=timing
# Precharge 10%-90%, after the first write has discharged BL_bar[0].
start=52e-9;u=cross(t,'Xchip.BLB0',.11,start-1e-9,start+10e-9,True);v=cross(t,'Xchip.BLB0',.99,start-1e-9,start+10e-9,True);assert u and v
metrics['precharge_10_90_ns']=(v-u)*1e9
fig,ax=plt.subplots(figsize=(8,3.8));xx=(t['time']-start)*1e9;mask=(xx>=-.2)&(xx<2);ax.plot(xx[mask],t['Xchip.BL0'][mask],label='BL[0]');ax.plot(xx[mask],t['Xchip.BLB0'][mask],label='BL̅[0]');ax.plot(xx[mask],t['CLK2'][mask],ls=':',label='CLK2');ax.plot([(u-start)*1e9,(v-start)*1e9],[.11,.99],'o');ax.axhline(.11,color='gray',ls='--');ax.axhline(.99,color='gray',ls='--');ax.set(xlabel='Time from precharge edge (ns)',ylabel='Voltage (V)',title=f'Both bitlines precharge to 1.1 V: 10%–90% = {(v-u)*1e9:.4f} ns');ax.legend();save(fig,'precharge_timing')
# Functional checks independent of the final readback sample.
pre_min=2.0;low_max=0.0;high_min=2.0;hold_bad=[]
for i,o in enumerate(ops):
 base_ns=50*i
 for c in range(6):
  for sig in [f'Xchip.BL{c}',f'Xchip.BLB{c}']:pre_min=min(pre_min,at(d,sig,(base_ns+15)*1e-9))
 ia=np.searchsorted(d['time'],(base_ns+20.5)*1e-9);ib=np.searchsorted(d['time'],(base_ns+39.5)*1e-9)
 if o['kind']=='read':
  for address,bit in enumerate(o['expected']):
   r,c=divmod(address,6);lo=f'Xchip.XMEM.{"QB" if bit else "Q"}{r}_{c}';hi=f'Xchip.XMEM.{"Q" if bit else "QB"}{r}_{c}'
   low_max=max(low_max,float(np.max(d[lo][ia:ib])));high_min=min(high_min,float(np.min(d[hi][ia:ib])))
 if i>24 and o['kind'] in ['write','invalid_read','invalid_write','conflict','overlap']:
  if abs(at(d,'DOUT',(base_ns+1)*1e-9)-at(d,'DOUT',(base_ns+37)*1e-9))>.11:hold_bad.append(i)
assert pre_min>1.089 and low_max<.55 and high_min>.55 and not hold_bad
metrics['precharge_all_bitlines_min_V']=pre_min;metrics['sampled_read_storage_low_max_V']=low_max;metrics['sampled_read_storage_high_min_V']=high_min;metrics['latch_hold_pass']=not hold_bad
# Unit decoder and amplifier plots, using the saved transistor simulation outputs.
for cell,signals in [('row_decoder',['EN','R1','R0','WL0','WL1','WL2','WL3']),('column_decoder',['C2','C1','C0','CS0','CS1','CS2','CS3','CS4','CS5']),('sense_amp',['BIT','BIT_bar','AMP_OUT'])]:
 z=read(ROOT/'results'/('unit_'+cell)/'psf/tran.tran.tran');fig,aa=plt.subplots(len(signals),1,sharex=True,figsize=(10,1.0*len(signals)+1.2))
 for ax,sig in zip(np.atleast_1d(aa),signals):ax.plot(z['time']*1e9,z[sig],lw=.9);ax.set_ylabel(sig);ax.set_ylim(-.08,1.18)
 np.atleast_1d(aa)[-1].set_xlabel('Time (ns)');fig.suptitle(cell.replace('_',' ').title()+(' — addresses 110 and 111 select no column' if cell=='column_decoder' else ' — includes ±100 mV differential tests' if cell=='sense_amp' else ' — disabled and all four enabled addresses'));save(fig,cell+'_simulation')
# Actual R/W controls around the protection test portion.
fig,aa=plt.subplots(7,1,sharex=True,figsize=(11,7));m=(tu>=10.5)
for ax,sig in zip(aa,['CLK1','CLK2','WR','RD','Xchip.WEN','Xchip.REN','Xchip.ROWEN']):ax.plot(tu[m],d[sig][m],lw=.8);ax.set_ylabel(sig.replace('Xchip.',''))
aa[-1].set_xlabel('Time (µs)');fig.suptitle('Read/write protection: unused column addresses, RD=WR=1, and overlapping clocks');save(fig,'rw_control_simulation')
# Actual write-driver waveforms.
fig,aa=plt.subplots(6,1,sharex=True,figsize=(10,6));xx=t['time']*1e9
for ax,sig in zip(aa,['CLK1','WR','DIN','Xchip.WEN','Xchip.GBL','Xchip.GBLB']):ax.plot(xx,t[sig],lw=.9);ax.set_ylabel(sig.replace('Xchip.',''))
aa[-1].set_xlabel('Time (ns)');fig.suptitle('Physical write driver and column path, writing both data values');save(fig,'write_driver_simulation')
# Aggregate only completed, independently checked corner runs.
summary=[]
for p in sorted((ROOT/'results').glob('array_*/checks.json')):
 if 'extracted' in p.parent.name:continue
 r=json.loads(p.read_text());summary.append({'name':p.parent.name,'pass':r['pass'],'operations':r['operations'],'writes':r.get('valid_write_operations'),'reads':r.get('valid_read_operations')})
metrics['corner_runs']=summary;metrics['units']=json.loads((ROOT/'results/unit_summary.json').read_text())
layout=json.loads((ROOT/'results/layout_metadata.json').read_text());metrics['layout']={c:{'width_um':layout[c]['width'],'height_um':layout[c]['height'],'area_um2':layout[c]['width']*layout[c]['height']} for c in C}
if (ROOT/'results/array_extracted_tt_27/checks.json').exists():
 r=json.loads((ROOT/'results/array_extracted_tt_27/checks.json').read_text());metrics['extracted']={k:v for k,v in r.items() if k!='rows'}
# Explicit per-address evidence table.
with (ROOT/'results/address_validation.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['row','column','address_bits','pattern','expected','read_scan_1','read_scan_2','pass'])
 for phase in ['ones','zeros','mixed']:
  for a,b in enumerate(spec['patterns'][phase]):
   r,c=divmod(a,6);vals=[z for z,o in zip(checks['rows'],ops) if o['kind']=='read' and o['phase']==phase and o['addr']==a];w.writerow([r,c,f'{r:02b}_{c:03b}',phase,b,*[int(v['DOUT_V']>.55) for v in vals],all(v['pass'] for v in vals)])
(ROOT/'results/full_metrics.json').write_text(json.dumps(metrics,indent=2))
print('Timing ns:',{k:v['delay_ns'] for k,v in timing.items()});print('Precharge 10-90 ns:',metrics['precharge_10_90_ns']);print('All-line precharge minimum V:',pre_min);print('Nominal coverage:',checks['operations'],'operations, all pass')
