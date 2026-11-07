#!/apps/anaconda/bin/python
from pathlib import Path
import re,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from simulate import ROOT,run_job,write,functional
source=(ROOT/'results/lvs/extracted.spice').read_text()
lines=[]; top_ports=None
for line in source.splitlines():
    line=line.split('$',1)[0].strip()
    if not line or line.startswith('*'):continue
    p=line.split()
    if p[0].lower()=='.subckt':
        name=p[1]
        if name=='sram_cell': top_ports=p[2:];name='sram_cell_physical'
        lines.append(f'subckt {name} ('+' '.join(p[2:])+')')
    elif p[0].lower()=='.ends': lines.append('ends '+('sram_cell_physical' if p[1]=='sram_cell' else p[1]))
    elif p[0][0].upper()=='M':
        # fw is an extraction width annotation; GPDK MOS models take w and nf.
        args=[a.lower() for a in p[6:] if not a.startswith('fw=')]
        lines.append(p[0]+' ('+' '.join(p[1:5])+') '+p[5]+' '+' '.join(args))
    elif p[0][0].upper()=='X':lines.append(p[0]+' ('+' '.join(p[1:-1])+') '+p[-1])
    else:raise ValueError(line)
assert top_ports
converted='\n'.join(lines)+'\nsubckt sram_cell (BL BL_bar WL Q Q_bar Vdd GND)\nXphysical ('+' '.join(top_ports)+') sram_cell_physical\nends sram_cell\n'
(ROOT/'netlists/sram_cell_extracted.scs').write_text('simulator lang=spectre\n'+converted)
for name,deck in [('extracted_write',write()),('extracted_functional',functional())]:
    deck=re.sub(r'subckt sram_cell \(.*?ends sram_cell\n',lambda m:converted,deck,flags=re.S)
    run_job((name,deck))
