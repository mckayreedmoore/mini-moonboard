"""Optimistic force-only necessary conditions for independent current panels."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from fea.round_structural_head_reference import references as head_references
from fea.round_structural_screw_reference import LBF_N
from fea.round_structural_screw_reference import references as screw_references


def maximum_lateral(withdrawal_n, lateral_n, head_n):
    """Maximize V with (V²/Z+T²/W)/hypot(V,T)<=1 and 0<=T<=H.

    This algebraic envelope uses supplied references unchanged. It is not an
    allowable load, calibrated stiffness, or prediction of force distribution.
    """
    if not all(math.isfinite(v) and v > 0 for v in (withdrawal_n, lateral_n, head_n)):
        raise ValueError('Require finite positive references')
    w, z = withdrawal_n, lateral_n
    optimum = w/2*math.sqrt((w-2*z)/(w-z)) if w > 2*z else 0.
    t = min(head_n, optimum)
    v2 = (z*z-2*z*t*t/w+z*math.sqrt(z*z+4*t*t*(1-z/w)))/2
    return {'maximum_lateral_n': math.sqrt(v2), 'tension_at_maximum_n': t,
            'maximum_tension_n': min(w, head_n)}


def necessary_force_check(count, downward_n, *, angle_from_vertical_deg,
                          withdrawal_n, lateral_n, head_n, panel_dead_n=0.):
    """Downward-only single-panel wrench; no edge bearing or backing friction."""
    if (not isinstance(count, int) or isinstance(count, bool) or count <= 0
            or not all(math.isfinite(v) and v >= 0 for v in (downward_n, panel_dead_n))
            or not math.isfinite(angle_from_vertical_deg)
            or not 0 <= angle_from_vertical_deg <= 90):
        raise ValueError('Require positive count, nonnegative loads and angle in [0,90]')
    cap = maximum_lateral(withdrawal_n, lateral_n, head_n)
    angle = math.radians(angle_from_vertical_deg)
    tangent = (downward_n+panel_dead_n)*math.cos(angle)
    outward = (downward_n+panel_dead_n)*math.sin(angle)
    lateral_sum = count*cap['maximum_lateral_n']
    tensile_sum = count*cap['maximum_tension_n']
    reasons = []
    if tangent > lateral_sum+1e-8:
        reasons.append('tangential_force_exceeds_sum_of_individual_maxima')
    if outward > tensile_sum+1e-8:
        reasons.append('outward_force_exceeds_sum_of_individual_maxima')
    return {'screw_count': count, 'downward_live_n': downward_n,
            'panel_dead_n': panel_dead_n, 'angle_from_vertical_deg': angle_from_vertical_deg,
            'required_tangential_n': tangent, 'required_outward_n': outward,
            'optimistic_lateral_sum_n': lateral_sum, 'optimistic_tensile_sum_n': tensile_sum,
            'conditional_force_equilibrium_impossible': bool(reasons), 'failure_reasons': reasons,
            'qualified_for_design': False}


def report():
    from mini_moonboard import panel_grid_v2 as grid
    from mini_moonboard import round_structural_frame as model

    screw, head = screw_references(), head_references()
    caps = {'withdrawal_n': screw['reference_withdrawal_n'],
            'lateral_n': screw['reference_lateral_n'], 'head_n': head['reference_head_n']}
    counts = Counter(row['panel'] for row in model.attachment_datums())
    expected = {f'main_{band}_{side}': 12 for band in ('lower', 'upper') for side in ('left', 'right')}
    expected.update({f'kicker_{side}': 4 for side in ('left', 'right')})
    if counts != expected or model.b.ANGLE_FROM_VERTICAL_DEG != 40:
        raise ValueError('Reassess changed panel count or slope')
    holds = {panel: [] for panel in counts}
    for label, (x, s) in grid.main_tnut_datums().items():
        side = 'left' if x < model.b.HALF else 'right'
        band = 'lower' if s < model.b.HALF else 'upper'
        holds[f'main_{band}_{side}'].append({'hold': label, 'x_mm': x-model.b.HALF, 's_mm': s})
    for label, (x, s) in grid.kicker_foothold_datums().items():
        side = 'left' if x < model.b.HALF else 'right'
        holds[f'kicker_{side}'].append({'hold': 'kicker_'+label, 'x_mm': x-model.b.HALF,
                                      'z_mm': model.b.V1_KICKER_HEIGHT_MM+s})
    loads = [('diagnostic_1200N', 1200.)]+[(f'{lb}lb_x{factor}', lb*factor*LBF_N)
                                            for lb in (250, 300) for factor in (1, 2)]
    rows = [{'panel': panel, 'case': label, **necessary_force_check(count, load,
             angle_from_vertical_deg=40. if panel.startswith('main_') else 0., **caps)}
            for panel, count in sorted(counts.items()) for label, load in loads]
    source_hashes = {**screw['source_sha256'], **head['source_sha256']}
    for path in ('fea/round_structural_panel_equilibrium.py', 'mini_moonboard/panel_grid.py',
                 'mini_moonboard/panel_grid_v2.py', 'mini_moonboard/box_frame.py',
                 'fea/round_service_floor.py'):
        source_hashes[path] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return {'candidate': model.KEY, 'qualified_for_design': False,
            'installation_adjustments_applied': False, 'moments_evaluated': False,
            'actual_force_distribution_evaluated': False, 'references_n': caps,
            'individual_envelope': maximum_lateral(**caps),
            'holds_by_panel': holds, 'cases': rows, 'source_sha256': source_hashes,
            'sources': screw['sources'],
            'limits': 'Necessary force-only screen with unadjusted conditional references. '
                     'Each case places the entire specified downward load on one independent panel. '
                     'No equal sharing, seam transfer, backing friction, kicker floor-edge bearing '
                     'or other tangential edge bearing is credited. Normal compression-only backing '
                     'contact may exist but cannot reduce required net screw tension. Ignoring panel '
                     'dead weight is optimistic for these downward-only loads; adding nonnegative '
                     'panel dead weight increases both projected demands. Hardware/hold mass omitted. '
                     'No load standoff, hold torque, panel bending, stiffness, moment equilibrium, '
                     'steel interaction, timber splitting or group reductions evaluated. Passing '
                     'these independent component bounds is not a feasible reaction witness. '
                     'Failure applies only to the stated references and support assumptions; '
                     'floor-edge support or changed applicable adjustments requires reassessment. '
                     '1200N is a diagnostic, not an adopted acceptance criterion. 250/300lb x1/x2 '
                     'are inherited sensitivity cases, not a climbing rating.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(report(), stream, indent=2, allow_nan=False)
        stream.write('\n')
