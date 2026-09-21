"""Current CAD rigid-body load and overturning sensitivity; no strength rating."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from fea.horizontal_service_floor import floor_contact_bodies, select_floor_supports
from fea.round_insert_floor import current_mass
from fea.round_insert_floor import sources as mass_sources
from fea.round_structural_audit import sources as geometry_sources
from fea.split_center_floor import verify_loaded_sources
from fea.user_load_envelope import envelope, hull


def locations(model):
    """Use current panel thickness and kicker plane, not a historical wrapper."""
    grid = model.timber.grid
    points = [(label, model.b.point(x-model.b.HALF, s, -model.wide.PANEL).toTuple(),
               (-model.b.normal()).toTuple())
              for label, (x, s) in grid.main_tnut_datums().items()]
    points.extend(('kicker_'+label,
                   (x-model.b.HALF, model.base.HEADER_FRONT_Y+model.wide.PANEL,
                    model.b.V1_KICKER_HEIGHT_MM+s), (0., 1., 0.))
                  for label, (x, s) in grid.kicker_foothold_datums().items())
    if len(points) != 142 or len({p[0] for p in points}) != 142:
        raise ValueError('Require all 132 main and 10 kicker locations')
    return points


def sources():
    result = {**mass_sources(), **geometry_sources()}
    for path in (Path(__file__).resolve().relative_to(Path.cwd()), Path('uv.lock')):
        result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def build():
    from mini_moonboard import round_structural_frame as model

    before = sources()
    verify_loaded_sources(before)
    state, inventory = current_mass(model)
    contacts = floor_contact_bodies(model)
    supports = select_floor_supports(contacts)
    state['support_polygon_mm'] = hull([p[:2] for r in supports for p in r['vertices_mm']])
    points = locations(model)
    cases = envelope(state, points, weights=(250, 300))
    if before != sources():
        raise ValueError('Source changed during current global screen')
    verify_loaded_sources(before)
    return {
        'candidate': model.KEY, 'source_sha256': before,
        'state': state, 'mass_inventory': inventory,
        'selected_floor_support_bodies': supports,
        'load_locations': [{'name': name, 'face_point_xyz_mm': point,
                            'outward_xyz': outward} for name, point, outward in points],
        'cases': cases, 'summary': dict(Counter(c['status'] for c in cases)),
        'case_count': len(cases), 'hold_count': len(points),
        'qualified_for_design': False, 'internal_connection_demands_evaluated': False,
        'floor_qualification': False, 'physical_floor_tests_performed': False,
        'assumptions': [
            'One resultant at one hold at a time; every main and kicker hold considered.',
            ('250 lb intended maximum; 300 lb sensitivity only. Multipliers 1 and 2 are '
             'project comparisons, not a verified dynamic envelope or rating.'),
            ('Hold standoff 0/50/100 mm and horizontal force 0/300 N. Each support '
             'edge uses its exact worst horizontal azimuth, not a sampled direction.'),
            ('Current drilled wood/plywood density 600 kg/m3 and modeled steel 7850 kg/m3. '
            'Holds and electrical mass excluded. 80% mass at unchanged centroid is '
            'a sensitivity, not a measured lower bound.'),
            ('Level rigid support at four posts and two leg feet. No kicker-edge, '
             'pad, anchor or unspecified ballast support credit.'),
            ('Rigid-body edge moments only. No floor pressure, individual support '
            'reactions, yaw/friction feasibility, frame flexibility, internal member '
            'or connection demands, or structural approval.'),
            ('The 1.5 overturning factor is the retained CWA comparison; scope and '
             'full load combinations remain unestablished for this custom equipment.'),
            ('Top/side-edge use, simultaneous hand/foot couples and actual hold '
             'projection beyond the stated offsets are not covered.'),
        ],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite saved evidence')
    report = build()
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'mass_kg': report['state']['mass_kg'], 'summary': report['summary']}))
