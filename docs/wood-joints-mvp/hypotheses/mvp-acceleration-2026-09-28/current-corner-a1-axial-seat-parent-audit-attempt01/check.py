"""Independent A1 seat/tie force and conditional component arithmetic check."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT, BASE = HERE.parents[4], HERE.parent
SCREEN = BASE/'current-corner-a1-rear-axial-seat-screen-attempt01/screen.json'
REPORT = BASE/'current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    s, r = (json.loads(p.read_text()) for p in (SCREEN, REPORT))
    for pin in s['source_pins'].values():
        assert sha(ROOT/pin['path']) == pin['sha256'], pin['path']
    bolts = {b['axis_id']: b for g in r['increments'][-1]['primary_physical_bolt_groups'].values() for b in g['bolts']}
    assert len(s['axes']) == len(bolts) == 6
    ratios, seats, changed = [], 0, []
    for axis in s['axes']:
        tie = next(a for a in bolts[axis['axis_id']]['actions'] if a['role'] == 'physical_bolt_outer_seat_tension')
        demand = math.sqrt(math.fsum(v*v for v in tie['force_on_first_xyz_n']))
        assert math.isclose(demand, axis['a1_rear_positive_tie_tension_demand_n'], rel_tol=1e-12)
        exceeds = demand > axis['a12_rear_comparison_only_tie_tension_n']
        assert exceeds == axis['a1_rear_tie_exceeds_a12_rear_on_this_axis']
        if exceeds:
            changed.append(axis['axis_id'])
        assert len(axis['seats']) == 2
        for seat in axis['seats']:
            side = 'first' if seat['physical_member'] == tie['first'] else 'second'
            assert seat['physical_member'] == tie[side]
            assert seat['seat_force_on_member_xyz_n'] == tie[f'force_on_{side}_xyz_n']
            assert math.isclose(demand/seat['modeled_cad_annular_plan_area_mm2'], seat['modeled_cad_full_annulus_uniform_average_pressure_mpa'], rel_tol=1e-12)
            annulus = seat['conditional_25nwus_min_annulus']
            if annulus:
                inner = max(annulus['maximum_id_in'], annulus['wood_bore_diameter_in'])
                area = math.pi/4*25.4**2*(annulus['minimum_od_in']**2-inner**2)
                assert math.isclose(area, annulus['area_mm2'], rel_tol=1e-12)
                assert math.isclose(demand/area, annulus['uniform_average_pressure_mpa'], rel_tol=1e-12)
            wood = seat['conditional_base_timber_fc_perp_component']
            if wood and wood.get('reference_n') is not None:
                assert seat['wood_receiver_kind'] == 'timber'
                ref = 625*0.006894757293168361*wood['full_annulus_area_mm2']
                assert math.isclose(ref, wood['reference_n'], rel_tol=1e-10)
                assert math.isclose(demand/ref, wood['demand_over_reference_component_ratio'], rel_tol=1e-10)
                ratios.append(demand/ref)
            seats += 1
        steel = axis['conditional_bolt_grade5_FyAt_component']
        reference = steel['minimum_yield_psi']*steel['tensile_stress_area_in2']*4.4482216152605
        assert math.isclose(reference, steel['unadjusted_tensile_first_yield_reference_n'], rel_tol=1e-12)
        assert math.isclose(demand/reference, steel['A1_tension_over_reference_component_ratio'], rel_tol=1e-12)
    assert seats == 12 and len(ratios) == 4 and len(changed) == 3
    result = {'status':'PASS_PARENT_A1_CONDITIONAL_AXIAL_SEAT_ARITHMETIC_AND_INVENTORY','screen_sha256':sha(SCREEN),'report_sha256':sha(REPORT),'bolt_count':6,'seat_count':12,'axes_with_larger_A1_tie_than_A12':changed,'maximum_base_timber_component_ratio':max(ratios),'joint_accepted':False,'limits':['Source-bound A1 actions only; no A12 demand transfer.','Ideal annulus and conditional material/hardware references; no complete joint, washer or combined bolt resistance.']}
    (HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])

if __name__ == '__main__':
    main()
