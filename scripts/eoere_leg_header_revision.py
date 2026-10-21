"""Compose the owner-directed leg pins, lower header angles and plywood cleats.

Reuse authenticated current solids and factory angle/hardware helpers. This is
development geometry; fresh response and resistance checks remain separate.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from unittest.mock import patch

from scripts import eoere_builder_layout as shop
from scripts.eoere_current_shop_followup import ROOT, csv_bytes, module, require, sha

DOC = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1')
INPUT = Path('docs/bolted-frame-development/single-bolt-legs-header-angles-inputs-v3.json')
PLYWOOD = Path('docs/bolted-frame-development/plywood-cleat-single-leaf-inputs-v2.json')
BASE = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/single-leg-header-integration-v1')
REVISION = 'eoere-single-leg-bolts-header-angles-v3'


def verify_attachment_axes(axes):
    """Every steel port must lie on its installed physical shaft axis."""
    seen = set()
    for axis in axes:
        p, d = axis['point_xyz_mm'], axis['direction_xyz']
        require(abs(sum(x*x for x in d)-1.) < 1e-8, 'unit shaft axis required')
        for port in axis['attachments']:
            delta = [a-b for a, b in zip(port['point'], p, strict=True)]
            along = sum(a*b for a, b in zip(delta, d, strict=True))
            radial = math.sqrt(sum((a-along*b)**2 for a, b in zip(delta, d, strict=True)))
            require(radial < 1e-6 and min(abs(along), abs(along-axis['grip_mm'])) < 1e-6,
                    'fitting port is off its installed axis: '+axis['id'])
            require(port['installed_bolt_axis_id'] == axis['id'], 'installed axis identity differs')
            key = (port['angle_id'], port['flange'], port['transverse'])
            require(key not in seen, 'fitting port bound twice')
            seen.add(key)
    require(len(seen) == 96, 'all96 unique fitting ports required')


def build(out):
    require(Path.cwd() == ROOT and out.resolve().is_relative_to(ROOT/BASE)
            and not out.exists(), 'fresh ignored revision output required')
    pins = {}

    def pin(path, expected=None):
        path = Path(path)
        digest = sha(path)
        require(expected is None or expected == digest, 'source changed: '+str(path))
        require(pins.get(str(path), digest) == digest, 'conflicting source: '+str(path))
        pins[str(path)] = digest
        return path

    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())

    index = json.loads(shop.INDEX.read_bytes())
    require(index['geometry']['revision'] == 'eoere-centred-enclosed-passages-v1', 'enclosed parent required')
    inputs, plywood = read(INPUT), read(PLYWOOD)
    parent = read(index['geometry']['receipt']['path'], index['geometry']['receipt']['sha256'])
    require(inputs['parent_geometry'] == index['geometry']['receipt'], 'input parent differs')
    require(plywood['leaves_per_corner'] == 1 and not plywood['geometry_adopted'], 'single-leaf proposal required')
    reader = shop.read_bound

    def recorded(root, ref):
        pin(root/ref['path'], ref['sha256'])
        return reader(root, ref)

    with patch.object(shop, 'read_bound', recorded):
        data = shop.load_sources()
    shop.validate(data)
    profiles = copy.deepcopy(data['profiles'])
    selections = {r['axis_id']: r for r in data['selected']}
    holes = data['holes']
    frozen = read(DOC/'selected-hardware-v1/current-response-v1/result.json')
    old = read(frozen['input']['path'], frozen['input']['sha256'])
    axes = {r['axis_id']: copy.deepcopy(r['source_axis']) for r in old['shafts']}
    post_revision = read(DOC/'occupied-front-posts-4x6-v1.json')
    axes.update(copy.deepcopy(post_revision['axis_overrides']))
    for a in axes.values():
        a['nominal_under_head_length_mm'] = float(selections[a['id']]['selected_underhead_length_mm'])
    poses = copy.deepcopy(old['fitting_poses'])
    out.mkdir(parents=True)
    (out/'parent-index.json').write_bytes(shop.INDEX.read_bytes())
    (out/'producer-snapshot.py').write_bytes(Path(__file__).read_bytes())
    pin(out/'parent-index.json')
    pin(Path(__file__).relative_to(ROOT))
    pin(Path(shop.__file__).relative_to(ROOT))

    import cadquery as cq

    from scripts import eoere_bolted_candidate as angles
    from scripts import thin_bolted_occupied as hardware

    bodies, changed, restores = {}, {}, []

    def load(name):
        if name not in bodies:
            ref = profiles[name]['finished']
            pin(ref['path'], ref['sha256'])
            bodies[name] = cq.Shape.importBrep(ref['path'])
        return bodies[name]

    def restore(axis_id):
        a = axes[axis_id]
        p, d = cq.Vector(*a['point_xyz_mm']), cq.Vector(*a['direction_xyz'])
        for h in (r for r in holes if r['axis_id'] == axis_id):
            name = h['receiver']
            before = load(name)
            lo, hi = float(h['entry_from_axis_point_mm']), float(h['exit_from_axis_point_mm'])
            # All affected bores cross constant-X stock faces, with contained
            # circular walls; their issued endpoints retain the foot recess.
            require(abs(d.x) == 1 and hi > lo, 'constant-X issued bore required')
            repair = cq.Solid.makeCylinder(a['bore_diameter_mm']/2, hi-lo, p+d*lo, d)
            expected = math.pi*(a['bore_diameter_mm']/2)**2*(hi-lo)
            require(before.intersect(repair).Volume() < 1e-4, 'restoration overlaps retained wood')
            after = before.fuse(repair).clean()
            require(after.isValid() and len(after.Solids()) == 1
                    and abs(after.Volume()-before.Volume()-expected) < .01, 'bore restoration differs')
            bodies[name] = changed[name] = after
            restores.append({'axis_id': axis_id, 'member': name, 'restored_mm3': expected})

    for identity in inputs['remove_leg_axis_ids']:
        restore(identity)
        del axes[identity]
        del selections[identity]
    # Rebuild the two plywood leaves directly, preserving their specified
    # outboard placement and the current runner seating elevation.
    for side in ('left', 'right'):
        name = 'eoere_cleat_'+side
        thickness = plywood['nominal_thickness_mm']
        inner = plywood['inboard_X_face_mm'][side]
        x = inner-thickness if side == 'left' else inner
        body = cq.Solid.makeBox(thickness, plywood['blank_Y_Z_mm'][0], plywood['blank_Y_Z_mm'][1],
            cq.Vector(x, plywood['Y_bounds_mm'][0], plywood['bottom_Z_mm']))
        bodies[name] = changed[name] = body
        profile = profiles[name]
        profile.update(kind='timber', material='proposed structural plywood',
            blank_mm=[plywood['blank_Y_Z_mm'][1], plywood['blank_Y_Z_mm'][0], thickness],
            datum_xyz_mm=[x, plywood['Y_bounds_mm'][0], plywood['bottom_Z_mm']],
            basis_grain_u_v_xyz=[[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
            vertices_luv_mm=[[l, u, v] for l in (0., plywood['blank_Y_Z_mm'][1])
                            for u in (0., thickness) for v in (0., plywood['blank_Y_Z_mm'][0])],
            end_planes=[])
    # Restoring a moved lower post hole affects the post only: the plywood
    # leaf above has no holes yet. Keep the source restoration independently.
    for identity, a in list(axes.items()):
        if identity.startswith('cleat_post_bolt_'):
            for h in (r for r in holes if r['axis_id'] == identity and r['receiver'].startswith('base_post_outer_')):
                name = h['receiver']
                p, d = cq.Vector(*a['point_xyz_mm']), cq.Vector(*a['direction_xyz'])
                lo, hi = float(h['entry_from_axis_point_mm']), float(h['exit_from_axis_point_mm'])
                repair = cq.Solid.makeCylinder(a['bore_diameter_mm']/2, hi-lo, p+d*lo, d)
                bodies[name] = changed[name] = load(name).fuse(repair).clean()
            side = 'left' if '_left_' in identity else 'right'
            inner = plywood['inboard_X_face_mm'][side]
            a['point_xyz_mm'][0] = -1130.3 if side == 'left' else 1127.125
            a['direction_xyz'] = [-1., 0., 0.] if side == 'left' else [1., 0., 0.]
            a['before_plate_mm'], a['after_plate_mm'] = 6.35, 0.
            a['point_xyz_mm'][2] = inputs['existing_lower_cleat_post_row_Z_mm']
            a['grip_mm'] = 88.9+plywood['nominal_thickness_mm']
        elif any(n.startswith('eoere_cleat_') for n in a['receivers']):
            a['grip_mm'] = 88.9+plywood['nominal_thickness_mm']
    template = angles.template(angles.Scenario())
    added_angles = {}
    for pose in inputs['new_header_angles']:
        placed = angles.pose(pose, template)
        require(placed.id == pose['id'], 'angle identity differs')
        added_angles[placed.id] = placed.shape
        poses.append({k: v for k, v in pose.items() if k != 'shared_header_axis_ids'})
        for identity in pose['shared_header_axis_ids']:
            axes[identity]['after_plate_mm'] = 6.35
        side = 'left' if pose['id'].endswith('left') else 'right'
        for hole in angles.Scenario().holes(active_only=True):
            beam = hole['flange'] == 'beam'
            along = pose['u_xyz'] if beam else pose['v_xyz']
            inward = [-v for v in (pose['v_xyz'] if beam else pose['u_xyz'])]
            point = [pose['origin_xyz_mm'][j]+along[j]*hole['along_mm']
                     +pose['w_xyz'][j]*hole['transverse_mm'] for j in range(3)]
            if beam:
                identity = next(i for i in pose['shared_header_axis_ids']
                                if abs(axes[i]['point_xyz_mm'][1]-point[1]) < 1e-7)
            else:
                identity = next(i for i in axes if i.startswith('cleat_post_bolt_'+side+'_')
                                and abs(axes[i]['point_xyz_mm'][1]-point[1]) < 1e-7)
            a = axes[identity]
            a.setdefault('attachments', []).append({**hole, 'angle_id': pose['id'],
                'duty_id': pose['duty_id'], 'receiver': 'base_header' if beam else pose['post'],
                'receivers': a['receivers'], 'point': point, 'direction': inward,
                'installed_bolt_axis_id': identity})
    verify_attachment_axes(list(axes.values()))
    require(len(axes) == 96 and len(poses) == 24, 'expected96 physical stacks and24 angles')
    # Fresh bores in the leaves/posts; the six leg/frame/runner restorations
    # otherwise retain their existing cuts and sole/recess profiles.
    for a in axes.values():
        if any(n.startswith('eoere_cleat_') for n in a['receivers']):
            p, d = cq.Vector(*a['point_xyz_mm']), cq.Vector(*a['direction_xyz'])
            cutter = cq.Solid.makeCylinder(a['bore_diameter_mm']/2, a['grip_mm']+2., p-d, d)
            for name in a['receivers']:
                if name.startswith(('eoere_cleat_', 'base_post_outer_')):
                    bodies[name] = changed[name] = load(name).cut(cutter).clean()
    for name, body in changed.items():
        require(body.isValid() and len(body.Solids()) == 1, 'invalid changed member: '+name)
    # Use the existing exact catalog-box inequalities, including both plate
    # flanges and the minimum proposed plywood thickness, before drawing metal.
    catalog_path = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/catalog-hardware-strength-v1/catalog-inputs.json')
    catalog = read(catalog_path)
    window_path = catalog_path.parent/'shop-window-v1/shop_windows.py'
    pin(window_path)
    windows = module(window_path, 'leg_header_catalog_windows')
    diameter = next(r for r in catalog['diameters'] if r['diameter_in'] == .375)
    products = copy.deepcopy(catalog['bolts'])
    base_product = next(r for r in products if r['diameter_in'] == .375 and r['nominal_length_in'] == 6.)
    for length, lb, lg, minus, sku in ((3.5, 2.19, 2.5, .06, 366),
                                       (5.5, 4.19, 4.5, .1, 370), (7., 5.44, 5.75, .18, 372)):
        if not any(r['diameter_in'] == .375 and r['nominal_length_in'] == length for r in products):
            products.append({**base_product, 'nominal_length_in': length, 'Lb_min_in': lb,
                'Lg_max_in': lg, 'length_tolerance_minus_in': minus,
                'minimum_full_thread_length_in': 1. if length <= 6 else 1.25, 'sku': sku,
                'url': 'https://boltdepot.com/Product-Details?product='+str(sku)})
    hardware_parts, choices = {}, []
    revised_ids = {a['id'] for a in axes.values() if any(n.startswith('eoere_cleat_') for n in a['receivers'])}
    revised_ids.update(i for p in inputs['new_header_angles'] for i in p['shared_header_axis_ids'])
    for identity in sorted(revised_ids):
        a = axes[identity]
        header = identity in {i for p in inputs['new_header_angles'] for i in p['shared_header_axis_ids']}
        length, spacer = ((3.5, 12.7) if header else (7., 25.4))
        bolt = next(r for r in products if r['diameter_in'] == .375 and r['nominal_length_in'] == length)
        stack = a['grip_mm']+a['before_plate_mm']+a['after_plate_mm']+spacer
        min_stack = stack-(plywood['nominal_thickness_mm']-plywood['minimum_proposed_actual_thickness_mm'] if not header else 0.)
        low, high = windows.bounds_for(min_stack, bolt, diameter), windows.bounds_for(stack, bolt, diameter)
        require(min(low['nut_near_minus_Lg_max_bounds_mm'][0],
                    high['catalog_min_length_max_stack_two_tip_margin_mm']) > 0, 'hardware window fails: '+identity)
        a['nut_side_spacer_mm'] = spacer
        a['hardware_scenario']['available_nominal_lengths_mm'] = [length*25.4]
        local = dict(hardware.local_hardware(a))
        if spacer:
            local['nut'] = local['nut'].translate((0, 0, spacer))
            for j in range(round(spacer/12.7)):
                start = a['grip_mm']+a['after_plate_mm']+a['hardware_scenario']['washer_thickness_mm']+12.7*j
                local['spacer' if j == 0 else 'spacer_2'] = cq.Solid.makeCylinder(19.05/2, 12.7, cq.Vector(0, 0, start)).cut(
                    cq.Solid.makeCylinder(10.31875/2, 12.7, cq.Vector(0, 0, start)))
            a['tip_projection_beyond_nut_mm'] -= spacer
        plane = cq.Plane(origin=cq.Vector(*a['point_xyz_mm']), normal=cq.Vector(*a['direction_xyz']))
        hardware_parts.update({identity+'_'+role: body.moved(plane.location) for role, body in local.items()})
        choices.append({**selections.get(identity, selections['eoere_bolt_067']), 'axis_id': identity,
            'selected_product': str(bolt['sku']), 'selected_product_url': bolt['url'],
            'selected_underhead_length_mm': length*25.4,
            'nut_side_spacer_mm': spacer, 'minimum_two_pitch_margin_mm': high['catalog_min_length_max_stack_two_tip_margin_mm'],
            'minimum_nut_seating_margin_mm': low['nut_near_minus_Lg_max_bounds_mm'][0],
            'minimum_full_body_mm': low['ASME_Lb_min_mm'], 'receiver_member_ids': ';'.join(a['receivers']),
            'minimum_body_mm': low['ASME_Lb_min_mm'], 'maximum_grip_gaging_mm': low['ASME_Lg_max_mm'],
            'receiver_plus_plate_nominal_mm': a['grip_mm']+a['before_plate_mm']+a['after_plate_mm'],
            'spacer_piece_count': round(spacer/12.7), 'spacer_piece_length_mm': 12.7 if spacer else 0.,
            'selected_recipe': 'head/head_washer/receivers/nut_washer/'+('spacer/'*round(spacer/12.7))+'nut',
            'Actual': '', 'Disposition': ''})
    saved = []

    def save(name, kind, body):
        path = out/(name+'.brep')
        require(body.exportBrep(str(path)), 'BREP export failed')
        box = body.BoundingBox()
        r = {'id': name, 'kind': kind, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
             'bytes': path.stat().st_size, 'volume_mm3': body.Volume(),
             'center_of_mass_xyz_mm': list(body.Center().toTuple()),
             'bounds_xyz_mm': [getattr(box, a+b) for a in 'xyz' for b in ('min', 'max')]}
        saved.append(r)
        return r

    for name, body in changed.items():
        profiles[name]['finished'] = save(name, 'timber', body)
    for name, body in added_angles.items():
        save(name, 'angle', body)
    for name, body in hardware_parts.items():
        save(name, 'bolt', body)
    for path, digest in pins.items():
        require(sha(path) == digest, 'source changed during build: '+path)
    result = {'schema': 'eoere_single_leg_header_geometry/v1', 'revision': REVISION,
        'parent_geometry': index['geometry'], 'frozen_parent_index': {'path': str(out/'parent-index.json'), 'sha256': sha(out/'parent-index.json')},
        'source_sha256': pins, 'axes': list(axes.values()), 'removed_axes': inputs['remove_leg_axis_ids'],
        'screw_axes': [r['source_screw_descriptor'] for r in old['hillman_rows']],
        'fitting_poses': poses, 'new_header_angles': inputs['new_header_angles'],
        'profiles': profiles, 'changed_finished_solids': saved, 'restorations': restores,
        'selected_stack_overrides': choices, 'current_angle_count': 24, 'current_bolt_count': 96,
        'current_Hillman_count': 66, 'plywood_leaf_count': 2, 'post_row_Z_mm': inputs['existing_lower_cleat_post_row_Z_mm'],
        'checks_pending': ['complete occupied geometry/access', 'fresh conditional forces', 'current connection/member resistances'],
        'release': copy.deepcopy(parent['release']), 'geometry_adopted': False,
        'new_response_computed': False, 'complete_joint_qualified': False, 'actual_observations': None}
    (out/'geometry.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    (out/'hardware-selection.csv').write_bytes(csv_bytes(choices))
    print(json.dumps({'result': str(out/'geometry.json'), 'sha256': sha(out/'geometry.json'),
        'angles': 24, 'bolts': 96, 'changed_members': len(changed), 'changed_stacks': len(choices)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.out.resolve())
