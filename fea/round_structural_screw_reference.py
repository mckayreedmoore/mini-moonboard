"""Conditional single-screw references; no current demand or assembly qualification."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from fea.dowel_yield import single_shear

LBF_N = 4.4482216152605
PRODUCT = Path('docs/round-panel-countersink-reference.json')
AUDIT = Path('fea/results/round-structural-audit-v1.json')


def wood_interaction(tension_n, lateral_n, *, withdrawal_n, lateral_reference_n,
                     head_reference_n):
    """NDS 2018 Eq.12.4-1 wood-screw interaction with separately supplied head cap.

    All capacities must already carry applicable adjustments. Withdrawal is a
    total force, not force per thread length. Nonnegative tensile demand only;
    compression/contact and combined steel resistance are outside this function.
    """
    demands = (tension_n, lateral_n)
    capacities = (withdrawal_n, lateral_reference_n, head_reference_n)
    if (not all(math.isfinite(v) and v >= 0 for v in demands)
            or not all(math.isfinite(v) and v > 0 for v in capacities)):
        raise ValueError('Require nonnegative finite demands and positive adjusted references')
    resultant = math.hypot(*demands)
    # R/Z_alpha = (V/R)*(V/Z) + (T/R)*(T/W); stable pure-load limits.
    ratio = ((lateral_n/resultant)*(lateral_n/lateral_reference_n)
             + (tension_n/resultant)*(tension_n/withdrawal_n)) if resultant else 0.
    return {'wood_interaction_ratio': ratio, 'head_pull_through_ratio': tension_n/head_reference_n,
            'qualified_for_design': False,
            'limits': 'Supplied adjusted references only; steel interaction, group/splitting, '
                      'contact, cyclic behavior and actual demand validity not evaluated.'}


def references():
    product = json.loads(PRODUCT.read_text())['nominal']
    audit = json.loads(AUDIT.read_text())
    if (audit['candidate'] != 'round-structural-development'
            or not audit['all_tested_geometry_gates_passed']
            or not audit['all_tested_product_geometry_gates_passed']):
        raise ValueError('Require matching current geometric acceptance')
    for path, sha in audit['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha:
            raise ValueError('Stale geometry producer: '+path)
    nominal_in = {k: v/25.4 for k, v in product.items() if k.endswith('_mm')}
    diameter = nominal_in['minor_thread_diameter_mm']
    major = nominal_in['major_thread_diameter_mm']
    length = nominal_in['overall_length_from_head_top_mm']
    thread = nominal_in['thread_length_including_tip_mm']
    head = nominal_in['head_diameter_mm']
    if not all(math.isclose(a, b, abs_tol=1e-10, rel_tol=0.) for a, b in
               ((diameter, .100), (major, .163), (length, 2.), (thread, 1.240), (head, .320))):
        raise ValueError('Reassess references for changed screw dimensions')
    side = 23/32
    penetration = length-side
    screws = [r for r in audit['screw_tip_checks']
              if r['connection'].startswith(('round_panel_', 'round_kicker_'))]
    if (len(screws) != 56 or product['included_head_angle_degrees'] != 90.
            or any(not math.isclose(r['gross_penetration_mm']/25.4, penetration,
                                    abs_tol=1e-8, rel_tol=0.) for r in screws)):
        raise ValueError('Reassess bearing lengths for changed panel thickness or head')
    # Exclude the entire ideal 90-degree cone to its apex, giving no lateral
    # bearing credit to head/neck material. This is not a countersink instruction.
    head_zone = head/2
    # NDS permits E=2D. Using major diameter here deducts more than root D.
    tapered_tip = 2*major
    moment = 187000*diameter**3/6
    inputs = {'main_length_in': penetration-tapered_tip/2,
              'side_length_in': side-head_zone,
              'main_bearing_lb_in': 4650*diameter,
              'side_bearing_lb_in': 3350*diameter,
              'main_yield_moment_lb_in': moment, 'side_yield_moment_lb_in': moment,
              'gap_in': 0.,
              'reduction_terms': {k: 2.2 for k in ('Im', 'Is', 'II', 'IIIm', 'IIIs', 'IV')}}
    lateral = single_shear(**inputs)
    if penetration < thread:
        raise ValueError('Full evaluated thread is not embedded')
    return {'candidate': audit['candidate'], 'product': 'SPAX XFT08P-2000',
            'qualified_for_design': False, 'current_demands_evaluated': False,
            'installation_adjustments_applied': False, 'steel_interaction_evaluated': False,
            'geometry_audit_sha256': hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
            'basis': {'method': 'TR12 single shear and NDS 2018 Chapter12; 2024 equivalence not verified',
                     'receiver': 'Douglas Fir-Larch, assigned G=0.50, Fe=4650psi',
                     'panel': '23/32-inch other-grade plywood, unknown ply species, G=0.42, Fe=3350psi',
                     'root_diameter_in': diameter, 'Fyb_psi': 187000,
                     'nominal_penetration_in': penetration,
                     'excluded_head_zone_in': head_zone, 'tapered_tip_allowance_in': tapered_tip},
            'lateral_inputs': inputs, 'lateral': lateral,
            'reference_lateral_n': lateral['reference_lateral_lbf']*LBF_N,
            'reference_withdrawal_n': 133*thread*LBF_N,
            'conditional_head_reference_n': 212*LBF_N,
            'head_reference_condition': 'TER Table6 requires plywood assigned G>=0.50; '
                                        'the G=0.42 lateral default does not establish this condition',
            'steel_isolated_reference_n': {'tension': 460*LBF_N, 'shear': 345*LBF_N},
            'sources': {'spax': 'https://www.drjcertification.org/report/download/1936',
                        'nds2018': 'https://plib.org/wp-content/uploads/2020/09/AWC-NDS2018.pdf',
                        'tr12': 'https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf'},
            'primary_pdf_sha256': {
                'spax': 'e989b7a89cfd6dce92c22bd88d79f0171382f605d5939940fedb62dd661fe8ed',
                'nds2018': '9a2c8fec7440a46bd6ad2f000feb22da099167a8a5424d7e6f329bf9a7624660',
                'tr12': '95abb7d382aadf6984121f8731a5b91c2b633516e7f134991ad0a34a1b916be2'},
            'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                              (Path(__file__).relative_to(Path.cwd()), Path('fea/dowel_yield.py'), PRODUCT, AUDIT)},
            'limits': 'Nominal single-fastener, one-plane, seated face-to-face wood connection. '
                      'Root-diameter and reduced-length reference is not a calibrated spring stiffness. '
                      'No end-use adjustments, group multiplier, load distribution, net-panel strength, '
                      'splitting, cyclic allowance or physical assembly qualification. '
                      'No SPF lateral table is reassigned to DF-L.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = references()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print({k: result[k] for k in ('reference_lateral_n', 'reference_withdrawal_n', 'qualified_for_design')})
