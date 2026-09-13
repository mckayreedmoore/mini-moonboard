"""Bounded side-rail load-path screen; no assembled triangle or release claim."""

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from fea.current_leg_revision_screen import LEG, capacity
from fea.dowel_yield import single_shear


def rear_horizontal_reference():
    """Single smooth 3/8-inch bolt, horizontal rail and actual leg grain."""
    d = .375
    force = np.array([0., 1., 0.])
    bearing = []
    for grain in (force, LEG):
        cosine2 = float(force @ grain)**2
        perpendicular = 6100*.5**1.45/math.sqrt(d)
        bearing.append(5600*perpendicular /
                       (5600*(1-cosine2)+perpendicular*cosine2)*d)
    reference = single_shear(main_length_in=1.5, side_length_in=1.5,
        main_bearing_lb_in=bearing[0], side_bearing_lb_in=bearing[1],
        main_yield_moment_lb_in=45000*d**3/6, side_yield_moment_lb_in=45000*d**3/6,
        gap_in=0., reduction_terms={'Im':5., 'Is':5., 'II':4.5, 'IIIm':4., 'IIIs':4., 'IV':4.})
    return reference['reference_lateral_lbf']*4.4482216152605


DEFAULT_SOURCE = Path(__file__).resolve().parent/'results/thick-leg-study/triangle-input.json'


def build(source=DEFAULT_SOURCE):
    """Estimate required couple transfer and reject the proposed ML24 receiver fit."""
    report = json.loads(source.read_text())
    if report.get('numerically_accepted') is not True:
        raise ValueError('Require accepted current native evidence')
    rows = [v for k, v in report['physical_connection_forces'].items()
            if k.startswith('lumber_leg_bolt_left_')]
    if len(rows) != 4 or any(r['second'] != 'lumber_leg_left' for r in rows):
        raise ValueError('Require the four-bolt baseline leg connection')
    points = np.array([r['point'] for r in rows])
    offsets = points-points.mean(axis=0)
    forces = np.array([r['force_on_second_xyz_n'] for r in rows])
    force = forces.sum(axis=0)
    moment = np.cross(offsets, forces).sum(axis=0)[0]/1000
    polar = np.sum(offsets[:, 1:]**2)

    def ratio(magnitude):
        distributed = np.broadcast_to(force/4, (4, 3)).copy()
        signed = np.sign(moment)*magnitude*1000
        distributed[:, 1] -= signed*offsets[:, 2]/polar
        distributed[:, 2] += signed*offsets[:, 1]/polar
        return float(np.max(np.linalg.norm(distributed[:, 1:], axis=1)
                            / capacity(distributed, .375)))

    low, high = 0., abs(moment)
    if ratio(0) > 1:
        raise ValueError('Direct force alone exceeds the conditional reference')
    for _ in range(64):
        trial = (low+high)/2
        if ratio(trial) <= 1:
            low = trial
        else:
            high = trial
    relief = abs(moment)-low
    rear_single_reference = rear_horizontal_reference()
    ml = json.loads((Path(__file__).resolve().parents[1]/'docs/ml24z-reference.json').read_text())['ml24z_nominal_mm']
    return {
        'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'baseline_moment_nm': moment, 'baseline_force_xyz_n': force.tolist(),
        'conditional_upper_smooth_bolt_moment_limit_nm': low,
        'fixed_resultant_required_moment_relief_nm': relief,
        'rail_cases': [
            {'joint_height_mm': z, 'required_horizontal_transfer_n': relief*1000/z,
             'four_rear_bolt_comparison_reference_n': rear_single_reference*4,
             'transfer_over_comparison_reference': relief*1000/z/(rear_single_reference*4)}
            for z in (69.85, 169.05)],
        'ml24_front_fit': {
            'receiver_thickness_mm': 38.1,
            'top_bottom_screw_row_span_mm': max(ml['width_stations'])-min(ml['width_stations']),
            'side_orientation_max_flange_hole_offset_mm': max(ml['front_flange_offsets']),
            'top_bottom_row_fits': False, 'side_flange_all_holes_fit': False},
        'lsta12_front_alternative': {
            'envelope_y_mm': [-188.4, 116.4], 'length_mm': 304.8,
            'width_mm': 31.75, 'center_z_mm': 169.05,
            'fasteners': '10 SD9112; five in each member',
            'source': 'https://icc-es.org/wp-content/uploads/report-directory/ESR-3096.pdf',
            'table': 26, 'published_tension_lbf_at_cd_1_6': 1235,
            'normal_duration_resistance_qualified': False,
            'limitation': 'Table note explicitly excludes other load durations; no CD=1 qualification by division.'},
        'decision': 'Reject ML24 front placement. LSTA12 is a plausible geometry alternative with unresolved normal-duration resistance.',
        'limits': [
            'Required rail force holds baseline upper resultant and contact lever geometry fixed; it is not a prediction.',
            'Upper comparison assumes smooth 3/8-inch shanks, equal elastic bolts and no out-of-plane demand.',
            'Rear comparison assumes equal pure-horizontal fastener force; excludes group moments, axial demand and local wood modes.',
            'Rail stiffness can redistribute forces; current no-slip supports already prevent simple foot spreading.',
            'This rejects the specified receivers and ML24 placement, not every triangular side frame.']}


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
