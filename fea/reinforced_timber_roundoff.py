"""Necessary resistance failures that persist over native print uncertainty."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from fea.reinforced_timber_resistance import adjusted_reference


def assess(native, uncertainty):
    members = {}
    for name, entry in native['member_section_demands'].items():
        width, depth = entry['member']['width_mm'], entry['member']['depth_mm']
        swapped = width > depth
        b, d = min(width, depth), max(width, depth)
        ref = adjusted_reference(d)
        ratios = []
        for action, radius in zip(entry['sections'], uncertainty['member_print_roundoff'][name]['sections'], strict=True):
            if (action['station_along_grain_mm'] != radius['station_along_grain_mm']
                    or action['include_station_loads'] != radius['include_station_loads']):
                raise ValueError('Section uncertainty ordering mismatch')
            fc = max(0., -action['axial_n_tension_positive']-radius['axial_n_radius'])/(b*d)
            ms, mw = ('moment_v', 'moment_u') if swapped else ('moment_u', 'moment_v')
            fs = max(0., abs(action[ms+'_nmm'])-radius[ms+'_nmm_radius'])/(b*d*d/6)
            fw = max(0., abs(action[mw+'_nmm'])-radius[mw+'_nmm_radius'])/(d*b*b/6)
            ratios.append((fc/ref['Fc_star_mpa'])**2+(fs+fw)/ref['Fb_star_mpa'])
        members[name] = {'maximum_necessary_interaction_lower_bound': max(ratios),
                         'failure_even_fully_braced_and_after_roundoff': max(ratios) > 1.}
    legs = {}
    # Equal maximum parallel-grain Fe in BOTH members, smooth full shank,
    # Cg=1, CD=1 and no geometry reductions deliberately maximize ModeII.
    # Use the most favorable Ktheta=1 (ModeII Rd=3.6) for a true upper bound.
    # A ratio below1 does not establish adequacy or erase directional failures.
    upper_mode_ii = 5600*.375*1.5*(math.sqrt(2)-1)/3.6*4.4482216152605
    for name, action in native['physical_connection_forces'].items():
        if not name.startswith('lumber_leg_bolt_'):
            continue
        force = action['force_on_first_xyz_n']
        radius = uncertainty['physical_connection_force_radius_xyz_n'][name]
        lower = math.hypot(max(0., abs(force[1])-radius[1]), max(0., abs(force[2])-radius[2]))
        legs[name] = {'lateral_force_lower_bound_n': lower,
                      'full_shank_best_bearing_ModeII_capacity_upper_bound_n': upper_mode_ii,
                      'ratio_lower_bound_to_optimistic_ModeII': lower/upper_mode_ii}
    return {'members': members, 'leg_bolts': legs, 'qualified_for_design': False,
            'scope': 'Same conditional sticking model; does not repair inadmissible floor friction'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, action='append', required=True)
    parser.add_argument('--roundoff', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if len(args.native) != len(args.roundoff):
        raise ValueError('Require one uncertainty file per native report')
    sources = [Path(__file__), Path('fea/reinforced_timber_resistance.py'), *args.native, *args.roundoff]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    cases = []
    for native_path, uncertainty_path in zip(args.native, args.roundoff, strict=True):
        native, uncertainty = json.loads(native_path.read_bytes()), json.loads(uncertainty_path.read_bytes())
        if uncertainty['original_report_sha256'] != hashes[str(native_path)]:
            raise ValueError('Uncertainty file does not authenticate this native report')
        cases.append({'native_report': str(native_path), 'roundoff_report': str(uncertainty_path),
                      **assess(native, uncertainty)})
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest for p, digest in hashes.items()):
        raise RuntimeError('Input/source changed during calculation')
    with args.output.open('x') as stream:
        json.dump({'source_and_input_sha256': hashes, 'cases': cases}, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
