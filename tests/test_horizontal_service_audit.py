"""Current structural fit and provisional electrical routing are distinct gates."""
import pytest

from fea import horizontal_service_audit as audit


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_horizontal_fit_inventory_and_qualification_boundaries(report):
    assert report['all_tested_geometry_gates_passed'], report['geometry_failures']
    assert report['all_tested_product_geometry_gates_passed'], report['product_geometry_failures']
    inventory = report['inventory']
    assert len(inventory['new_single_2x6_principals']) == 2
    assert len(inventory['service_rails']) == 4
    assert inventory['bolts'] == 8
    assert len(report['bolt_component_envelopes']) == 8
    assert all(row['passed'] for row in report['bolt_component_envelopes'])
    assert all(row['passed'] for row in report['bracket_screw_ownership'])
    assert report['future_insert_reserves']['reserve_count'] == inventory['panel_kicker_screws']
    for flag in ('qualified_for_design', 'structural_analysis_run', 'joint_strength_passed', 'floor_qualified'):
        assert report[flag] is False


def test_electrical_fit_uses_machined_parts_and_excludes_unknown_mass(report):
    result = report['electrical_fit']
    assert result['light_count'] == 132 and result['wire_count'] == 131
    assert not result['collisions']
    assert not result['hold_service_collisions']
    assert result['front_cutouts'] and all(row['passed'] for row in result['front_cutouts'])
    assert all(row['entry_face'].startswith('front N=0') for row in result['front_cutouts'])
    assert len(result['segments']) == 131
    assert all(row['within_approximate_budget'] for row in result['segments'])
    assert all(row['qualified_for_installation'] is False for row in result['segments'])
    assert result['electrical_mass_included'] is False and result['electrical_qualified'] is False
    # The upper panel's bottom edge now has actual horizontal-rail support.
    lower, upper = report['horizontal_seam_comparison']['current']
    assert not any(row['member'].startswith('base_rail_') for row in lower['backing'])
    assert {row['member'] for row in upper['backing'] if row['member'].startswith('base_rail_')} == {
        'base_rail_service_upper_left', 'base_rail_service_upper_right'}
    assert upper['maximum_clear_span_mm'] == pytest.approx(101.9)
