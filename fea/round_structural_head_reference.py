"""Conditional NDS 2018 plywood head reference; no adjusted assembly capacity."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from fea.round_structural_screw_reference import LBF_N
from fea.round_structural_screw_reference import references as screw_references


def head_pull_through_lbf(head_diameter_in, net_thickness_in, specific_gravity):
    """NDS 2018 Eq. 12.2-6 within Table 12.2F's panel/input range.

    Caller establishes circular head, supported wood panel and net thickness.
    Returns an unadjusted force reference, not resistance to a supplied demand.
    """
    if (not all(math.isfinite(v) for v in
                (head_diameter_in, net_thickness_in, specific_gravity))
            or not .234 <= head_diameter_in <= .500
            or not 5/16 <= net_thickness_in <= 1.5
            or specific_gravity not in (.42, .50)):
        raise ValueError('Require Table 12.2F diameter/thickness and tabulated panel G')
    effective_thickness = min(net_thickness_in, 2.5*head_diameter_in)
    return 690*math.pi*head_diameter_in*specific_gravity**2*effective_thickness


def references():
    # Reuse the existing current-product and all-56-attachment provenance gates.
    current = screw_references()
    diameter = .320
    thickness = 23/32
    excluded_depth = current['basis']['excluded_head_zone_in']
    net = thickness-excluded_depth
    value = head_pull_through_lbf(diameter, net, .42)
    source_hashes = dict(current['source_sha256'])
    own_path = Path(__file__).resolve().relative_to(Path.cwd().resolve())
    source_hashes[str(own_path)] = hashlib.sha256(own_path.read_bytes()).hexdigest()
    return {
        'candidate': current['candidate'], 'product': current['product'],
        'qualified_for_design': False, 'current_demands_evaluated': False,
        'installation_adjustments_applied': False,
        'actual_head_seat_verified': False, 'governing_edition_reconciled': False,
        'actual_head_geometry_applicability_unresolved': True,
        'basis': {
            'method': 'NDS 2018 Eq.12.2-6a, Tables12.2F/12.3.3B; Commentary C12.2.5',
            'head_shape': 'Circular perimeter, nominal 90-degree flat countersunk head',
            'head_diameter_in': diameter, 'panel_thickness_in': thickness,
            'panel_specific_gravity': .42,
            'specific_gravity_basis': 'Other-grade plywood with unknown ply species; '
                                     'Table12.2F footnote2 invokes Table12.3.3B',
            'excluded_head_zone_in': excluded_depth,
            'net_thickness_in': net,
            'thickness_choice': 'Exclude entire ideal cone to apex; discretionary reduction, '
                                'not prescribed countersink depth or measured installation',
            'table_range_satisfied': True,
        },
        'reference_head_lbf': value, 'reference_head_n': value*LBF_N,
        'full_thickness_comparison_n': head_pull_through_lbf(diameter, thickness, .42)*LBF_N,
        'geometry_audit_sha256': current['geometry_audit_sha256'],
        'source_sha256': source_hashes,
        'sources': {
            'nds2018': current['sources']['nds2018'],
            'commentary2018': 'https://awc.org/wp-content/uploads/2021/10/'
                              'AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf',
            'underlying_research': 'https://web-media.awc.org/wp-content/uploads/2021/12/'
                                   '17210650/2018-nds-head-pull-through-paper.pdf',
            'drawing': 'https://dxf82wtg340bb.cloudfront.net/resources/'
                       '8-Flat-Head-Unidrive-and-T-Star-Plus-2D-11-5-21.pdf',
            'counterevidence': 'https://www.buildsite.com/pdf/simpsonstrongtie/'
                               'Simpson-Strong-Tie-Fastening-Systems-Technical-Guide-2895928.pdf#page=20',
        },
        'primary_pdf_sha256': {
            'nds2018': '9a2c8fec7440a46bd6ad2f000feb22da099167a8a5424d7e6f329bf9a7624660',
            'underlying_research': 'b0f7b80cfa891b4babea733894ee856b3da944abb8ce9a982477cb90c4887e2f',
            'drawing': 'ad119b2dbfff8c6c55a230f3edc02d079e2cd9742120c578cdee139f5eb5e9d5',
        },
        'adjustment_basis': 'For ASD head pull-through, Table11.3.1 lists CD, CM, Ct. '
                            'Their end-use applicability is not established here. '
                            'No impact-duration increase; no shank-friction bonus.',
        'limits': 'Conditional nominal reference for intact plywood and supported flush seat. '
                  'Not a SPAX product-specific test value or an adjusted allowable. '
                  'Does not establish TER Table6 G>=0.50, actual seat damage/tolerances, '
                  'panel bending, group sharing, steel action, cyclic behavior or frame release. '
                  'Simpson C-F-2025TECHSUP p20 reports flathead geometry underperformance '
                  'for its dimensional-lumber screws; its factors do not transfer here. '
                  'Reduced thickness is a smaller equation reference, not proof of a lower '
                  'bound on the SPAX countersunk plywood seat. '
                  '2018 inspected; equivalence to project 2024 provisions remains unresolved.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = references()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print({key: result[key] for key in ('reference_head_n', 'qualified_for_design')})
