"""Reflect accepted A12-left search state by actual spring/cell coordinates."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive',type=Path)
parser.add_argument('target_input',type=Path)
parser.add_argument('target_report',type=Path)
parser.add_argument('output',type=Path)
parser.add_argument('--no-reflect',action='store_true')
args = parser.parse_args()
archive = args.archive
report = json.loads(gzip.decompress((archive/'report.json.gz').read_bytes()))
manifest = json.loads((archive/'manifest.json').read_text())
source = Path(manifest['native_directory'])/report['contact_cycles'][-1]['directory']/'input.json'
expected_input_hash = report['artifact_sha256'][str(source.relative_to(Path(manifest['native_directory'])))]
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_input_hash
for name, expected in manifest['files'].items():
 assert hashlib.sha256((archive/name).read_bytes()).hexdigest() == expected
target = args.target_input
current = json.loads(args.target_report.read_text())
reflection = [1,1,1] if args.no_reflect else [-1,1,1]
a,b = [json.loads(p.read_text()) for p in (source,target)]
assert report['numerically_accepted'] and report['floor_friction_law']['mu_assumed'] == .4
assert a['candidate'] == b['candidate']
assert a['materials'] == b['materials']
assert a['floor_tangent_cells'] == b['floor_tangent_cells']
assert a['members'] == b['members']
rows = [[s for s in r['springs'] if s['bearing_closed_assumption'] and s['name'] not in r['floor_tangent_cells']] for r in (a,b)]
points = [np.array([r['nodes'][str(s['nodes'][0])] for s in ss]) for r,ss in zip((a,b),rows)]
points[0] *= reflection
indices = cKDTree(points[1]).query_ball_point(points[0],1.e-5)
active = {v['name'] for v in report['bearings'] if v['active']}
mapping, unmatched = {}, []
for s, matches in zip(rows[0],indices):
 matches = [i for i in matches if rows[1][i]['dof'] == s['dof'] and abs(rows[1][i]['stiffness_n_per_mm']-s['stiffness_n_per_mm']) < 1.e-5*max(1,s['stiffness_n_per_mm'])]
 if len(matches) != 1:
  unmatched.append({'name':s['name'],'matches':len(matches)})
 else:
  mapping[s['name']] = rows[1][matches[0]]['name']
cells = b['floor_tangent_cells']
cellmap = {}
for name,cell in a['floor_tangent_cells'].items():
 point = np.array(cell['point_xyz_mm'])*reflection
 matches = [n for n,c in cells.items() if np.linalg.norm(np.array(c['point_xyz_mm'])-point)<1.e-5 and c['elastic_tangent_n_per_mm'] == cell['elastic_tangent_n_per_mm']]
 assert len(matches)==1,(name,matches)
 cellmap[name] = matches[0]
floor_normals = {c['normal_contact'] for c in cells.values()}
floor_map = {a['floor_tangent_cells'][name]['normal_contact']:cells[other]['normal_contact'] for name,other in cellmap.items()}
nonfloor_active = {s['name'] for s in current['bearings'] if s['active'] and s['name'] not in floor_normals}
output = {'scope':'Only floor normal and friction states reflected; current K12-right initial non-floor contacts retained because panel seating mesh lacks exact reflection. Different hold needs full fresh native acceptance',
 'initial_contact_names':sorted(nonfloor_active | {other for name,other in floor_map.items() if name in active}),
 'initial_tangent_secants':{cellmap[n]:v['next_secant_n_per_mm'] for n,v in report['floor_friction_law']['feet'].items()},
 'reflection_xyz':reflection,'normal_mapping':floor_map,'nonfloor_mapping_rejections':unmatched,'cell_mapping':cellmap,'normal_count':len(floor_map),'cell_count':len(cellmap),
 'coordinate_match_tolerance_mm':1.e-5,
 'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,target,args.target_report,archive/'report.json.gz',Path(__file__))}}
args.output.write_text(json.dumps(output,indent=2)+'\n')
print('Mapped',len(floor_map),'floor normal springs and',len(cellmap),'friction cells')
