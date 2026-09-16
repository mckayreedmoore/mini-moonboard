"""Read saved flush-candidate evidence; report dimensional budgets, not tolerances.

Run with ``python3 scripts/floor_flush_fabrication_review.py``. No CAD or solver
dependencies are needed. Catalog bounds reproduce the cited local assessments;
they are not delivered-hardware measurements or current supplier verification.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = (
    'docs/floor-flush-geometry.json',
    'docs/floor-flush-a12-left-assessment.json',
    'docs/floor-flush-construction/connection-axes.csv',
    'docs/compact-half-inch-hardware.md',
    'docs/clear-space-hardware.md',
    'docs/floor-runner-recess-hardware.md',
)


def spacing_budget(spacing, diameter, drill_radius):
    """Two independent positional-error disks can approach by twice their radius."""
    if not all(math.isfinite(v) for v in (spacing, diameter, drill_radius)) or (
            spacing <= 0 or diameter <= 0 or drill_radius < 0):
        raise ValueError('Require finite positive spacing/diameter and nonnegative error')
    margin = spacing - 4 * diameter
    return {'nominal_spacing_mm': spacing, 'adopted_4D_mm': 4 * diameter,
            'nominal_margin_mm': margin,
            'independent_error_radius_limit_for_spacing_only_mm': margin / 2,
            'margin_at_recorded_drill_radius_mm': margin - 2 * drill_radius}


def build(root=ROOT):
    geometry = json.loads((root / INPUTS[0]).read_text())
    assessment = json.loads((root / INPUTS[1]).read_text())
    candidate = 'compact-floor-flush-development'
    if geometry['candidate'] != candidate or assessment['candidate'] != candidate:
        raise ValueError('Require matching flush-candidate evidence')
    with (root / INPUTS[2]).open(newline='') as source:
        axes = {row['name']: row for row in csv.DictReader(source) if row['kind'] == 'bolt'}
    radius = geometry['placement_assumptions']['drill_position_radius_mm']
    groups = {}
    for name, group in assessment['joint_groups'].items():
        first, second = (axes[bolt] for bolt in group['bolt_names'])
        spacing = math.dist([float(first[f'start_{a}_mm']) for a in 'yz'],
                            [float(second[f'start_{a}_mm']) for a in 'yz'])
        diameter = float(first['modeled_diameter_mm'])
        if diameter != float(second['modeled_diameter_mm']):
            raise ValueError('Pair diameter mismatch')
        groups[name] = spacing_budget(spacing, diameter, radius)
    boundary = []
    for bolt, result in assessment['stage_one']['bolts'].items():
        for member, placement in result['placement'].items():
            for edge, margin in placement['margins_mm'].items():
                boundary.append({'bolt': bolt, 'member': member, 'edge': edge,
                                 'adjusted_margin_mm': margin})
    hardware = {}
    # Inches: length deduction, minimum thread length, washer min/max,
    # maximum nut height, maximum washer OD. Sources are included in INPUTS.
    for label, bolt, bounds in (
        ('upper', 'lumber_leg_bolt_left_1', (.18, 1.5, .086, .132, .448, 1.380)),
        ('front', 'rail_front_bolt_left_1', (.06, 1., .064, .104, .337, 1.030)),
        ('rear', 'rail_rear_bolt_left_1', (.10, 1., .064, .104, .337, 1.030)),
    ):
        deduction, thread, washer_min, washer_max, nut_max, od_max = (v * 25.4 for v in bounds)
        spec = geometry['hardware_by_name'][bolt]
        nut_member = axes[bolt]['second_member']
        nut_bearing = geometry['geometries_by_bolt_name'][bolt]['members'][nut_member]['bearing_length_mm']
        threshold = spec['grip_mm'] + washer_max - nut_bearing / 4
        nominal_thread_start = spec['length_mm'] - thread
        hardware[label] = {
            'nominal_grip_mm': spec['grip_mm'],
            'catalog_washer_thickness_range_mm': [washer_min, washer_max],
            'required_full_body_to_first_transition_mm': threshold,
            'shortest_bolt_minus_minimum_threads_mm': nominal_thread_start - deduction,
            'extra_thread_transition_budget_at_shortest_bolt_mm': nominal_thread_start - deduction - threshold,
            'tip_projection_at_shortest_bolt_thickest_washers_tallest_nut_mm':
                spec['length_mm'] - deduction - spec['grip_mm'] - 2 * washer_max - nut_max,
            'nominal_thread_start_to_nut_seat_at_thinnest_washers_mm':
                spec['grip_mm'] + 2 * washer_min - nominal_thread_start,
            'catalog_max_washer_radius_increase_over_CAD_mm': (od_max - spec['washer_od_mm']) / 2,
        }
    return {
        'candidate': candidate,
        'status': 'DIMENSIONAL_REVIEW_ONLY_NOT_A_FABRICATION_RELEASE',
        'source_sha256': {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in INPUTS},
        'placement_assumptions': geometry['placement_assumptions'],
        'pair_spacing': groups,
        'pair_spacing_survives_recorded_independent_drill_errors': all(
            row['margin_at_recorded_drill_radius_mm'] >= -1e-9 for row in groups.values()),
        'tightest_saved_A12_directional_boundary': min(boundary, key=lambda row: row['adjusted_margin_mm']),
        'hardware_dimensional_budgets': hardware,
        'limits': [
            'Spacing uses the adopted 4D screen, not a new code applicability determination.',
            'Boundary result retains saved A12 load directions and existing inward-boundary allowance.',
            'Minimum catalog thread length does not guarantee minimum delivered full-body length.',
            'Washer radius changes need full-seat and nearby-opening checks; nominal fit does not certify them.',
            'No tolerance envelope, bore diameter, changed contact response or construction release is established.',
        ],
    }


if __name__ == '__main__':
    print(json.dumps(build(), indent=2, allow_nan=False))
