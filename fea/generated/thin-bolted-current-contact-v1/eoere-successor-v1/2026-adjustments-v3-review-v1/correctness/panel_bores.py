"""Final bounded actual-panel bore checks for the two exact frozen v3 receipts."""
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq
from scripts.hl35_candidate import overlaps

DOC=Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1')
HERE=Path(__file__).parent
PINS={}

def sha(path):
    value=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    PINS[str(path)]=value
    return value

def read(path):
    sha(path)
    return json.loads(Path(path).read_bytes())

def load(row):
    assert sha(row['path'])==row['sha256']
    shape=cq.Shape.importBrep(row['path'])
    assert shape.isValid() and len(shape.Solids())==1
    return shape

base=read(DOC/'occupied-adjusted-base-v3.json')
extra=read(DOC/'occupied-2026-adjustments-v3.json')
assert PINS[str(DOC/'occupied-adjusted-base-v3.json')]=='5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7'
assert PINS[str(DOC/'occupied-2026-adjustments-v3.json')]=='5dfa03b785715c92717725400e73bf41b00a58160595ddf6b61b61c3b31f6134'
old=read(DOC/'occupied-aligned-wire-v1.json')
raised=read(DOC/'occupied-bottom-rail-v1.json')
original={r['id']:load(r) for r in raised['finished_panel_solids']}
off={**original,**{r['id']:load(r) for r in base['changed_finished_solids'] if r['kind']=='panel'}}
on={**off,**{r['id']:load(r) for r in extra['changed_finished_solids'] if r['kind']=='panel'}}
old_screws={r['axis_id']:r for r in old['screw_axes']}
relocations=[]
for row in base['screw_axes']:
    if row['axis_id'] not in base['moved_panel_screw_axes']:
        continue
    previous=old_screws[row['axis_id']]
    probes=[]
    for record in (previous,row):
        p,d=cq.Vector(*record['origin_xyz_mm']),cq.Vector(*record['direction_xyz'])
        probes.append(cq.Solid.makeCylinder(2.5,18.25625,p,d))
    first,second=probes
    before=original[row['panel']];after=off[row['panel']]
    fractions=[overlaps(first,before)/first.Volume(),overlaps(second,before)/second.Volume(),
               overlaps(first,after)/first.Volume(),overlaps(second,after)/second.Volume()]
    assert max(abs(a-b) for a,b in zip(fractions,[0,1,1,0]))<1e-6,(row['axis_id'],fractions)
    assert overlaps(second,on[row['panel']])/second.Volume()<1e-6
    relocations.append({'id':row['axis_id'],'old_original_new_original_old_OFF_new_OFF_fractions':fractions})
N=cq.Vector(0,-math.cos(math.radians(40)),math.sin(math.radians(40)))
def point(x,s):
    a=math.radians(40)
    return cq.Vector(x,-18*(1+math.cos(a))+s*math.sin(a),277+18*math.sin(a)+s*math.cos(a))
bores=[]
for row in extra['grid']:
    for kind,xy,panel,radius in [('hold',row['tnut_x_s_mm'],row['tnut_panel'],11.1125/2),
                                ('LED',row['LED_x_s_mm'],row['LED_panel'],6.5)]:
        probe=cq.Solid.makeCylinder(radius,18.25625,point(xy[0]-1219.2,xy[1]),-N)
        before=overlaps(probe,off[panel])/probe.Volume()
        after=overlaps(probe,on[panel])/probe.Volume()
        assert before>.999999 and after<1e-6,(row['id'],kind,before,after)
        bores.append({'id':row['id'],'kind':kind,'before_fraction':before,'after_fraction':after})
for path,digest in list(PINS.items()):
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
sha(__file__)
result={'schema':'independent_v3_panel_bore_review/v1','moved_screw_bores':relocations,
        'optional_bore_count':len(bores),'minimum_before_fraction':min(r['before_fraction'] for r in bores),
        'maximum_after_fraction':max(r['after_fraction'] for r in bores),'source_sha256':PINS,
        'limits':['Exact frozen v3 nominal panel solids; cylinder occupancy only, no bit or physical drilling instruction.']}
(HERE/'panel-bores.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'moved_screw_bores':len(relocations),'optional_bores':len(bores),
                  'receipt_sha256':sha(HERE/'panel-bores.json')}),flush=True)
