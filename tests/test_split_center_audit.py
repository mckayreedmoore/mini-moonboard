"""Split-center clearance, complete bolt stacks and retained qualification gaps."""
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea import split_center_audit as audit
from mini_moonboard.bolted_frame import FrameBolt


@pytest.fixture(scope='module')
def report():
    return audit.build()


@pytest.mark.parametrize('sign', [-1, 1])
def test_bolt_component_envelopes_follow_both_axis_directions(sign):
    bolt = FrameBolt('test', cq.Vector(100, 0, 0), cq.Vector(sign, 0, 0),
                     95.25, 9.525, ('a', 'b'), 'bolt', 76.2)
    row = audit.bolt_components([bolt])[0]
    assert row['passed'] and row['component_count'] == 5
    assert [c['role'] for c in row['components']] == ['shaft', 'head_washer', 'nut_washer', 'head', 'nut']
    assert row['components'][-1]['axial_interval_mm'][0] == pytest.approx(80.264)
    missing_nut = SimpleNamespace(name='missing', kind='bolt', direction=bolt.direction,
                                  start=bolt.start, length=bolt.length, grip=bolt.grip,
                                  components=lambda: bolt.components()[:-1])
    assert not audit.bolt_components([missing_nut])[0]['passed']
    shapes = bolt.components()
    wrong_end = SimpleNamespace(name='wrong_end', kind='bolt', direction=bolt.direction,
                                start=bolt.start, length=bolt.length, grip=bolt.grip,
                                components=lambda: (*shapes[:-1], shapes[-1].translate((-sign*100., 0, 0))))
    assert not audit.bolt_components([wrong_end])[0]['passed']


def test_six_independent_principals_clear_center_lights_and_have_posts(report):
    assert report['all_tested_geometry_gates_passed'], report['geometry_failures']
    assert report['all_tested_product_geometry_gates_passed'], report['product_geometry_failures']
    members = report['inventory']['new_single_2x6_principals']
    assert len(members) == 6 and 'base_principal_center' not in members
    clearances = report['split_center_service_clearance']
    assert len(clearances) == 2 and all(r['passed'] for r in clearances)
    assert min(r['minimum_full_service_envelope_clearance_mm'] for r in clearances) == pytest.approx(11.75, abs=1e-5)
    assert all(r['difference_from_uncut_principal_mm3'] < .01 for r in clearances)
    assert len(report['new_principal_support_paths']) == 6
    assert all(r['passed'] for r in report['new_principal_support_paths'])
    for row in report['header_transverse_transfer']['member_transfers']:
        if row['member'].startswith('base_principal_'):
            assert row['footprint_rear_overhang_beyond_post_mm'] == pytest.approx(0., abs=1e-5)
            assert row['footprint_over_post_fraction'] == pytest.approx(1., abs=1e-5)
        assert not row['strength_assessed']


def test_panel_seam_overhang_and_gusset_demands_are_not_qualified(report):
    seam = report['vertical_panel_seam']
    assert seam['backing_edge_distances_left_right_mm'] == pytest.approx([50.95, 50.95])
    assert not seam['panel_edges_supported_continuously'] and not seam['strength_qualified']
    for flag in ('qualified_for_design', 'structural_analysis_run', 'joint_strength_passed', 'floor_qualified'):
        assert not report[flag]
    gussets = report['retained_gussets']
    assert gussets['bolt_axes_and_grips_unchanged']
    assert not gussets['force_reduction_established']
    assert not gussets['current_forces_available']


def test_every_screw_and_complete_bolt_stack_is_accounted_for(report):
    count = report['inventory']['panel_kicker_screws']
    assert count > 56
    assert len(report['panel_kicker_screws']) == count
    assert report['future_insert_reserves']['reserve_count'] == count
    assert report['future_insert_reserves']['passes_nominal_reserves']
    bolts = report['bolt_component_envelopes']
    assert len(bolts) == report['inventory']['bolts'] == 16
    assert all(r['passed'] and r['component_count'] == 5 for r in bolts)
    assert all(r['passed'] for r in report['drilled_axis_checks'])
    assert 'fea/vertical_principal_audit.py' in report['source_sha256']
    assert 'mini_moonboard/split_center_frame.py' in report['source_sha256']
