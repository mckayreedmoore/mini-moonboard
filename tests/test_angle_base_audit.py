"""Angle replacement preserves panels, not former gusset/frame qualification."""
import pytest

from fea import angle_base_audit as audit


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_direct_base_angles_replace_all_gussets_and_restore_old_bores(report):
    assert report['all_tested_geometry_gates_passed'], report['geometry_failures']
    assert report['all_tested_product_geometry_gates_passed'], report['product_geometry_failures']
    replacement = report['base_angle_replacement']
    assert replacement['passed'] and len(replacement['removed_gusset_names']) == 2
    assert len(replacement['removed_gusset_bolt_names']) == 8
    assert all(r['passed'] and r['direct_angle_screw_count'] == 6 for r in replacement['outer_connection_paths'])
    holes = report['former_gusset_bore_restoration']
    assert len(holes) == 8 and all(r['passed'] for r in holes)
    assert all(r['expected_restored_volume_mm3'] > 1. for r in holes)
    assert not replacement['equivalent_stiffness_or_strength_established']
    assert report['retained_geometry']['passed']


def test_replacement_inventory_has_complete_bolts_and_angle_screws(report):
    inventory = report['inventory']
    assert inventory['wood_parts'] == 32
    assert inventory['panel_kicker_screws'] == 151
    assert inventory['brackets'] == 36 and inventory['bracket_screws'] == 216
    assert inventory['bolts'] == 8 and inventory['installed_inserts'] == 0
    assert len(report['bolt_component_envelopes']) == 8
    assert all(r['passed'] for r in report['bolt_component_envelopes'])
    assert all(r['passed'] for r in report['receiver_checks'])
    assert all(r['passed'] for r in report['drilled_axis_checks'])
    assert report['future_insert_reserves']['reserve_count'] == 151
    assert report['future_insert_reserves']['passes_nominal_reserves']


def test_identical_panel_problem_does_not_transfer_frame_forces(report):
    result = report['panel_support_equivalence']
    assert result['fixed_point_restraint_panel_geometry_equivalent']
    assert result['all_panel_kicker_connections_identical']
    assert result['panel_kicker_connection_count'] == 151
    assert len(result['panels']) == 4 and all(r['passed'] for r in result['panels'])
    assert not result['whole_frame_equivalent'] and not result['joint_force_transfer_authorized']
    for flag in ('qualified_for_design', 'structural_analysis_run', 'joint_strength_passed', 'floor_qualified'):
        assert not report[flag]
    assert 'fea/infill_panel_audit.py' in report['source_sha256']
    assert 'mini_moonboard/angle_base_frame.py' in report['source_sha256']
