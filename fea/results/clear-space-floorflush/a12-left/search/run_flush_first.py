import gzip,json
from pathlib import Path
from fea.floor_flush_run import run,face_contacts
from mini_moonboard import compact_floor_flush_frame as m
from scripts.compact_rail_study import bolt_properties
old=json.loads(gzip.decompress(Path('fea/results/clear-space-floortaper/a12-left/report.json.gz').read_bytes()))
bolts={c.name:bolt_properties(c) for c in m.connections() if c.kind=='bolt'}
seed=[r['name'] for r in old['bearings'] if r['active']]+[r['name'] for r in face_contacts()]
secants={n:v['next_secant_n_per_mm'] for n,v in old['floor_friction_law']['feet'].items()}
r=run(Path('fea/generated/floor-flush-first/a12-left/block-00'),mu=.4,max_cycles=60,damping=.5,
      initial_contact_names=seed,initial_tangent_secants=secants,
      bolt_stiffness={**next(iter(bolts.values())),'by_name':bolts},
      hold='A12',pounds=250.,horizontal_force=(-300.,0.),leg_floor_grid=3,patch_size=20.)
print(json.dumps({'accepted':r['numerically_accepted'],'termination':r['termination']}),flush=True)
