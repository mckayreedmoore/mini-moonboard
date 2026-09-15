import gzip,json,shutil,hashlib
from pathlib import Path
from guarded_coulomb_aitken_seed import build as accelerated_seed
from fea.floor_taper_run import run
from mini_moonboard import compact_floor_taper_frame as model
from scripts.clear_space_batch import archive, CASES
from scripts.clear_space_study import geometry
from scripts.compact_rail_study import bolt_properties
ROOT=Path('fea/generated/floor-taper-remaining')
OUT=Path('fea/results/clear-space-floortaper')

def seed(report,native=None):
 result={'initial_contact_names':[r['name'] for r in report['bearings'] if r['active']], 'initial_tangent_secants':{n:v['next_secant_n_per_mm'] for n,v in report['floor_friction_law']['feet'].items()}}
 if native and not report['closed_bearing_assumption_passed']:
  data=json.loads((native/report['contact_cycles'][-1]['directory']/'input.json').read_text())
  result['initial_tangent_secants']={n:next(s['stiffness_n_per_mm'] for s in data['springs'] if s['name']==n) for n in result['initial_tangent_secants']}
 return result

def main():
 ROOT.mkdir(parents=True,exist_ok=False)
 g=geometry(model); assert g['receiver_fit_pass']; gp=ROOT/'geometry.json';gp.write_text(json.dumps(g,indent=2,allow_nan=False)+'\n')
 initial=Path('fea/results/clear-space-floortaper/a12-rear/report.json.gz')
 report=json.loads(gzip.decompress(initial.read_bytes()));assert report['numerically_accepted']
 bolts={c.name:bolt_properties(c) for c in model.connections() if c.kind=='bolt'}
 history=[]
 for case in ('a12-left','a12-forward','k12-right','k12-rear','a1-rear'):
  if (OUT/case).exists():raise FileExistsError(case)
  state=seed(report); damping=1. if case=='a12-rear' else .5
  for block in range(6):
   d=ROOT/case/f'block-{block:02d}';hold,force=CASES[case]
   report=run(d,module=model,mu=.4,max_cycles=30,damping=damping,**state,
    bolt_stiffness={**next(iter(bolts.values())),'by_name':bolts},member_contacts=[],
    hold=hold,pounds=250.,horizontal_force=force,leg_floor_grid=3,patch_size=20.)
   history.append({'case':case,'block':block,'native':str(d),'accepted':report['numerically_accepted'],'termination':report['termination']})
   (ROOT/'history.json').write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(history[-1]),flush=True)
   if report['numerically_accepted']:
    result=archive(d,gp,OUT/case,model)
    search=OUT/case/'search';search.mkdir();shutil.copy2(__file__,search/'controller.py');shutil.copy2('/tmp/guarded_coulomb_aitken_seed.py',search/'guarded_coulomb_aitken_seed.py');shutil.copy2(ROOT/'history.json',search/'history.json')
    if not result.get('criteria') or not all(result['criteria'].values()):raise SystemExit('Design gate failed: '+case)
    break
   try:
    candidate=accelerated_seed(d)
    if not candidate['extrapolated_count']:raise ValueError('No guarded acceleration')
    state={k:candidate[k] for k in ('initial_contact_names','initial_tangent_secants')};damping=1.
   except ValueError:
    state=seed(report,d);damping=.5
  else:raise SystemExit('Bounded native budget exhausted: '+case)
 print('All six tapered cases passed their listed criteria.',flush=True)
if __name__=='__main__':main()
