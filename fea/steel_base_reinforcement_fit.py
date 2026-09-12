"""Bounded fabricated-shoe geometry audit; no calculated connection capacity."""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard import steel_base_reinforcement as model
from mini_moonboard.connection_geometry import material_intervals
from mini_moonboard.selected_hardware import BoltSpec


def overlap(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any(min(getattr(aa, q+'max'), getattr(bb, q+'max'))-
           max(getattr(aa, q+'min'), getattr(bb, q+'min')) <= 1.e-6 for q in 'xyz'):
        return 0.
    return a.intersect(b).Volume()


def hashes():
    from fea.round_structural_audit import sources

    result = sources()
    for p in ('mini_moonboard/steel_base_reinforcement.py', 'fea/steel_base_reinforcement_fit.py'):
        result[p] = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return result


def assess():
    before = hashes()
    parts = {p.name: p.shape for p in model.parts()}
    raw = {p.name: p.shape for p in (*model.wood_parts(), *model.steel_parts())}
    added = model.added_connections()
    added_names = {c.name for c in added}
    new_steel = {c.members[i] for c in added for i in (0, 2)}
    collisions = []
    for name in sorted(new_steel):
        for other, shape in parts.items():
            if other == name or (other in new_steel and other < name):
                continue
            volume = overlap(parts[name], shape)
            if volume > 1.e-4:
                collisions.append({'first': name, 'second': other, 'volume_mm3': volume})
    stacks = []
    tools = []
    components = [(c.name, i, shape) for c in model.connections()
                  for i, shape in enumerate(c.components())]
    for connection_name, index, shape in components:
        selected_parts = parts if connection_name in added_names else {
            name: parts[name] for name in new_steel}
        for name, body in selected_parts.items():
            volume = overlap(shape, body)
            if volume > 1.e-4:
                collisions.append({'first': connection_name, 'component': index,
                                   'second': name, 'volume_mm3': volume})
    # Component-to-component intersections between different fasteners.
    for i, (name, index, shape) in enumerate(components):
        for other, oi, body in components[i+1:]:
            if name == other or not ({name, other} & added_names):
                continue
            volume = overlap(shape, body)
            if volume > 1.e-4:
                collisions.append({'first': name, 'component': index,
                    'second': other, 'second_component': oi, 'volume_mm3': volume})
    spec = BoltSpec('provisional A307 family', model.BOLT_LENGTH, model.GRIP, 0.)
    for c in added:
        start = model.WASHER
        intervals = []
        for member, thickness in zip(c.members, (model.THICKNESS, 38.1,
                                   model.BEARING_PLATE_THICKNESS), strict=True):
            found = material_intervals(raw[member], c.start, c.direction, 0., c.length)
            expected = [(start, start+thickness)]
            good = len(found) == 1 and max(abs(found[0][j]-expected[0][j]) for j in (0, 1)) < 1.e-5
            intervals.append({'member': member, 'actual_mm': found,
                              'expected_mm': expected, 'passed': good})
            start += thickness
        protrusion = c.length-(2*model.WASHER+c.grip+spec.nut_height_max_mm)
        stacks.append({'connection': c.name, 'component_count': len(c.components()),
            'start_xyz_mm': c.start.toTuple(), 'direction': c.direction.toTuple(),
            'members': list(c.members), 'length_mm': c.length, 'grip_mm': c.grip,
            'material_intervals': intervals, 'nominal_thread_protrusion_mm': protrusion,
            'nut_fully_on_reference_thread': c.length-spec.thread_length_reference_mm <= 2*model.WASHER+c.grip,
            'passed': all(r['passed'] for r in intervals) and protrusion >= 2*spec.pitch_mm})
        for label, point, direction in (
            ('head', c.start-c.direction*spec.head_height_max_mm, -c.direction),
            ('nut', c.start+c.direction*(2*model.WASHER+c.grip+spec.nut_height_max_mm), c.direction)):
            tool = cq.Solid.makeCylinder(12.5, 50., point, direction)
            hits = [name for name, body in parts.items() if overlap(tool, body) > 1.e-4]
            hits += [other for other, _, body in components if other != c.name and overlap(tool, body) > 1.e-4]
            tools.append({'connection': c.name, 'end': label, 'hits': sorted(set(hits)),
                          'allowance_diameter_mm': 25., 'allowance_length_mm': 50.})
    trims = []
    baseline = {p.name: p.shape for p in model.previous.wood_parts()}
    for side in ('left', 'right'):
        name = 'base_side_'+side
        trims.append({'member': name, 'removed_wood_volume_mm3': baseline[name].Volume()-raw[name].Volume(),
                      'new_bearing_z_mm': raw[name].BoundingBox().zmin})
    drilled_receivers = dict(raw)
    for c in added:
        receiver = c.members[1]
        drilled_receivers[receiver] = drilled_receivers[receiver].cut(
            cq.Solid.makeCylinder(model.WOOD_HOLE_DIAMETER/2, c.length+2.,
                                 c.start-c.direction, c.direction)).clean()
    preserved_screw_intervals = []
    retained_names = {c.name for c in model.connections()}-added_names
    panel_names = {c.name for c in model.previous.panel_connections()}
    for c in model.previous.connections():
        if c.kind != 'screw' or c.name not in retained_names:
            continue
        receiver = c.members[1]
        if receiver not in ('base_side_left', 'base_side_right', 'base_header'):
            continue
        a = material_intervals(baseline[receiver], c.start, c.direction, 0., c.length+2.)
        b = material_intervals(drilled_receivers[receiver], c.start, c.direction, 0., c.length+2.)
        passed = len(a) == len(b) and all(abs(x-y) < 1.e-5 for aa, bb in zip(a, b, strict=True)
                                        for x, y in zip(aa, bb, strict=True))
        preserved_screw_intervals.append({'connection': c.name, 'before_mm': a, 'after_mm': b,
            'is_panel_screw': c.name in panel_names, 'passed': passed})
    if before != hashes():
        raise ValueError('Source changed during fabricated-shoe fit audit')
    return {'candidate': model.KEY, 'source_sha256': before,
        'added_bolts': len(added), 'retained_leg_bolts': sum(c.name.startswith('lumber_leg_bolt_') for c in model.connections()),
        'panel_screws': len(model.previous.panel_connections()), 'remaining_ml24z': len(model.stations()),
        'new_steel_body_count': len(new_steel), 'collisions': collisions,
        'bolt_stacks': stacks, 'tool_allowances': tools, 'rim_trims': trims,
        'preserved_retained_screw_receiver_intervals': preserved_screw_intervals,
        'preserved_panel_receiver_intervals': [r for r in preserved_screw_intervals if r['is_panel_screw']],
        'nominal_fit_passed': not collisions and all(r['passed'] for r in stacks)
            and all(not r['hits'] for r in tools) and all(r['passed'] for r in preserved_screw_intervals),
        'qualified_for_design': False, 'limits': [
            '25mm-diameter x50mm socket allowance is a project assumption, not a selected tool drawing.',
            'Includes existing hardware and occupied steel/wood cuts; source geometry remains nominal.',
            'Weld strength, plate bending/prying, bolt steel and wood connection resistance unresolved.',
            'Header pressure distribution, all receiver edge/end/group checks and signed current demand remain required.',
            'No clamp-friction, old ML24Z rating, or prior gusset resistance assigned.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = assess()
    with args.output.open('x') as f:
        f.write(json.dumps(result, indent=2)+'\n')
    print({k: result[k] for k in ('nominal_fit_passed', 'added_bolts', 'collisions')})
