"""Kicker pitch-equilibrium bounds with explicit bottom-edge bearing credit."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from scipy.optimize import linprog

from fea.round_structural_head_reference import references as head_references
from fea.round_structural_panel_equilibrium import maximum_lateral
from fea.round_structural_screw_reference import LBF_N
from fea.round_structural_screw_reference import references as screw_references

MASS = Path('fea/results/round-structural-global-envelope-v1.json')
GRAVITY = 9.80665


def pitch_screen(*, rows_mm, head_n, lateral_max_n, thickness_mm, downward_n,
                 standoff_mm, outward_n, load_height_mm, dead_n, dead_y_mm):
    """Necessary bound plus a restricted, conditional two-dimensional witness.

    The bound permits any vertical screw force within +/-Vmax and any shear
    reaction depth within the panel. Floor reaction is upward only, anywhere
    through thickness. Backing pushes outward at nonnegative height.
    """
    values = (*rows_mm, head_n, lateral_max_n, thickness_mm, downward_n,
              standoff_mm, outward_n, load_height_mm, dead_n, dead_y_mm)
    if (len(rows_mm) != 4 or len(set(rows_mm)) != 2
            or not all(math.isfinite(v) for v in values)
            or min(*rows_mm, head_n, lateral_max_n, thickness_mm) <= 0
            or min(downward_n, standoff_mm, load_height_mm, dead_n) < 0
            or not 0 <= dead_y_mm <= thickness_mm):
        raise ValueError('Require four two-row screws and finite physical loads/dimensions')
    lo, hi = sorted(set(rows_mm))
    lower_count, upper_count = rows_mm.count(lo), rows_mm.count(hi)
    # Subtract the MOST favorable possible floor moment, t*(D+d).
    q = (downward_n*standoff_mm+load_height_mm*outward_n
         -dead_n*(thickness_mm-dead_y_mm))
    shear_assistance = len(rows_mm)*thickness_mm*lateral_max_n
    tension_pitch = sum(rows_mm)*head_n
    required_top = max(0., (q-lower_count*lo*head_n-shear_assistance)/hi)
    impossible = q > tension_pitch+shear_assistance+1.e-8

    # A more restrictive witness: zero vertical screw shear, upward floor
    # resultant at mid-thickness, backing resultants at z=25 and 200 mm.
    # These are explicit locations, not a freely assigned reaction couple.
    floor = downward_n+dead_n
    floor_y = thickness_mm/2
    witness_q = (downward_n*(thickness_mm+standoff_mm)+outward_n*load_height_mm
                 +dead_n*dead_y_mm-floor*floor_y)
    result = linprog([1., 1., 0., 0.],
                     A_eq=[[1., 1., -1., -1.], [hi, lo, -25., -200.]],
                     b_eq=[outward_n, witness_q],
                     bounds=[(0., upper_count*head_n), (0., lower_count*head_n),
                             (0., None), (0., None)], method='highs')
    witness = None
    if result.success:
        upper, lower, b25, b200 = map(float, result.x)
        force_residual = upper+lower-b25-b200-outward_n
        moment_residual = hi*upper+lo*lower-25*b25-200*b200-witness_q
        if (abs(force_residual) > 1.e-6 or abs(moment_residual) > 1.e-4
                or min(upper, lower, b25, b200) < -1.e-8
                or upper > upper_count*head_n+1.e-6
                or lower > lower_count*head_n+1.e-6):
            raise ValueError('Invalid restricted pitch-equilibrium witness')
        witness = {'top_row_tension_sum_n': upper, 'bottom_row_tension_sum_n': lower,
                   'backing_force_at_z25_n': b25, 'backing_force_at_z200_n': b200,
                   'floor_upward_n': floor, 'floor_y_from_back_mm': floor_y,
                   'all_screw_vertical_forces_n': [0.]*4,
                   'force_residual_n': force_residual, 'pitch_residual_nmm': moment_residual}
    elif result.status != 2:
        raise ValueError('Pitch witness LP did not resolve: '+result.message)
    if impossible and witness is not None:
        raise ValueError('Pitch witness contradicts the necessary bound')
    return {'downward_live_n': downward_n, 'hold_standoff_mm': standoff_mm,
            'outward_live_n': outward_n, 'load_height_mm': load_height_mm,
            'panel_dead_n': dead_n, 'panel_dead_y_from_back_mm': dead_y_mm,
            'most_favorable_residual_pitch_nmm': q,
            'independent_tension_pitch_upper_nmm': tension_pitch,
            'independent_shear_couple_upper_nmm': shear_assistance,
            'required_top_row_tension_lower_bound_n': required_top,
            'top_row_reference_sum_n': upper_count*head_n,
            'conditional_pitch_equilibrium_impossible': impossible,
            'restricted_2d_witness': witness,
            'qualified_for_design': False}


def report():
    from mini_moonboard import round_structural_frame as model

    mass = json.loads(MASS.read_text())
    if mass['candidate'] != model.KEY:
        raise ValueError('Require current mass inventory')
    hashes = {**mass['source_sha256']}
    for path, sha in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha:
            raise ValueError('Stale mass geometry: '+path)
    screw, head = screw_references(), head_references()
    caps = {'withdrawal_n': screw['reference_withdrawal_n'],
            'lateral_n': screw['reference_lateral_n'], 'head_n': head['reference_head_n']}
    shear = maximum_lateral(**caps)['maximum_lateral_n']
    profiles = []
    for side in ('left', 'right'):
        name = 'kicker_'+side
        part = next(p for p in mass['mass_inventory'] if p['name'] == name)
        rows = sorted(r['s'] for r in model.attachment_datums() if r['panel'] == name)
        if rows != [60., 60., 140., 140.]:
            raise ValueError('Reassess altered kicker rows')
        profiles.append({'panel': name, 'screw_rows_z_mm': rows,
                         'dead_n': part['mass_kg']*GRAVITY,
                         'dead_y_mm': part['centre_xyz_mm'][1]-model.base.HEADER_FRONT_Y})
    if any(profiles[0][key] != profiles[1][key]
           for key in ('screw_rows_z_mm', 'dead_n', 'dead_y_mm')):
        raise ValueError('Cannot aggregate unequal kicker profiles')
    profile = profiles[0]
    cases = [{'case': label, **pitch_screen(rows_mm=profile['screw_rows_z_mm'],
              head_n=caps['head_n'], lateral_max_n=shear, thickness_mm=model.wide.PANEL,
              downward_n=down, standoff_mm=offset, outward_n=out,
              load_height_mm=model.b.V1_KICKER_HEIGHT_MM-75.,
              dead_n=profile['dead_n'], dead_y_mm=profile['dead_y_mm'])}
             for label, down in [('diagnostic_1200N', 1200.),
                                 *[(f'{lb}lb_x{factor}', lb*factor*LBF_N)
                                   for lb in (250, 300) for factor in (1, 2)]]
             for offset in (0., 50., 100.) for out in (-300., 0., 300.)]
    hashes.update(screw['source_sha256'])
    hashes.update(head['source_sha256'])
    for path in (MASS, Path(__file__).resolve().relative_to(Path.cwd()),
                 Path('fea/round_structural_panel_equilibrium.py')):
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    if any(hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha
           for path, sha in hashes.items()):
        raise ValueError('Source changed during kicker pitch calculation')
    return {'candidate': model.KEY, 'profiles': profiles, 'references_n': caps,
            'source_sha256': hashes, 'cases': cases,
            'summary': {'cases_per_kicker': len(cases),
                        'conditional_pitch_impossible': sum(c['conditional_pitch_equilibrium_impossible'] for c in cases),
                        'restricted_2d_witnesses': sum(c['restricted_2d_witness'] is not None for c in cases)},
            'qualified_for_design': False, 'actual_head_applicability_resolved': False,
            'edge_bearing_resistance_evaluated': False,
            'three_dimensional_equilibrium_evaluated': False,
            'limits': 'Conditional fixed-reference statics, not actual capacity or release. '
                      'Bottom-edge bearing credited only for this explicit comparison. '
                      'Dead weight uses current CAD at assumed600kg/m3 and its actual centroid. '
                      'Holds/hardware dead weight and dynamic validity not established. '
                      'Bound permits arbitrary shear depth and independently maximal shear/tension; '
                      'nonfailure is not a feasible force distribution. Restricted witnesses set '
                      'all vertical screw shear to zero and place floor reaction at mid-thickness. '
                      'No x-direction equilibrium, real contact patch/pressure, panel bending, '
                      'stiffness compatibility, installed head resistance or floor qualification. '
                      'Screws transfer point forces; no independent head/shank moment is credited.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = report()
    with args.output.open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(data['summary']))
