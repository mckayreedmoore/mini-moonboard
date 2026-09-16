"""Recheck selected floor-runner shop geometry; not a fabrication release."""
import csv
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as model
from mini_moonboard.connection_geometry import material_intervals

ROOT = Path(__file__).resolve().parents[1]
HILLMAN_LENGTH_MM = 63.5
PANEL_THICKNESS_MM = 18.25625


def front_fixture_budget():
    """Conservative finished-hole pitch and independent axial/perpendicular offsets."""
    nominal_pitch, minimum_pitch, maximum_pitch = 39.5, 39., 40.
    midpoint_registration, perpendicular_error = .5, .5
    maximum_axis_error = math.hypot(midpoint_registration +
                                    (maximum_pitch-nominal_pitch)/2,
                                    perpendicular_error)
    return {
        'nominal_pitch_mm': nominal_pitch,
        'finished_pitch_range_mm': [minimum_pitch, maximum_pitch],
        'minimum_4D_margin_mm': minimum_pitch - 4*9.525,
        'maximum_midpoint_registration_mm': midpoint_registration,
        'maximum_perpendicular_error_per_hole_mm': perpendicular_error,
        'maximum_axis_error_mm': maximum_axis_error,
        'within_recorded_1mm_position_allowance': maximum_axis_error <= 1.,
    }


def build():
    geometry = json.loads((ROOT / 'docs/floor-flush-geometry.json').read_text())
    if geometry['candidate'] != model.KEY or not geometry['receiver_fit_pass']:
        raise ValueError('Selected floor-flush nominal receivers differ')
    connections = model.connections()
    bolts = [row for row in connections if row.kind == 'bolt']
    if (len(bolts) != 12 or
            {name for row in bolts for name in row.members} !=
            {name for name in geometry['members'] if name.startswith(
                ('base_side_', 'lumber_leg_', 'base_post_outer_', 'base_floor_'))}):
        raise ValueError('Bolt/receiver inventory differs')
    with (ROOT / 'docs/floor-flush-construction/bolt-member-datums.csv').open(
            newline='') as source:
        sheet_rows = list(csv.DictReader(source))
    if (len(sheet_rows) != 24 or
            {(row['connection'], row['member']) for row in sheet_rows} !=
            {(bolt.name, receiver) for bolt in bolts for receiver in bolt.members}):
        raise ValueError('Left/right construction bolt datums differ')
    finished = {row.name: row.shape for row in model.parts()}
    washers = {}
    for bolt in bolts:
        components = bolt.components()
        catalog_od = 35.052 if bolt.diameter > 10 else 26.162
        for index, receiver in enumerate(bolt.members):
            washer = components[index+1]
            direction = bolt.direction if index == 0 else -bolt.direction
            thickness = washer.BoundingBox().xlen
            centre = washer.Center()
            outer = cq.Solid.makeCylinder(catalog_od/2, thickness,
                                          centre-direction*thickness/2, direction)
            inner = cq.Solid.makeCylinder(
                geometry['hardware_resistance_bounds_by_name'][bolt.name][
                    'washer_hole_diameter_mm']/2, thickness,
                centre-direction*thickness/2, direction)
            seat = outer.cut(inner).translate(direction*thickness)
            unsupported = max(0., seat.Volume()-seat.intersect(finished[receiver]).Volume())
            washers[f'{bolt.name}/{receiver}'] = unsupported
    if len(washers) != 24 or any(value >= .01 for value in washers.values()):
        raise ValueError('Maximum catalog outside-diameter washer seat lacks support')

    raw = {part.name: part.shape for part in model.uncut_wood_parts()}
    panel_screws = model.panel_connections()
    if len(panel_screws) != 66:
        raise ValueError('Hillman axis inventory differs')
    tip_reserves = {}
    for screw in panel_screws:
        intervals = material_intervals(raw[screw.members[1]], screw.start,
                                       screw.direction, 0., 200.)
        if (len(intervals) != 1 or
                not math.isclose(intervals[0][0], PANEL_THICKNESS_MM, abs_tol=1e-6) or
                intervals[0][1] <= HILLMAN_LENGTH_MM):
            raise ValueError('Hillman screw escapes its receiver: '+screw.name)
        tip_reserves[screw.name] = intervals[0][1]-HILLMAN_LENGTH_MM
    from fea.floor_flush_run import face_contacts
    contact_pairs = {tuple(sorted((row['first'], row['second'])))
                     for row in face_contacts()}
    expected = {tuple(sorted(pair)) for side in ('left', 'right') for pair in (
        (f'base_side_{side}', f'lumber_leg_{side}'),
        (f'base_post_outer_{side}', f'base_floor_{side}'),
        (f'lumber_leg_{side}', f'base_floor_{side}'))}
    fixture = front_fixture_budget()
    if contact_pairs != expected or fixture['minimum_4D_margin_mm'] < 0 or not fixture[
            'within_recorded_1mm_position_allowance']:
        raise ValueError('Contact inventory or fixture budget differs')
    return {
        'candidate': model.KEY,
        'bolt_count': len(bolts), 'receiver_seat_count': len(washers),
        'maximum_catalog_washer_unsupported_mm3': max(washers.values()),
        'panel_screw_count': len(tip_reserves),
        'minimum_hillman_tip_reserve_mm': min(tip_reserves.values()),
        'contact_interface_count': len(contact_pairs),
        'front_fixture': fixture,
        'qualified_for_design': False,
        'scope': ('Nominal CAD envelope and finished-hole fixture bounds only. '
                  'Actual bore concentricity, delivered hardware and stock inspection '
                  'remain required; no strength or fabrication release.'),
    }


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
