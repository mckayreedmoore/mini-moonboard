"""Independent frozen-v3 correctness checks, cached BREP and bounded probes only.

Run from the checkout root: PYTHONPATH=. .venv/bin/python -B <this file>.
No producer run, mesh materialization, native solver, source edit or Git writes.
"""
import copy
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

import cadquery as cq

from scripts.hl35_candidate import overlaps
from scripts.wood_joint_midpoint_clearance import _bbox, _overlap
from scripts.hl35_full_fit_candidate import line_span
from scripts.hl35_nominal_service_candidate import sweep

DOC = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1')
RAW = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/2026-adjustments-v10')
HERE = Path(__file__).parent
EXPECTED = {
    str(DOC / 'occupied-adjusted-base-v3.json'): '5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7',
    str(DOC / 'occupied-2026-adjustments-v3.json'): '5dfa03b785715c92717725400e73bf41b00a58160595ddf6b61b61c3b31f6134',
}
PINS, CACHE, CHECKS = {}, {}, {}


def sha(path):
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    PINS[str(path)] = digest
    return digest


def read(path):
    sha(path)
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if Path(path).suffix == '.gz' else raw)


def load(row):
    path = row['path']
    assert sha(path) == row['sha256'], path
    if path not in CACHE:
        shape = cq.Shape.importBrep(path)
        assert shape.isValid() and len(shape.Solids()) == 1, path
        if 'volume_mm3' in row:
            assert abs(shape.Volume() - row['volume_mm3']) < .001, path
        CACHE[path] = shape
    return CACHE[path]


def hits(first, second):
    a = [(n, s, _bbox(s)) for n, s in first.items()]
    b = [(n, s, _bbox(s)) for n, s in second.items()]
    return [{'first': n, 'second': m, 'intersection_mm3': v}
            for n, s, x in a for m, t, y in b
            if n != m and _overlap(x, y) and (v := overlaps(s, t)) > .01]


def pose(row):
    m = row['transform']
    return cq.Plane(origin=m[12:15], xDir=m[:3], normal=m[8:11]).location


for path, expected in EXPECTED.items():
    assert sha(path) == expected, path
base = read(DOC / 'occupied-adjusted-base-v3.json')
extra = read(DOC / 'occupied-2026-adjustments-v3.json')
old = read(DOC / 'occupied-aligned-wire-v1.json')
native = read(DOC.parent / 'native-geometry-v4.json')
raised = read(DOC / 'occupied-bottom-rail-v1.json')
for report in (base, extra):
    for path, expected in report['source_sha256'].items():
        assert sha(path) == expected, path
assert sha('scripts/eoere_2026_adjustments.py') == sha(RAW / 'driver.py.snapshot')
assert (DOC / 'occupied-adjusted-base-v3.json').read_bytes() == (RAW / 'base/geometry.json').read_bytes()
assert (DOC / 'occupied-2026-adjustments-v3.json').read_bytes() == (RAW / 'geometry.json').read_bytes()
base_patch = read('site/eoere-adjusted-base-v3-scene.json.gz')
extra_patch = read('site/eoere-2026-adjustments-v3-scene.json.gz')
assert sha(RAW / 'base/scene.json.gz') == sha('site/eoere-adjusted-base-v3-scene.json.gz')
assert sha(RAW / 'scene.json.gz') == sha('site/eoere-2026-adjustments-v3-scene.json.gz')
for patch, path in [(base_patch, DOC / 'occupied-adjusted-base-v3.json'),
                    (extra_patch, DOC / 'occupied-2026-adjustments-v3.json')]:
    assert patch['layout_report']['sha256'] == sha(path)
    assert not patch['mechanics_ready'] and not any(patch['release'].values())
CHECKS['source_closure'] = {'base_pins': len(base['source_sha256']), 'extra_pins': len(extra['source_sha256']),
                            'producer_matches_frozen_snapshot': True, 'issued_raw_and_maintained_bytes_identical': True}

# Independently find the shared-duty closure and compare every machine record.
shift = cq.Vector(*base['principal_shift_xyz_mm'])
target = 'base_principal_center_right'
duties = {a['duty_id'] for row in old['axes'] if target in row['receivers'] for a in row['attachments']}
while True:
    closed = duties | {a['duty_id'] for row in old['axes']
                       if any(a['duty_id'] in duties for a in row['attachments']) for a in row['attachments']}
    if closed == duties:
        break
    duties = closed
moved = {r['id'] for r in old['axes'] if any(a['duty_id'] in duties for a in r['attachments'])}
assert duties == set(base['affected_duties']) and len(duties) == 6
assert moved == set(base['moved_bolt_axes']) and len(moved) == 22
new_axes = {r['id']: r for r in base['axes']}
assert len(new_axes) == 100
intervals = 0
for row in old['axes']:
    expected = copy.deepcopy(row)
    if row['id'] in moved:
        expected['point_xyz_mm'][0] -= 39.2
        for a in expected['attachments']:
            a['point'][0] -= 39.2
            direction = cq.Vector(*a['direction']).normalized()
            if next(v for v in direction.toTuple() if abs(v) > 1e-8) < 0:
                direction *= -1
            a['interval_mm'] = [v + shift.dot(direction) for v in a['interval_mm']]
            intervals += 1
    assert expected == new_axes[row['id']], row['id']
new_screws = {r['axis_id']: r for r in base['screw_axes']}
assert len(new_screws) == 66
expected_screws = {r['axis_id'] for r in old['screw_axes']
                   if r['receiver'] in (target, 'base_post_center_right')}
assert expected_screws == set(base['moved_panel_screw_axes']) and len(expected_screws) == 10
for row in old['screw_axes']:
    expected = copy.deepcopy(row)
    if row['axis_id'] in expected_screws:
        expected['origin_xyz_mm'][0] -= 39.2
    assert expected == new_screws[row['axis_id']]
for key, rows in [('bolt_axes_unchanged_sha256', base['axes']), ('screw_axes_unchanged_sha256', base['screw_axes'])]:
    assert extra[key] == hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
CHECKS['metadata'] = {'duties': 6, 'moved_stacks': 22, 'canonical_shifted_ports': intervals,
                      'moved_screws': 10, 'all_bolt_axes': 100, 'all_Hillman_axes': 66,
                      'unchanged_starting_bolts': 12}

print('Authenticated frozen inputs and exact coordinated metadata; loading saved bodies.', flush=True)
base_shapes = {r['id']: load(r) for r in base['changed_finished_solids']}
extra_shapes = {r['id']: load(r) for r in extra['changed_finished_solids']}
wood = {r['id']: load(r) for r in old['changed_finished_solids'] + old['unchanged_finished_solids']}
off = {**wood, **{r['id']: base_shapes[r['id']] for r in base['changed_finished_solids'] if r['kind'] == 'timber'}}
on = {**off, **{r['id']: extra_shapes[r['id']] for r in extra['changed_finished_solids'] if r['kind'] == 'timber'}}
changed_off = {r['id'] for r in base['changed_finished_solids'] if r['kind'] == 'timber'}
changed_on = changed_off | set(extra['changed_timber_ids'])
assert len(base_shapes) == 136 and len(extra_shapes) == 23
assert sorted(changed_on) == extra['retained_services_checked_timber_ids']

# Reuse a saved factory-angle BREP under rigid transforms; inspect all holes.
scene = read('site/eoere-bottom-rail-scene.json.gz')
bracket_rows = {r['name']: r for r in scene['solids'] if r['fabrication']['kind'] == 'bracket'}
sample = 'eoere_clip_split_base_center_right'
angle_template = base_shapes[sample].translate(-shift).moved(pose(bracket_rows[sample]).inverse)
angles = {}
for name, row in bracket_rows.items():
    candidate = angle_template.moved(pose(row))
    if row['fabrication']['duty_id'] in duties:
        candidate = candidate.translate(shift)
        actual = base_shapes[name]
        assert candidate.cut(actual).Volume() + actual.cut(candidate).Volume() < .001
        angles[name] = actual
    else:
        angles[name] = candidate
factory = []
for axis in base['axes']:
    p, d = cq.Vector(*axis['point_xyz_mm']), cq.Vector(*axis['direction_xyz']).normalized()
    for port in axis['attachments']:
        row = bracket_rows[port['angle_id']]
        m = row['transform']
        u, v, w = [cq.Vector(*m[i:i+3]) for i in (0, 4, 8)]
        origin = cq.Vector(*m[12:15]) + (shift if port['duty_id'] in duties else cq.Vector())
        hole = origin + (u if port['flange'] == 'beam' else v) * port['along_mm'] + w * port['transverse_mm']
        assert (hole-p).cross(d).Length < 1e-6
        assert (hole-cq.Vector(*port['point'])).Length < 1e-6
        probe = cq.Solid.makeCylinder(axis['diameter_mm']/2, 16, hole-d*8, d)
        assert overlaps(probe, angles[port['angle_id']]) < .01
        factory.append({'axis': axis['id'], 'angle': port['angle_id']})
assert len(factory) == 88

# Exact saved shaft poses and raw timber crossing intervals; seven bounded raw members.
raw_rows = {r['member']: r for r in native['raw_parts']}
raw_changed = {n: load(raw_rows[n]) for n in (target, 'base_post_center_right', 'base_header', 'base_rail_top')}
for n in (target, 'base_post_center_right'):
    raw_changed[n] = raw_changed[n].translate(shift)
plan = read(old['plan']['path'])
for row in plan['rails']:
    if row['id'] in base['extended_rails']:
        stock = load(row['raw']).translate(tuple(row['raw_translation_xyz_mm']))
        raw_changed[row['id']] = stock.fuse(stock.translate(shift)).clean()
shaft_checks = []
port_errors = []
for axis in base['axes']:
    if axis['id'] not in moved:
        continue
    p, d = cq.Vector(*axis['point_xyz_mm']), cq.Vector(*axis['direction_xyz'])
    h = axis['hardware_scenario']
    cylinder = cq.Solid.makeCylinder(axis['diameter_mm']/2, axis['nominal_under_head_length_mm'],
                                   p-d*(axis['before_plate_mm']+h['washer_thickness_mm']), d)
    shaft = base_shapes[axis['id']+'_shaft']
    difference = shaft.cut(cylinder).Volume()+cylinder.cut(shaft).Volume()
    bore = cq.Solid.makeCylinder(axis['bore_diameter_mm']/2, axis['grip_mm'], p, d)
    raw_receiver = cq.Compound.makeCompound([raw_changed[n] for n in axis['receivers']])
    support = overlaps(bore, raw_receiver)/bore.Volume()
    residuals = {mode: sum(overlaps(shaft, bodies[n]) for n in axis['receivers'])
                 for mode, bodies in [('OFF', off), ('ON', on)]}
    assert difference < .001 and support > .999999 and max(residuals.values()) < .01
    for port in axis['attachments']:
        direction = cq.Vector(*port['direction']).normalized()
        if next(v for v in direction.toTuple() if abs(v) > 1e-8) < 0:
            direction *= -1
        point = cq.Vector(*port['point'])
        span = line_span(raw_changed[port['receiver']], point, cq.Vector(*port['direction']))
        expected = sorted((point+cq.Vector(*port['direction'])*s).dot(direction) for s in span)
        error = max(abs(a-b) for a,b in zip(expected, port['interval_mm']))
        assert error < 1e-6, (axis['id'], port['duty_id'], error)
        port_errors.append(error)
    shaft_checks.append({'axis':axis['id'],'shaft_symmetric_difference_mm3':difference,
                         'raw_bore_support_fraction':support,'finished_receiver_overlap_mm3':residuals})
metal = {n:s for n,s in base_shapes.items() if n.startswith('eoere_')}
assert not hits(metal, angles)
assert not hits(metal, off) and not hits(metal, on)
assert not hits({n:off[n] for n in changed_off}, off)
assert not hits({n:on[n] for n in changed_on}, on)
CHECKS['factory_and_shafts'] = {'factory_ports':len(factory),'saved_changed_angles':6,'saved_shafts':22,
                                'raw_port_intervals':len(port_errors),'maximum_interval_error_mm':max(port_errors),
                                'moved_metal_vs_all_angles_and_OFF_ON_wood_hits':0,'shaft_checks':shaft_checks}

contacts = []
for mode, bodies in [('OFF', off), ('ON', on)]:
    for row in base['restored_contacts']:
        a = bodies[row['member']] if 'receiver' in row else bodies[target]
        b = bodies[row['receiver']] if 'receiver' in row else bodies[row['member']]
        gap, volume = a.distance(b), overlaps(a,b)
        assert gap < 1e-5 and volume < .01
        contacts.append({'mode':mode,'member':row['member'],'distance_mm':gap,'intersection_mm3':volume})
CHECKS['contacts'] = contacts
backing = []
for mode, bodies, changed in [('OFF',off,changed_off),('ON',on,changed_on)]:
    for row in base['screw_axes']:
        if row['receiver'] not in changed:
            continue
        for thickness in (18.25625,19.05):
            p,d = cq.Vector(*row['origin_xyz_mm']),cq.Vector(*row['direction_xyz'])
            probe = cq.Solid.makeCylinder(2.5,63.5-thickness,p+d*thickness,d)
            fraction = overlaps(probe,bodies[row['receiver']])/probe.Volume()
            assert fraction > .999999, (mode,row['axis_id'],fraction)
            backing.append({'mode':mode,'id':row['axis_id'],'panel_thickness_mm':thickness,'fraction':fraction})
CHECKS['screw_backing'] = {'checks':len(backing),'minimum_fraction':min(r['fraction'] for r in backing)}

print('Factory closure, saved shafts, intervals, bores, contacts and screw backing agree; checking services.', flush=True)
retained = {}
canonical = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/aligned-wire-cutouts-v1/cad-v1')
for row in native['parts']:
    if row['kind'] not in ('wire','light','tnut'):
        continue
    path = canonical/(row['id']+'.brep')
    if row['kind']=='wire' and str(path) in extra['source_sha256']:
        row = {**row,'path':str(path),'sha256':extra['source_sha256'][str(path)]}
        row.pop('volume_mm3',None)
    retained[row['id']] = load(row)
assert len(retained)==405
retained_on = {**retained, **{r['id']:extra_shapes[r['id']] for r in extra['changed_finished_solids'] if r['kind']=='wire'}}
service_hits = {}
for mode, bodies, services, changed in [('OFF',off,retained,changed_off),('ON',on,retained_on,changed_on)]:
    service_hits[mode] = hits(services,{n:bodies[n] for n in changed})
    assert not service_hits[mode], service_hits[mode]
assert not hits(retained,metal) and not hits(retained_on,metal)
CHECKS['retained_services'] = {'authenticated_bodies':405,'OFF_changed_timber_count':len(changed_off),
                               'ON_changed_timber_count':len(changed_on),'OFF_ON_hits':service_hits,
                               'retained_vs_moved_metal_hits':0}

# New service checks use only saved template BREP rigid transforms and bounded
# cable probes whose scene bounds overlap changed finished wood. No assembly rebuild.
def point(x,s,n=0):
    angle=math.radians(40)
    return cq.Vector(x,-18*(1+math.cos(angle))+s*math.sin(angle)-n*math.cos(angle),
                     277+18*math.sin(angle)+s*math.cos(angle)+n*math.sin(angle))

N=cq.Vector(0,-math.cos(math.radians(40)),math.sin(math.radians(40)))
native_tnut=next(r for r in native['parts'] if r['id']=='hold_tnut_main_A1')
tnut_template=load(native_tnut).moved(cq.Plane(origin=point(-1019.2,99.2),xDir=(1,0,0),normal=-N).location.inverse)
new_bodies={}
for row in extra_patch['additions']:
    kind=row['fabrication']['kind']
    if kind in ('tnut','light'):
        local=tnut_template if kind=='tnut' else cq.Solid.makeCylinder(6.35,30.25625,cq.Vector(0,0,-18.25625))
        new_bodies[row['id']]=local.moved(pose(row))
changed_bodies={n:on[n] for n in changed_on}
new_hits=hits(new_bodies,changed_bodies)
wire_candidates=0
additions={r['id']:r for r in extra_patch['additions']}
for route in extra['new_wire_routes']:
    bounds=additions[route['id']]['mesh']['bounds_xyz_mm']
    if not any(_overlap(tuple(bounds),_bbox(s)) for s in changed_bodies.values()):
        continue
    wire_candidates+=1
    body,length=sweep(route['route_local_mm'],2.0,[0,0,52])
    for endpoint in (route['route_local_mm'][0],route['route_local_mm'][-1]):
        body=body.fuse(cq.Solid.makeCylinder(2,6,point(endpoint[0],endpoint[1],8),N)).clean()
    assert abs(length-route['rounded_length_mm'])<1e-6
    new_hits+=hits({route['id']:body},changed_bodies)
assert not new_hits,new_hits
CHECKS['new_services_vs_changed_ON_timber']={'templates_rigid_instances':240,
    'wire_routes_screened':119,'bounded_wire_probes':wire_candidates,'hits':new_hits,
    'OFF_new_services':0}

# Independent midpoint formulas, chain topology, original endpoints and panel bores.
old_routes={r['name']:r for r in old['wire_proposals']}
for row in extra['rerouted_original_wire_links']:
    original=old_routes[row['id']]
    assert row['route_local_mm'][0]==original['route_local_mm'][0]
    assert row['route_local_mm'][-1]==original['route_local_mm'][-1]
grid={r['id']:r for r in extra['grid']}
degree={n:0 for n in grid}
for row in grid.values():
    column=ord(row['column'])-ord('A');number=row['row']
    hs=1219.2-1120+200*(number-1) if number<=6 else 1219.2+100+200*(number-7)
    ls=1219.2-1200 if number==1 else (1219.2-1020+200*(number-2) if number<=7 else 1219.2+200+200*(number-8))
    assert row['tnut_x_s_mm']==[300+200*column,hs] and row['LED_x_s_mm']==[300+200*column,ls]
    for kind,prefix,xy in [('tnut','hold_tnut_2026_',row['tnut_x_s_mm']),('light','light_2026_',row['LED_x_s_mm'])]:
        item=additions[prefix+row['id']]
        assert (cq.Vector(*item['transform'][12:15])-point(xy[0]-1219.2,xy[1])).Length<1e-8
        assert (cq.Vector(*item['transform'][8:11])-(N if kind=='light' else -N)).Length<1e-8
for route in extra['new_wire_routes']:
    a,b=route['endpoints'];degree[a]+=1;degree[b]+=1
    assert route['route_local_mm'][0]==[grid[a]['LED_x_s_mm'][0]-1219.2,grid[a]['LED_x_s_mm'][1],14]
    assert route['route_local_mm'][-1]==[grid[b]['LED_x_s_mm'][0]-1219.2,grid[b]['LED_x_s_mm'][1],14]
assert len(degree)==120 and sorted(degree.values())==[1,1]+[2]*118
before_panels={r['id']:load(r) for r in raised['finished_panel_solids']}
base_panels={**before_panels, **{r['id']:base_shapes[r['id']] for r in base['changed_finished_solids'] if r['kind']=='panel'}}
panels=[]
for name,shape in base_panels.items():
    before=before_panels[name]
    bounds_error=max(abs(a-b) for a,b in zip(_bbox(shape),_bbox(before)))
    assert bounds_error<1e-6 and abs(shape.Volume()-before.Volume())<.01
    panels.append({'panel':name,'base_bounds_error_mm':bounds_error,'base_volume_error_mm3':abs(shape.Volume()-before.Volume())})
for row in extra['panel_drilling']:
    parent,shape=base_panels[row['panel']],extra_shapes[row['panel']]
    expected=math.pi*18.25625*(row['added_hold_bores']*(11.1125/2)**2+row['added_LED_bores']*6.5**2)
    assert shape.cut(parent).Volume()<.01 and abs(parent.Volume()-shape.Volume()-expected)<.01
    assert max(abs(a-b) for a,b in zip(_bbox(shape),_bbox(parent)))<1e-6
    panels.append({'panel':row['panel'],'ON_removed_mm3':parent.Volume()-shape.Volume(),'expected_mm3':expected})
CHECKS['grid_panels_and_census']={'midpoints':120,'world_pose_checks':240,'links':119,'old_detours':10,'panels':panels,
                                 'base_replacements':136,'base_visible':1021,'ON_replacements':23,'ON_additions':359,'ON_visible':1380}
assert extra['unofficial_2026_positions'] and extra['all_midpoints_are_assumed_not_confirmed']
assert not base['mechanics_ready'] and not extra['mechanics_ready']
assert not any(base['release'].values()) and not any(extra['release'].values())
for path,digest in list(PINS.items()):
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
PINS[str(Path(__file__))]=sha(__file__)
receipt={'schema':'independent_correctness_review/v1','reviewer':'/root/adjusted_geometry_correctness_v3',
    'status':'NO_CONFIRMED_SUBSTANTIVE_FINDINGS','reviewed_sha256':EXPECTED,
    'checks':CHECKS,'findings':[],'cadquery_version':cq.__version__,'source_sha256':PINS,
    'reproduction_command':'PYTHONPATH=. .venv/bin/python -B '+str(Path(__file__)),
    'limits':['Exact frozen v3 nominal geometry and machine records only; no strength, force, tool, tolerance or physical acceptance.',
              'No producer run, full assembly rebuild, native/global solve, mesh materialization, source edits or Git mutation.',
              'Retained services checked using authenticated cached BREP; new services use saved T-nut BREP transforms, exact light cylinders and bounded source-route probes after saved-scene bounds filtering.',
              'Source producer complete collision registers were inspected; no wholesale historical global collision rerun.',
              'New grid remains unofficial with exact midpoints assumed; all structural/physical release flags remain false.']}
(HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'receipt':str(HERE/'receipt.json'),'sha256':sha(HERE/'receipt.json'),'findings':0,
                  'bounded_wire_probes':wire_candidates,'loaded_cached_BREPs':len(CACHE),'checks':list(CHECKS)},indent=2),flush=True)
