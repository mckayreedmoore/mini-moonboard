"""Independent seat inventory, vector and reference arithmetic audit."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
SCREEN = BASE / 'current-corner-axial-tie-seat-screen-attempt01/screen.json'
REPORT = BASE / 'current-corner-native-demand-export-attempt03/corner-demand-report.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    screen, report = (json.loads(p.read_text()) for p in (SCREEN, REPORT))
    for pin in screen['source_pins'].values():
        assert sha(ROOT / pin['path']) == pin['sha256'], pin['path']
    bolts = {bolt['axis_id']: bolt for group in report['increments'][-1]['primary_physical_bolt_groups'].values() for bolt in group['bolts']}
    assert len(screen['axes']) == len(bolts) == 6
    seats = 0
    timber_ratios = []
    for axis in screen['axes']:
        tie = next(a for a in bolts[axis['axis_id']]['actions'] if a['role'] == 'physical_bolt_outer_seat_tension')
        demand = math.sqrt(math.fsum(v*v for v in tie['force_on_first_xyz_n']))
        assert math.isclose(demand, axis['positive_outer_seat_tie_tension_demand_n'], rel_tol=1e-12)
        assert len(axis['seats']) == 2
        for seat in axis['seats']:
            side = 'first' if seat['physical_member'] == tie['first'] else 'second'
            assert seat['physical_member'] == tie[side]
            assert seat['seat_force_on_member_xyz_n'] == tie[f'force_on_{side}_xyz_n']
            assert math.isclose(demand / seat['modeled_cad_annular_plan_area_mm2'], seat['modeled_cad_full_annulus_uniform_average_pressure_mpa'], rel_tol=1e-12)
            annulus = seat['conditional_25nwus_minimum_annulus_scenario']
            if annulus is not None:
                area = math.pi/4 * ((annulus['minimum_od_in']*25.4)**2 - (annulus['governing_inner_diameter_in']*25.4)**2)
                assert math.isclose(area, annulus['full_annulus_area_mm2'], rel_tol=1e-12)
                assert math.isclose(demand/area, annulus['uniform_average_pressure_mpa'], rel_tol=1e-12)
            wood = seat['conditional_wood_bearing_component']
            if wood['unadjusted_Fc_perp_reference_n'] is not None:
                assert seat['wood_receiver_kind'] == 'timber'
                assert seat['load_grain_relation'] == 'perpendicular_to_proposed_grain'
                ref = 625 * 0.006894757293168361 * wood['conditional_full_annulus_area_mm2']
                assert math.isclose(ref, wood['unadjusted_Fc_perp_reference_n'], rel_tol=1e-10)
                assert math.isclose(demand/ref, wood['demand_over_reference_component_ratio'], rel_tol=1e-10)
                timber_ratios.append(demand/ref)
            seats += 1
        steel = axis['conditional_1_4_20_unc_grade5_bolt_material_screen']
        inputs = steel['assumptions']
        reference = inputs['project_specified_minimum_yield_psi'] * inputs['thread_tensile_stress_area_in2'] * 4.4482216152605
        assert math.isclose(reference, steel['unadjusted_tensile_first_yield_reference_n'], rel_tol=1e-12)
        assert math.isclose(demand/reference, steel['axial_tension_demand_over_reference_component_ratio'], rel_tol=1e-12)
    assert seats == 12 and len(timber_ratios) == 4
    result = {'status': 'PASS_PARENT_CONDITIONAL_AXIAL_SEAT_ARITHMETIC_AND_INVENTORY', 'screen_sha256': sha(SCREEN), 'report_sha256': sha(REPORT), 'bolt_count': 6, 'seat_count': seats, 'base_timber_perpendicular_comparison_count': 4, 'maximum_base_timber_reference_ratio': max(timber_ratios), 'joint_accepted': False, 'limits': ['Full-annulus average pressure is hypothetical, not a local pressure field or verified support area.', 'Candidate-block strength assignment, parallel-grain BG045 bearing, steel washer response and combined bolt interactions remain open.', 'No unchanged original LEG/FLOOR-RUNNER resistance reopened.']}
    (HERE/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result['status'])

if __name__ == '__main__':
    main()
