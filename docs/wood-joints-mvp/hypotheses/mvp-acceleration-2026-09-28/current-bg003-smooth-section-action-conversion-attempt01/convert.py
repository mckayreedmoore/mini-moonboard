"""Convert reviewed diagnostic actions to nominal smooth-section quantities.

This does not qualify material, thread position, contact state or strength.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
DIAGNOSTIC = BASE.parent / 'support-corner-review-2026-09-30/diagnostics.json'
DIAGNOSTIC_SHA = '174f8f945e41a273318a41fc401f1ef484160b500d624d80f57cd3480a343c98'
CASES = {
    'a12-rear': 'current-corner-native-demand-export-attempt03',
    'a1-rear': 'current-corner-a1-rear-case-bound-export-attempt01',
    'k12-rear': 'current-corner-k12-rear-case-bound-export-attempt01',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def produce():
    assert sha(DIAGNOSTIC) == DIAGNOSTIC_SHA
    diagnostic = json.loads(DIAGNOSTIC.read_text())
    assert diagnostic['status'] == 'PASS_SMALL_MODEL_DIAGNOSTICS_ONLY'
    assert not diagnostic['joint_accepted'] and not diagnostic['capacity_calculated']
    pins = dict(diagnostic['source_sha256'])
    pins[str(DIAGNOSTIC.relative_to(ROOT))] = DIAGNOSTIC_SHA
    producer = DIAGNOSTIC.parent / 'diagnose.py'
    assert sha(producer) == diagnostic['producer_sha256']
    pins[str(producer.relative_to(ROOT))] = sha(producer)
    for name, expected in pins.items():
        assert sha(ROOT / name) == expected, name
    diameter = 6.35
    area = math.pi * diameter**2 / 4
    section_modulus = math.pi * diameter**3 / 32
    ties = {}
    for case, folder in CASES.items():
        source = BASE / folder / 'corner-demand-report.json'
        report = json.loads(source.read_text())
        assert report['actual_case_demand_usable_for_conditional_joint_checks']
        state = report['increments'][-1]
        assert state['load_factor'] == 1.0
        assert state['all_five_corner_bodies_raw_and_interval_balance_passed']
        for bolt in state['primary_physical_bolt_groups']['BG003']['bolts']:
            tie, = [a for a in bolt['actions']
                    if a['role'] == 'physical_bolt_outer_seat_tension']
            assert tie['first'] == 'knee_outer_left_spine'
            assert tie['second'] == 'knee_outer_left_inner_frame_block'
            first = tie['force_on_first_xyz_n']
            second = tie['force_on_second_xyz_n']
            assert first[0] >= 0 and first[1:] == [0.0, 0.0]
            assert all(abs(a+b) < 1e-12 for a,b in zip(first, second))
            ties[case, bolt['axis_id']] = first[0]
    rows = []
    for source in diagnostic['bg003']['rows']:
        axial = ties[source['case'], source['axis']]
        shear = source['middle_cut_internal_force_on_left_YZ_N']
        couple = source['middle_cut_internal_couple_on_left_My_Mz_Nmm']
        magnitude = math.hypot(*couple)
        assert math.isclose(magnitude, source['middle_cut_bending_magnitude_Nmm'], rel_tol=1e-12)
        assert math.isclose(math.hypot(*shear), source['middle_cut_shear_magnitude_N'], rel_tol=1e-12)
        normal_mean = axial / area
        bending = magnitude / section_modulus
        rows.append({
            'case': source['case'], 'axis': source['axis'], 'beta': source['beta'],
            'load_factor': 1.0, 'middle_cut_tension_N': axial,
            'middle_cut_internal_force_on_left_YZ_N': shear,
            'middle_cut_internal_couple_on_left_My_Mz_Nmm': couple,
            'nominal_axial_mean_normal_stress_MPa': normal_mean,
            'nominal_middle_cut_extreme_bending_stress_MPa': bending,
            'nominal_middle_cut_extreme_normal_stress_range_MPa':
                [normal_mean-bending, normal_mean+bending],
            'middle_cut_signed_mean_transverse_traction_YZ_MPa': [v/area for v in shear],
            'diagnostic_sampled_peak_bending_only_stress_MPa':
                source['sampled_peak_bending_magnitude_Nmm']/section_modulus,
        })
    assert len(rows) == 18 and len(ties) == 6
    pins[str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    return {
        'schema': 'bg003_smooth_section_action_conversion/v1',
        'status': 'PASS_SOURCE_BOUND_NOMINAL_ACTION_CONVERSION_ONLY',
        'smooth_gross_diameter_mm': diameter, 'gross_area_mm2': area,
        'elastic_section_modulus_mm3': section_modulus,
        'axial_assumption': 'Outer-seat source tie remains constant through the middle cut; no distributed axial bearing or preload is introduced.',
        'limits': 'Elastic nominal smooth-gross-section conversion of diagnostic zero-gap isotropic-foundation actions. Mean transverse traction is not maximum shear stress. No combined equivalent stress is formed from nonconcurrent stress locations. No yield/capacity comparison, actual thread/runout or washer qualification, grain/gap calibration, shared timber compatibility, splitting or group acceptance.',
        'source_sha256': pins, 'rows': rows,
        'strength_checked': False, 'joint_accepted': False,
        'geometry_changed': False, 'native_solve_run': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    data = produce()
    target = HERE / 'action-conversion.json'
    if args.verify:
        assert json.loads(target.read_text()) == data
        print('PASS_SOURCE_BOUND_NOMINAL_ACTION_CONVERSION_ONLY: 18 scenarios')
    else:
        target.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+'\n')
        print('Wrote 18 source-bound action conversions')
