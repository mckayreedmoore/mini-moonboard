"""Finite conservative leg assessment, including the whole existing foot face.

A failed necessary check closes this assessment with a negative decision; it
neither predicts collapse nor qualifies the investigated hardware revision.
"""
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea.leg_attachment_check import BUNDLE, LEG, RIM, bolt_group
from fea.leg_member_capacity import leg_check
from fea.leg_only_load_check import MASS
from fea.leg_only_load_check import build as load_build
from fea.leg_smooth_bolt_check import moment_interval, smooth_bolt_group


def foot_joint_moment(*, compression_n, top, foot, leg_mass_kg, leg_centre):
    """Local sagittal equilibrium; compression delivered along the leg axis.

    Foot carries that force plus the leg's own weight. Retaining the latter
    separately adds a small conservative gravity allowance to the global model.
    No assumption of centered pressure or zero top-joint moment is made.
    """
    values = [compression_n, leg_mass_kg, *top, *foot, *leg_centre]
    if not all(math.isfinite(x) for x in values) or min(compression_n, leg_mass_kg) < 0:
        raise ValueError('Require finite geometry and nonnegative loads')
    weight = leg_mass_kg*9.80665
    fy, fz = compression_n*LEG[1], compression_n*LEG[2]+weight
    return ((foot[1]-top[1])*fz-(foot[2]-top[2])*fy
            -(leg_centre[1]-top[1])*weight)


def splitting_screen(bolt_forces, *, kmod=.8):
    """Supplemental EC5 solid-timber splitting check, separate from NDS ASD.

    Sum absolute cross-grain bolt components to avoid cancellation; amplify
    by 1.5 on top of the specified service comparison. Values in N and mm.
    """
    b, h, he = 38.1, 139.7, (139.7+57.3962318)/2
    perpendicular = (0., RIM[2], -RIM[1])
    demand = 1.5*sum(abs(sum(a*v for a, v in zip(force, perpendicular, strict=True)))
                     for force in bolt_forces)
    characteristic = 14*b*math.sqrt(he/(1-he/h))
    resistance = kmod*characteristic/1.3
    return {'factored_transverse_demand_n':demand, 'design_resistance_n':resistance,
            'ratio':demand/resistance, 'kmod':kmod, 'gamma_m':1.3,
            'scope':'Supplemental EC5 splitting screen; not an NDS tensile value'}


def build():
    # 25 kg equipment plus 2 kg reserved for the investigated hardware change.
    loads = load_build(equipment_mass_kg=27.)
    mass = json.loads(MASS.read_text())
    leg = next(p for p in mass['mass_inventory'] if p['name'] == 'lumber_leg_left')
    footprint = next(p['vertices_mm'] for p in mass['selected_floor_support_bodies']
                     if p['name'] == 'lumber_leg_left')
    with tarfile.open(BUNDLE, 'r:gz') as archive:
        native = json.load(archive.extractfile('report.json'))
    points = [native['physical_connection_forces'][f'lumber_leg_bolt_left_{i}']['point']
              for i in range(1, 5)]
    top = [sum(p[k] for p in points)/4 for k in range(3)]
    load_case = next(c for c in loads['cases']
                     if c['climber_lb'] == 250 and c['vertical_multiplier'] == 2)
    force = load_case['entire_rear_compression_assigned_to_one_leg_n']
    front_y = load_case['front_support_y_mm']
    centre = [sum(p[k] for p in footprint)/len(footprint) for k in range(3)]
    half_length = (max(p[1] for p in footprint)-min(p[1] for p in footprint))/2
    full_contact_points = [[centre[0],centre[1]+sign*half_length/3,0.] for sign in (-1,1)]
    rows = []
    for index, foot in enumerate(full_contact_points+footprint):
        # Rebalance the whole assembly at each actual pressure-resultant Y.
        # The original load case remains a valid necessary comparison even if
        # another hold/front-support position becomes more demanding.
        local_force = force*(centre[1]-front_y)/(foot[1]-front_y)
        moment = foot_joint_moment(compression_n=local_force, top=top, foot=foot,
            leg_mass_kg=leg['mass_kg'], leg_centre=leg['centre_xyz_mm'])
        original = bolt_group(points, local_force, moment)
        smooth = smooth_bolt_group(points, local_force, moment)
        rows.append({'scope':'full-face linear pressure' if index < 2 else 'whole-foot extreme sensitivity',
            'foot_pressure_resultant_xyz_mm':foot,'joint_moment_nmm':moment,
            'axial_compression_n':local_force,
            'current_bolt_lateral_ratio':original['peak_lateral_ratio'],
            'smooth_bolt_lateral_ratio':smooth['peak_lateral_ratio'],
            'parallel_local_checks':original['parallel_local_checks'],
            'supplemental_splitting':splitting_screen([b['force_xyz_n'] for b in smooth['bolts']]),
            'member':leg_check(local_force, effective_length_mm=loads['support_span_mm'],
                              additional_strong_moment_nmm=abs(moment))})
    passed = all(r['smooth_bolt_lateral_ratio'] <= 1 and r['member']['meets_member_criteria']
                 and r['supplemental_splitting']['ratio'] <= 1 for r in rows[:2])
    paths = [Path(__file__), Path('fea/leg_member_capacity.py'),
             Path('fea/leg_only_load_check.py'), Path('fea/leg_attachment_check.py'),
             Path('fea/leg_smooth_bolt_check.py'), Path('fea/reinforced_timber_resistance.py'),
             Path('fea/dowel_yield.py'), MASS, BUNDLE]
    return {'candidate':loads['candidate'], 'assessment_complete':True,
        'decision':'No passing leg-assembly design established by the conservative assessment',
        'qualified_for_construction':False, 'necessary_checks_pass':passed,
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'load_assumptions':{'climber_lb':250,'vertical_multiplier':2,'horizontal_n':300,
            'hold_projection_mm':100,'equipment_allowance_kg':25,'hardware_allowance_kg':2,
            'rear_load_share_one_leg':1.,'feet_do_not_slide':True,
            'primary_foot_pressure':'Nonnegative linear pressure over full rectangular foot face; resultant spans middle third'},
        'axial_compression_n':force,'supported_span_mm':loads['support_span_mm'],
        'axial_only_member':leg_check(force,effective_length_mm=loads['support_span_mm']),
        'smooth_bolt_moment_interval_nmm':moment_interval(points,force),
        'full_contact_cases':rows[:2], 'whole_foot_sensitivity_cases':rows[2:],
        'limits':[
            'Primary cases use finite full-face triangular pressure at the middle-third boundaries. Whole-foot corners are a separate extreme sensitivity.',
            'Horizontal foot reaction follows the chosen axial load direction; no-slip alone does not enforce that direction.',
            'A failure within this stated envelope defeats a pass; this envelope is not claimed to bound all possible frame actions.',
            'Full joint sagittal moment is conservatively carried throughout the member in addition to its existing self-weight bending allowance.',
            'Prying and bolt combined-action qualification cannot turn a failed lateral/member check into a passing assembly.',
            'No physical breaking weight, whole-frame comparison or floor-friction qualification is claimed.']}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = build()
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps({k:result[k] for k in ('decision','axial_compression_n','necessary_checks_pass')}))
