"""Independent arithmetic/source check; no mechanics or code applicability pass."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BASE = Path(__file__).resolve().parent.parent
END = BASE / 'current-corner-bg001-signed-end-distance-attempt01/signed-end-distance-screen.json'
WOOD = BASE / 'current-bg001-appendix-e-parallel-row-screen-attempt01/screen.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    end, wood = (json.loads(p.read_text()) for p in (END, WOOD))
    for pins in (end['input_provenance']['source_sha256'], wood['source_hashes']):
        for path, expected in pins.items():
            assert sha(ROOT / path) == expected, path
    factors = []
    for row in end['signed_direction_results']:
        for g in row['member_geometry'].values():
            x, y, z = g['member_action_xyz_N']
            angle = math.degrees(math.atan2(math.hypot(x, y), abs(z)))
            full = 7 - 3 * angle / 90
            factor = min(1, g['loaded_end_distance_D'] / full)
            assert math.isclose(angle, g['load_to_grain_angle_deg'], abs_tol=1e-10)
            assert math.isclose(factor, g['angle_interpolated_Cdelta'], abs_tol=1e-12)
            assert g['loaded_grain_end'] == ('g+' if z > 0 else 'g-')
            factors.append(factor)
    assert math.isclose(min(factors), end['group_angle_interpolated_Cdelta'], abs_tol=1e-12)
    for row in end['reference_scalings']:
        reference = row['unadjusted_actual_direction_mode_IV_reference_N'] * min(factors)
        assert math.isclose(reference, row['group_Cdelta_only_reference_N'], rel_tol=1e-12)
        assert math.isclose(row['demand_N'] / reference, row['demand_over_group_Cdelta_only_reference'], rel_tol=1e-12)
        assert not row['Cg_applied']
    for row in wood['row_tear_out_component_screens']:
        # E.3.3: two shear lines, each with triangular stress distribution Fv/2.
        reference = row['n_bolts_in_row'] * 180 * (row['member_thickness_along_bolt_axis_mm'] / 25.4) * (row['critical_spacing_mm'] / 25.4)
        assert math.isclose(reference, row['base_unadjusted_row_reference_lbf'], rel_tol=1e-12)
        assert math.isclose(row['parallel_component_demand_N'] / row['base_unadjusted_row_reference_N'], row['component_ratio_to_base_unadjusted_reference'], rel_tol=1e-12)
        assert not row['base_reference_inputs']['Fv_adjusted_factors_applied']
    net = wood['spine_candidate_net_section_reference']
    assert math.isclose(575 * net['candidate_net_area_mm2'] / 25.4**2, net['base_unadjusted_net_tension_reference_lbf'], rel_tol=1e-12)
    assert not wood['standard_source']['cvr_scope_review']['cvr_applied']
    result = {
        'status': 'PASS_CONDITIONAL_REFERENCE_ARITHMETIC_AND_SOURCE_AUDIT',
        'checks': ['Repository source hashes match', 'Signed ends and recorded interpolation arithmetic agree', 'Group minimum and individual reference scaling agree without Cg', 'Appendix E nominal row/net arithmetic agrees; unsupported glulam Cvr omitted'],
        'screen_hashes': {str(p.relative_to(ROOT)): sha(p) for p in (END, WOOD)},
        'mechanical_acceptance': False,
        'limits': ['Interpolation authority is reused from the recorded reviewed method, not independently established by this arithmetic check.', 'Mixed-action Cg, splitting, adjusted resistance and complete corner acceptance remain open.', 'No unchanged original LEG/FLOOR-RUNNER resistance reopened.'],
    }
    (Path(__file__).resolve().parent / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])

if __name__ == '__main__':
    main()
