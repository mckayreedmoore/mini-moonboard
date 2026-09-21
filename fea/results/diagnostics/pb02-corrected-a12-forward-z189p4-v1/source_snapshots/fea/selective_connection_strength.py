"""Current selective-frame connection geometry and conditional resistance ledger."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea.lumber_leg_resistance import bolt_reference
from mini_moonboard import selective_2x6_frame as model
from mini_moonboard.connection_geometry import material_intervals

REFERENCE = Path('docs/selective-connection-reference.json')


def receiver_axes(name):
    """Explicit grain assignments for solid members; never infer from box size."""
    slope = (model.b.point(0, 1, 0)-model.b.point(0, 0, 0)).normalized()
    if name.startswith(('base_side_', 'base_principal_')):
        return slope, cq.Vector(1, 0, 0)
    if name.startswith('base_rail_'):
        return cq.Vector(1, 0, 0), slope
    if name.startswith('base_post_'):
        return cq.Vector(0, 0, 1), cq.Vector(1, 0, 0)
    if name == 'base_header':
        return cq.Vector(1, 0, 0), cq.Vector(0, 1, 0)
    raise ValueError(f'Unassigned receiver grain: {name}')


def boundary_distances(shape, point, axis):
    """Outer cut boundaries at the actual entry section, including bevels.

    Internal service gaps are recorded separately; they are not automatically
    classified as stock ends under the manufacturer's end-distance table.
    """
    runs = material_intervals(shape, point, axis, -5000., 5000.)
    if not runs or not any(a < 0 < z for a, z in runs):
        raise ValueError('Screw entry section is not inside receiver material')
    return [-runs[0][0], runs[-1][1]], runs


def spacing_checks(screws, distances):
    """Actual same-receiver pairs; no reduced stagger-spacing credit."""
    result = []
    for a, z in combinations(screws, 2):
        if a.members[1] != z.members[1]:
            continue
        grain, across = receiver_axes(a.members[1])
        delta = z.start-a.start
        parallel, perpendicular = abs(delta.dot(grain)), abs(delta.dot(across))
        if perpendicular < 1e-5:
            rule, measured = 'same_row_parallel', parallel
        elif parallel < 1e-5:
            rule, measured = 'same_row_perpendicular', perpendicular
        else:
            rule, measured = 'rows_inline', perpendicular
        result.append({'connections': [a.name, z.name], 'receiver': a.members[1],
                       'parallel_mm': parallel, 'perpendicular_mm': perpendicular,
                       'rule': rule, 'required_mm': distances[rule],
                       'passed': measured >= distances[rule]-1e-5})
    return result


def build():
    reference = json.loads(REFERENCE.read_text())
    distances = reference['spax']['table_19_mm']
    raw = {p.name: p for p in model.wood_parts()}
    screws = [c for c in model.connections() if isinstance(c, model.timber.PanelScrew)]
    if len(screws) != 56:
        raise ValueError('Expected all 56 current panel and kicker screws')
    rows, failures = [], []
    for c in screws:
        receiver = c.members[1]
        shape = raw[receiver].shape
        grain, across = receiver_axes(receiver)
        runs = material_intervals(shape, c.start, c.direction, 0., c.length)
        if len(runs) != 1:
            raise ValueError(f'Noncontinuous receiver engagement: {c.name}')
        entry = c.start+c.direction*(runs[0][0]+.001)
        ends, grain_runs = boundary_distances(shape, entry, grain)
        edges, edge_runs = boundary_distances(shape, entry, across)
        row = {'connection': c.name, 'receiver': receiver,
               'grain_xyz': list(grain.toTuple()), 'entry_section_offset_mm': .001,
               'end_distances_mm': ends, 'edge_distances_mm': edges,
               'gross_penetration_mm': runs[0][1]-runs[0][0],
               'entry_section_grain_material_runs_mm': grain_runs,
               'entry_section_cross_material_runs_mm': edge_runs,
               'passes_end_away_or_perpendicular': min(ends) >= distances['end_away_or_perpendicular']-1e-5,
               'passes_reversible_end': min(ends) >= distances['end_toward']-1e-5,
               'passes_edge': min(edges) >= distances['edge_any_direction']-1e-5}
        rows.append(row)
        for gate in ('passes_end_away_or_perpendicular', 'passes_reversible_end', 'passes_edge'):
            if not row[gate]:
                failures.append({'gate': gate, 'connection': c.name, 'receiver': receiver})
    spacing = spacing_checks(screws, distances)
    failures.extend({'gate': 'screw_spacing', **row} for row in spacing if not row['passed'])
    bolts = []
    for c in model.connections():
        if not c.name.startswith('lumber_leg_bolt_'):
            continue
        spans = [material_intervals(raw[n].shape, c.start, c.direction, 0., c.length) for n in c.members]
        if len(spans) != 2 or any(len(s) != 1 or abs(s[0][1]-s[0][0]-38.1) > 1e-5 for s in spans):
            raise ValueError('Conditional leg reference requires two continuous 38.1 mm members')
        bolts.append({'connection': c.name, 'members': list(c.members), 'raw_intervals_mm': spans})
    if len(bolts) != 8:
        raise ValueError('Expected eight current leg bolts')
    conditional = bolt_reference()
    basis = reference['leg_bolt']
    if (basis['effective_diameter_in'] != .298 or basis['bearing_psi_each_member'] != 3650
            or basis['bending_yield_psi_assumed'] != conditional['steel_Fyb_assumed_psi']):
        raise ValueError('Recorded reference differs from conditional bolt kernel inputs')
    kicker = next(c for c in screws if c.name == 'timber_kicker_right_0_2')
    sources = [Path(__file__).resolve(), REFERENCE.resolve(),
               *[Path(p).resolve() for p in ('fea/lumber_leg_resistance.py', 'fea/dowel_yield.py',
                                            'fea/leg_stock_screen.py', 'docs/ml24z-reference.json',
                                            'docs/panel-insert-reference.json', 'docs/selective-stock-reference.json')],
               *sorted(Path('mini_moonboard').resolve().glob('*.py'))]
    return {'candidate': model.KEY, 'qualified_for_design': False,
            'current_connection_demands_available': False, 'joint_strength_passed': False,
            'limits': 'Entry-section stock edge/end and screw spacing screen, not splitting or local service-pocket qualification. '
                      'Loads may reverse; the toward-end bound is screened at both ends. '
                      'No panel demand division by screw count, bracket capacity sum, group resistance or prior FE force transfer. '
                      'Commercial bracket mixed-axis classification and plywood/washer/bolt combined action remain open.',
            'reference': reference, 'panel_kicker_screws': rows, 'screw_spacing': spacing,
            'all_tested_product_geometry_gates_passed': not failures, 'failures': failures,
            'leg_bolt_stacks': bolts, 'conditional_leg_single_fastener_reference': conditional,
            'recommended_kicker_axis': {'connection': 'timber_kicker_right_0_2',
                'current_z_mm': kicker.start.z, 'preliminary_z_mm': 140.,
                'resulting_post_top_distance_mm': model.base.HEADER_BOTTOM-140.,
                'status': 'Recommendation only; fresh hardware, panel, repair-reserve and service collision checks required; no CAD changed'},
            'source_sha256': {str(p.relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(build(), stream, indent=2, allow_nan=False)
        stream.write('\n')
