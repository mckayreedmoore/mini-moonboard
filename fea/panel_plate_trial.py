"""Single-joint plate concept and placement screen; no installation approval."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard import angle_base_frame as model
from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard.raster import render

LEDGER = Path('fea/results/infill-connection-screen-v1.json')
WIDTH, HEIGHT, THICKNESS = 31.75, 50.8, 7.9375
LENGTH, THREAD, HEAD, MAJOR, HOLE = 88.9, 60.325, 9.906, 5.08, 5.8
PLY = 18.25625
LBF_N = .45359237*9.80665
REFERENCE = {
    'product': 'SPAX XFU10-3500 #10 x 3.5 in Unidrive flat head',
    'url': 'https://www.drjcertification.org/report/download/1936',
    'report': '2010-02, revised 2025-11-04; Tables 4, 10 and 19',
    'source_pdf_sha256': 'e989b7a89cfd6dce92c22bd88d79f0171382f605d5939940fedb62dd661fe8ed',
    'thread_including_tip_mm': THREAD, 'head_diameter_mm': HEAD,
    'major_diameter_mm': MAJOR, 'overall_length_mm': LENGTH,
    'withdrawal_lbf_per_in_DFL_SG050': 176.,
    'allowable_steel_tension_lbf': 690.,
    'minimum_edge_mm': 9.525, 'toward_end_distance_mm': 57.15,
    'conditions': 'Unadjusted conditional product references. Actual timber, installation, '
                  'custom steel seat, combined loading and cyclic response are unqualified.'}


def calculation(force):
    """Declared strip idealization and required material resistance, not capacity."""
    if not math.isfinite(force) or force < 0:
        raise ValueError('Require finite nonnegative tensile force')
    penetration = LENGTH-THICKNESS-PLY
    engaged = min(THREAD, penetration)
    withdrawal = engaged/25.4*176*LBF_N
    net_width = WIDTH-HEAD
    # Entire force at midspan of a strip supported at its two ends. Removing
    # the largest countersink diameter through all thickness is conservative
    # within this strip model; actual plywood contact/support is not proven.
    moment = force*HEIGHT/4
    stress = 6*moment/(net_width*THICKNESS**2)
    area = WIDTH*HEIGHT-math.pi*HEAD**2/4
    return {'force_n': force, 'gross_wood_penetration_mm': penetration,
            'embedded_thread_including_tip_mm': engaged,
            'conditional_withdrawal_reference_n': withdrawal,
            'withdrawal_reference_exceeded': force > withdrawal,
            'conditional_steel_tension_reference_n': 690*LBF_N,
            'steel_tension_reference_exceeded': force > 690*LBF_N,
            'strip_bending_stress_mpa': stress,
            'required_yield_mpa_at_assumed_1_67_divisor': 1.67*stress,
            'nominal_plate_contact_area_mm2': area,
            'average_plywood_contact_pressure_mpa': force/area,
            'qualification_passed': False}


def placements():
    """Screen all 119 interior locations; no old connection is silently changed."""
    origin = model.b.point(0., 0., 0.)
    tangent = (model.b.point(0., 1., 0.)-origin).normalized()
    service = [(x-model.b.HALF, s) for x, s in
               (*grid.main_tnut_datums().values(), *grid.main_led_datums().values())]
    rows = []
    for c in model.connections():
        if not (isinstance(c, model.timber.PanelScrew)
                and c.members[0].startswith('main_') and c.members[1].startswith('base_principal_')):
            continue
        s = (c.start-origin).dot(tangent)
        distance = min(math.hypot(max(abs(c.start.x-x)-WIDTH/2, 0.),
                                 max(abs(s-z)-HEIGHT/2, 0.)) for x, z in service)
        # Principal top is LENGTH-38.1. Its level bearing bottom is not S=0;
        # using actual raw vertices gives the extreme S range, not a universal
        # along-grain end-distance pass for a sloping cut.
        part = next(p for p in model.wood_parts() if p.name == c.members[1])
        stations = [(v.Center()-origin).dot(tangent) for v in part.shape.Vertices()]
        upper_distance = max(stations)-s
        low, high = (0., model.b.HALF) if '_lower_' in c.members[0] else (model.b.HALF, model.b.LENGTH)
        rows.append({'connection': c.name, 'panel': c.members[0], 'receiver': c.members[1],
                     'axis_x_s_mm': [c.start.x, s],
                     'plate_inside_panel_s_bounds': low <= s-HEIGHT/2 and s+HEIGHT/2 <= high,
                     'plate_to_extended_40mm_service_envelope_clearance_mm': distance-20.,
                     'nominal_receiver_side_edge_mm': 19.05,
                     'upper_end_axis_distance_mm': upper_distance,
                     'upper_toward_end_reference_passed': upper_distance >= 57.15,
                     'full_lower_end_and_split_resistance_checked': False,
                     'installed_or_qualified': False})
    if len(rows) != 119:
        raise ValueError('Unexpected interior attachment inventory')
    return rows


def deeper_fit(rows):
    """Check extended shafts against current retained hardware and raw receivers."""
    connections = {c.name: c for c in model.connections()}
    replaced = {r['connection'] for r in rows}
    retained = [(c.name, shape) for c in connections.values() if c.name not in replaced
                for shape in c.components()]
    retained += [(p.name, p.shape) for p in model.hardware.clip_parts(model.stations())]
    retained = [(name, shape, shape.BoundingBox()) for name, shape in retained]
    raw = {p.name: p.shape for p in model.wood_parts()}
    failures = []
    for row in rows:
        c = connections[row['connection']]
        shaft = cq.Solid.makeCylinder(MAJOR/2, LENGTH, c.start-c.direction*THICKNESS, c.direction)
        aa = shaft.BoundingBox()
        collided = sorted({name for name, shape, bb in retained if
            all(getattr(aa, a+'max') > getattr(bb, a+'min') and
                getattr(bb, a+'max') > getattr(aa, a+'min') for a in 'xyz')
            and shaft.intersect(shape).Volume() > .01})
        inside = cq.Solid.makeCylinder(MAJOR/2, LENGTH-THICKNESS-PLY,
                                      c.start+c.direction*PLY, c.direction)
        missing = inside.cut(raw[c.members[1]]).Volume()
        if collided or missing > .01:
            failures.append({'connection': c.name, 'retained_hardware_collisions': collided,
                             'missing_raw_receiver_volume_mm3': missing})
    return {'checked_extended_shaft_count': len(rows), 'failures': failures,
            'scope': 'Nominal major-diameter extended shafts against retained fasteners/brackets and '
                     'solid receiver coverage. Front plates, actual threads, driver/hold bodies and '
                     'installation sequence still require full assembly checks.',
            'complete_replacement_fit_qualified': False}


def build(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Refusing to overwrite a trial')
    own_source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    ledger_bytes = LEDGER.read_bytes()
    ledger = json.loads(ledger_bytes)
    for name, sha in ledger['source_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != sha:
            raise ValueError('Panel ledger source changed: '+name)
    peak = ledger['maximum_ideal_tension']
    rows = placements()
    depth_fit = deeper_fit(rows)
    location = next(r for r in rows if r['connection'] == peak['connection'])
    force_cases = {label: calculation(peak[key]) for label, key in (
        ('250lb_normal_only', 'ideal_tension_250lb_n'), ('300lb_normal_only', 'ideal_tension_300lb_n'))}
    # Local joint coordinates: X across receiver, Y uphill, Z into the frame.
    # No countersink is removed from the plywood. Front steel remains proud.
    panel = cq.Solid.makeBox(100., 120., PLY, cq.Vector(-50., -60., 0.))
    receiver = cq.Solid.makeBox(38.1, 120., 139.7, cq.Vector(-19.05, -60., PLY))
    plate = cq.Solid.makeBox(WIDTH, HEIGHT, THICKNESS,
                            cq.Vector(-WIDTH/2, -HEIGHT/2, -THICKNESS))
    axis = cq.Vector(0., 0., 1.)
    start = cq.Vector(0., 0., -THICKNESS)
    shank = cq.Solid.makeCylinder(MAJOR/2, LENGTH, start, axis)
    cone_depth = (HEAD-HOLE)/2  # Explicit 90-degree placeholder, not a vendor drawing.
    seat = cq.Solid.makeCone(HEAD/2, HOLE/2, cone_depth, start, axis)
    plate = plate.cut(cq.Solid.makeCylinder(HOLE/2, THICKNESS, start, axis)).cut(seat)
    head = cq.Solid.makeCone(HEAD/2, MAJOR/2, (HEAD-MAJOR)/2, start, axis)
    screw = shank.fuse(head)
    # Occupancy envelopes only, not pilot or drilling instructions.
    panel = panel.cut(shank)
    receiver = receiver.cut(shank)
    bodies = {'panel_cutout': panel, 'principal_cutout': receiver,
              'trial_front_plate': plate, 'trial_screw_envelope': screw}
    if not all(s.isValid() and len(s.Solids()) == 1 for s in bodies.values()):
        raise ValueError('Invalid single-joint trial body')
    # Countersink root blends into the cylindrical hole; the screw envelope
    # must not penetrate the steel despite the assumed seat profile.
    intersection = plate.intersect(screw).Volume()
    if intersection > .01:
        raise ValueError('Screw envelope collides with trial plate')
    output.mkdir(parents=True)
    assembly = cq.Assembly(name='panel_plate_local_trial_not_for_construction')
    for name, shape in bodies.items():
        assembly.add(shape, name=name)
    from mini_moonboard.export import _export_step
    _export_step(assembly, output/'panel-plate-trial.step')
    # Cut half of the wood away for an explicit section view; steel and screw
    # are unmoved and the STEP retains all four full local bodies.
    half = cq.Solid.makeBox(50., 120., 200., cq.Vector(-50., -60., -10.))
    render([(panel.cut(half), (190, 157, 107)), (receiver.cut(half), (157, 90, 36)),
            (plate, (154, 165, 177)), (screw, (41, 182, 214))], output/'section.png')
    for name, sha in ledger['source_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != sha:
            raise ValueError('Panel ledger source changed during trial: '+name)
    if LEDGER.read_bytes() != ledger_bytes:
        raise ValueError('Panel ledger changed during trial')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != own_source_sha:
        raise ValueError('Trial source changed during build')
    report = {'candidate': 'single-joint-panel-plate-trial', 'parent': model.KEY,
              'qualified_for_design': False, 'installed_in_current_frame': False,
              'complete_frame_reanalysis_run': False, 'actual_connection_demands_available': False,
              'reference': REFERENCE, 'plate_dimensions_mm': [WIDTH, HEIGHT, THICKNESS],
              'plate_hole_mm': HOLE, 'assumed_countersink_included_angle_deg': 90.,
              'selected_source_location': location, 'diagnostic_force_cases': force_cases,
              'placements': rows, 'extended_shaft_fit': depth_fit,
              'upper_end_reference_failures': [r['connection'] for r in rows
                  if not r['upper_toward_end_reference_passed']],
              'front_service_envelope_failures': [r['connection'] for r in rows
                  if r['plate_to_extended_40mm_service_envelope_clearance_mm'] < 0.],
              'plate_crosses_panel_edge': [r['connection'] for r in rows
                  if not r['plate_inside_panel_s_bounds']],
              'plate_screw_collision_volume_mm3': intersection,
              'limits': 'Single-joint hypothesis, not a new full-frame schedule. Existing ideal point-restraint '
                        'panel reactions are diagnostic only, not the redistributed forces of a plated joint. '
                        'Steel grade/yield, actual countersink, plywood contact/bearing/punching, screw '
                        'combined action, timber splitting, lower end distances and actual hold/tool shapes '
                        'remain unqualified. No equal sharing, friction or stiffness benefit is credited. '
                        '40mm service circles are extended to the front for this placement screen; they '
                        'are not actual hold-body envelopes. Render hides half the local wood for inspection.',
              'source_sha256': {**ledger['source_sha256'], str(LEDGER): hashlib.sha256(ledger_bytes).hexdigest(),
                  'fea/panel_plate_trial.py': own_source_sha},
              'artifact_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}}
    (output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({k: result[k] for k in ('diagnostic_force_cases', 'upper_end_reference_failures',
                                            'front_service_envelope_failures', 'plate_crosses_panel_edge')}))
