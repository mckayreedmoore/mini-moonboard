"""Dimensional acceptance and conditional bending references for centered 2x6 bores.

This isolated-section screen does not qualify a timber member or the equipment.
It does not consume the historical rear-prism numerical demand model.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

PSI_MPA = 0.006894757293168361
AWC_REFERENCE = ('https://web-media.awc.org/wp-content/uploads/2023/11/17210143/'
                 'AWC_DVJR2024_20231130_AWCWebsite.pdf')
ICC_REFERENCE = ('https://www.iccsafe.org/building-safety-journal/'
                 'bsj-technical/codenotes-cutting-drilling-and-notching/')
# AWC Table W-1, printed p5: 1345 psi, normal duration, includes repetitive use.
# Remove the table's 13% as instructed; round DOWN from 1170.15 psi.
BENDING_REFERENCE_PSI = 1170.


def dimensional_screen(depth_mm, diameter_mm, *, depth_shortfall_mm=0.,
                       diameter_oversize_mm=0., center_error_mm=0.):
    """Worst-case two-inch edge comparison, centered on measured stock depth.

    Shortfall/oversize/error are nonnegative absolute fabrication allowances.
    Other openings, bearing cuts, connections and applicability are separate.
    """
    values = (depth_mm, diameter_mm, depth_shortfall_mm,
              diameter_oversize_mm, center_error_mm)
    if (not all(math.isfinite(v) for v in values) or min(values) < 0
            or depth_mm <= 0 or diameter_mm <= 0):
        raise ValueError('Require positive finite sizes and nonnegative allowances')
    depth = depth_mm-depth_shortfall_mm
    diameter = diameter_mm+diameter_oversize_mm
    if depth <= diameter:
        raise ValueError('Worst-case hole must remain smaller than stock depth')
    edge = (depth-diameter)/2-center_error_mm
    margin = edge-50.8
    return {'minimum_edge_clearance_mm': edge, 'two_inch_edge_margin_mm': margin,
            'one_third_depth_diameter_margin_mm': depth/3-diameter,
            'dimensional_comparison_passed': margin >= -1.e-10 and diameter <= depth/3+1.e-10,
            'minimum_depth_for_edge_rule_mm': diameter+101.6+2*center_error_mm,
            'other_openings_and_end_cuts_checked': False,
            'local_opening_resistance_qualified': False}


def centered_section(width_mm=38.1, depth_mm=139.7, diameter_mm=38.1):
    """At the bore center, a transverse round hole removes a full-width strip."""
    if (not all(math.isfinite(v) and v > 0 for v in (width_mm, depth_mm, diameter_mm))
            or diameter_mm >= depth_mm):
        raise ValueError('Require positive finite dimensions and an enclosed bore')
    area = width_mm*(depth_mm-diameter_mm)
    strong_i = width_mm*(depth_mm**3-diameter_mm**3)/12
    weak_i = (depth_mm-diameter_mm)*width_mm**3/12
    strong_s, weak_s = strong_i/(depth_mm/2), weak_i/(width_mm/2)
    return {'net_area_mm2': area, 'centroid_n_mm': depth_mm/2,
            'strong_I_mm4': strong_i, 'weak_I_mm4': weak_i,
            'strong_S_mm3': strong_s, 'weak_S_mm3': weak_s,
            'bending_reference_psi': BENDING_REFERENCE_PSI,
            'strong_reference_product_nm': strong_s*BENDING_REFERENCE_PSI*PSI_MPA/1000,
            'weak_reference_product_nm': weak_s*BENDING_REFERENCE_PSI*PSI_MPA/1000,
            'qualified_for_design': False}


def report():
    return {'candidate': 'round-structural-development',
            'scope': 'Isolated nominal section calculation; no current CAD geometry-match gate',
            'current_geometry_authenticated': False,
            'source_sha256': {str(Path(__file__).resolve().relative_to(Path.cwd())):
                hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            'primary_pdf_sha256': {'AWC_Table_W1_printed_p5':
                '1ba94caeec85ca59ea0e41642ea7630dbcd7ffbf7a29673784fc4e3c6ff063e9'},
            'sources': {'AWC_Table_W1_printed_p5': AWC_REFERENCE, 'ICC_CodeNotes': ICC_REFERENCE},
            'nominal_dimensions': dimensional_screen(139.7, 38.1),
            'example_half_mm_each_allowance': dimensional_screen(139.7, 38.1,
                depth_shortfall_mm=.5, diameter_oversize_mm=.5, center_error_mm=.5),
            'isolated_section': centered_section(),
            'frame_member_resistance_qualified': False,
            'limits': 'Bending products require verified US Douglas Fir-Larch No.2, dry unincised '
                'normal-temperature service, accepted local opening detail and verified lateral '
                'restraint. No impact-duration, repetitive-member or flat-use increase. Axial '
                'interaction, shear, torsion, column/beam stability, fastener openings, end cuts '
                'and connections are not evaluated. Dimensional pass is not machining release.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(report(), indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            stream.write(result)
    else:
        print(result, end='')
