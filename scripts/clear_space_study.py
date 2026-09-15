"""Run or geometrically audit a separate clear-space support candidate."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path

from scripts.compact_rail_study import bolt_properties

MODELS = {'floor': 'compact_floor_rail_frame', 'exterior': 'compact_exterior_brace_frame',
          'floortaper': 'compact_floor_taper_frame',
          'floor2x4': 'compact_floor_rail_2x4_frame', 'floorrecess': 'compact_floor_recess_frame'}


def geometry(model):
    from scripts.compact_thick_geometry import build

    result = build(model)
    if model.KEY == 'compact-floor-taper-development':
        taper = model.floor_recess_geometry()
        result['floor_taper_geometry'] = taper
        for name, record in taper.items():
            result['members'][name]['floor_taper_geometry'] = record
    result['hardware_by_name'] = {c.name:model.bolt_dimensions(c) for c in model.connections() if c.kind == 'bolt'}
    reference = json.loads(Path('fea/results/compact-splice-study/a12-rear/geometry.json').read_text())
    bounds = reference['hardware_resistance_bounds_by_name']
    half = next(bounds[n] for n in bounds if n.startswith('lumber_leg_bolt_'))
    three_eighths = next(bounds[n] for n in bounds if n.startswith('knee_bolt_'))
    result['hardware_resistance_bounds_by_name'] = {}
    for name, row in result['geometries_by_bolt_name'].items():
        row['bending_yield_psi'] = 90000.
        if row['diameter_mm'] < 7.:
            path = Path('docs/floor-rail-2x4-hardware-reference.json')
            result['hardware_resistance_bounds_by_name'][name] = json.loads(path.read_text())['washer_resistance_bounds']
            result['source_sha256'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            result['hardware_resistance_bounds_by_name'][name] = half if row['diameter_mm'] > 10 else three_eighths
    if (model.KEY == 'compact-exterior-brace-development' and
            model.parameters.get('upper_joint_revision') == '64mm-24mm-tail-thick-round-washers'):
        result['upper_joint_revision'] = model.parameters['upper_joint_revision']
        for name, bounds in result['hardware_resistance_bounds_by_name'].items():
            if name.startswith('lumber_leg_bolt_'):
                result['hardware_resistance_bounds_by_name'][name] = dict(bounds,
                    washer_thickness_mm=model.UPPER_WASHER_MINIMUM_THICKNESS_MM,
                    procurement_condition='Minimum delivered thickness 3.0 mm; nominal CAD 3.175 mm. Retain existing conservative washer OD/hole and 33 ksi steel basis.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', choices=MODELS)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--geometry', action='store_true')
    parser.add_argument('--hold', default='A12')
    parser.add_argument('--horizontal', type=float, nargs=2, default=(0., 300.))
    parser.add_argument('--contact-seed', type=Path)
    parser.add_argument('--floor-grid', type=int, nargs=2)
    args = parser.parse_args()
    model = importlib.import_module('mini_moonboard.'+MODELS[args.candidate])
    if not args.geometry and args.candidate == 'floortaper':
        parser.error('Tapered legs require scripts.clear_space_batch floortaper --friction-mu .4 with actual taper geometry')
    if not args.geometry and getattr(model, 'RECESS_NATIVE_GEOMETRY_REQUIRED', False):
        parser.error('Recessed legs require scripts.clear_space_batch floorrecess --friction-mu .4 with actual recess geometry')
    if args.geometry:
        result = geometry(model)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        print('Receiver fit:', result['receiver_fit_pass'], flush=True)
    else:
        from fea.current_response_run import run

        if args.floor_grid:
            if not args.candidate.startswith('floor'):
                parser.error('--floor-grid requires floor candidate')
            model.FLOOR_RAIL_GRID = tuple(args.floor_grid)
        by_name = {c.name:bolt_properties(c) for c in model.connections() if c.kind == 'bolt'}
        contacts = [{**row, 'stiffness_n_per_mm':100.*row['tributary_area_mm2']}
                    for row in model.overlap_contact_datums()]
        seeded = {}
        if args.contact_seed:
            seed = json.loads(args.contact_seed.read_text())
            if seed.get('candidate') != model.KEY or seed.get('numerically_accepted') is not True:
                raise ValueError('Contact seed must be an accepted result of this candidate')
            seeded['initial_contact_names'] = [row['name'] for row in seed['bearings'] if row['active']]
        result = run(args.output, module=model, expected_candidate=model.KEY,
            bolt_stiffness={**next(iter(by_name.values())), 'by_name':by_name}, member_contacts=contacts,
            hold=args.hold, pounds=250., horizontal_force=tuple(args.horizontal),
            leg_floor_grid=3, patch_size=20., **seeded)
        print({k:result.get(k) for k in ('candidate', 'numerically_accepted',
            'maximum_timber_displacement_mm', 'termination')}, flush=True)
