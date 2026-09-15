import json,pickle,subprocess,os,hashlib
from pathlib import Path
from fea import current_response_run as native
from fea import horizontal_panel_frame as frame
from fea.reinforced_frame_demand import active_with_friction
old=Path('fea/generated/clear-space-exterior-controlled-a12-left')
root=Path('fea/generated/exterior-single-contact-search');root.mkdir(exist_ok=False)
cached=pickle.loads((old/'model.pkl').read_bytes());current=native.source_hashes()
assert all(current.get(k)==v for k,v in cached['source_sha256'].items())
(root/'source-check.json').write_text(json.dumps({'old':cached['source_sha256'],'current':current,'search_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
structure,metadata=cached['model']; springs={s['name'] for s in structure.springs}
report=json.loads((old/'report.json').read_text())
active=active_with_friction({r['name'] for r in report['bearings'] if r['active']},springs,metadata['connection_ownership'])
seen={tuple(sorted(active))}
for i in range(100):
 violations=[r for r in report['bearings'] if not r['compression_only_assumption_satisfied']]
 if not violations:
  (root/'seed.json').write_text(json.dumps(sorted(r['name'] for r in report['bearings'] if r['active'])))
  print('CONVERGED',i,flush=True);break
 # Largest geometric violation first; skip previously visited active sets.
 for row in sorted(violations,key=lambda r:(-abs(r['opening_mm']),r['name'])):
  normals={r['name'] for r in report['bearings'] if r['active']};normals.symmetric_difference_update({row['name']})
  proposed=active_with_friction(normals,springs,metadata['connection_ownership'])
  if tuple(sorted(proposed)) not in seen:break
 else:raise RuntimeError('No unvisited single-contact pivot')
 active=proposed;seen.add(tuple(sorted(active)))
 job=root/f'cycle-{i:03}';job.mkdir()
 record=frame.record_structure(structure,metadata,active)
 (job/'input.json').write_text(json.dumps(record))
 (job/'frame.inp').write_text(structure.deck(active_bearings=active,stress=False).replace('*END STEP','*NODE FILE,OUTPUT=3D\nU\n*END STEP'))
 cmd=['docker','run','--rm','--network=none','--cpus=1','--memory=4g','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/output','-w','/output',frame.panel_kernel.IMAGE,'timeout','240s','ccx','-i','frame']
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=260);(job/'frame.log').write_text(result.stdout+result.stderr);result.check_returncode()
 report=native.assess(record,(job/'frame.dat').read_text(),(job/'frame.frd').read_text(),(job/'frame.12d').read_text(),expected_candidate=metadata['candidate'])
 (job/'report.json').write_text(json.dumps(report))
 print(json.dumps({'cycle':i,'pivot':row['name'],'violations':sum(not r['compression_only_assumption_satisfied'] for r in report['bearings']),'max_violation_mm':max([abs(r['opening_mm']) for r in report['bearings'] if not r['compression_only_assumption_satisfied']]+[0]),'equilibrium':report['global_equilibrium_passed'],'member_eq':report['member_equilibrium_passed']}),flush=True)
else:print('BOUNDED_SEARCH_EXHAUSTED',flush=True)
