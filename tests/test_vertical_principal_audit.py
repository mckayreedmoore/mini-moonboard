"""Discrete seam supports and extra connections never imply a strength pass."""
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea import vertical_principal_audit as audit


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_interval_union_preserves_unsupported_seam_spans():
    assert audit.free_intervals([[-5, 2], [1, 4], [7, 9], [12, 20]], 0, 15) == [[4, 7], [9, 12]]
    assert audit.free_intervals([], -1, 1) == [[-1, 1]]
    assert audit.free_intervals([[-2, 3]], -1, 1) == []


def test_repair_inventory_follows_current_screws_instead_of_fixed_count():
    receiver = cq.Solid.makeBox(70, 40, 60)
    screws = [SimpleNamespace(name=f'screw_{i}', members=('panel', 'receiver'),
              start=cq.Vector(x, 20, 0), direction=cq.Vector(0, 0, 1), components=lambda: ())
              for i, x in enumerate((15, 50))]
    result = audit.repair_reserves({'receiver': SimpleNamespace(shape=receiver)}, screws, screws)
    assert result['reserve_count'] == 2 and result['passes_nominal_reserves']
    assert not result['qualified_for_design'] and not result['qualified_repair']
    # Moving one reservation outside its receiver must fail that screw.
    screws[1].start = cq.Vector(69, 20, 0)
    result = audit.repair_reserves({'receiver': SimpleNamespace(shape=receiver)}, screws, screws)
    assert result['reserve_count'] == 2 and not result['passes_nominal_reserves']


def test_added_principals_have_support_but_no_strength_inheritance(report):
    assert report['all_tested_geometry_gates_passed'], report['geometry_failures']
    assert report['all_tested_product_geometry_gates_passed'], report['product_geometry_failures']
    for name in ('qualified_for_design', 'structural_analysis_run', 'joint_strength_passed', 'floor_qualified'):
        assert not report[name]
    supports = report['new_principal_support_paths']
    assert len(supports) == 4
    assert sorted(r['principal_x_mm'] for r in supports) == pytest.approx([-770, -370, 430, 830])
    assert all(r['footprint_over_post_fraction'] == pytest.approx(1., abs=1e-5) for r in supports)
    assert all(r['passed'] and not r['strength_qualified'] for r in supports)
    assert report['unresolved_original_header_transfer']['principal_footprint_beyond_post_mm'] == pytest.approx(48.1627295277)
    assert not report['unresolved_original_header_transfer']['strength_assessed']
    gussets = report['retained_gussets']
    assert gussets['members'] and all(r['raw_shape_unchanged'] for r in gussets['members'])
    assert gussets['bolt_count'] == 8 and gussets['bolt_axes_and_grips_unchanged']
    assert not gussets['current_forces_available'] and not gussets['force_reduction_established']


def test_removed_rails_leave_explicit_free_panel_edges(report):
    assert report['inventory']['interior_horizontal_seam_rails'] == []
    comparison = report['horizontal_seam_comparison']
    assert len(comparison['current']) == len(comparison['previous']) == 2
    for edge in comparison['current']:
        # Six bays remain unsupported. Net service pockets may also produce
        # small gaps inside a nominal support and must not be discarded.
        spans = edge['clear_spans_mm']
        assert len([span for span in spans if span > 100.]) == 6
        assert edge['maximum_clear_span_mm'] == pytest.approx(392.05, abs=1e-5)
        if edge['edge'] == 'lower_panel_top':
            assert any(0.39 < span < 0.41 for span in spans)
        assert not any(r['member'].startswith('base_rail_mid_') for r in edge['backing'])
    assert all(any(r['member'].startswith('base_rail_mid_') for r in edge['backing'])
               for edge in comparison['previous'])


def test_every_new_screw_has_ownership_reserve_and_product_checks(report):
    count = report['inventory']['panel_kicker_screws']
    assert count > 56
    assert len(report['panel_kicker_screws']) == count
    assert report['future_insert_reserves']['reserve_count'] == count
    assert report['future_insert_reserves']['passes_nominal_reserves']
    assert report['inventory']['bracket_screws'] == 6*report['inventory']['brackets']
    assert all(r['passed'] for r in report['bracket_screw_ownership'])
    assert all(r['passed'] for r in report['receiver_checks'])
    assert all(r['passed'] for r in report['drilled_axis_checks'])
    assert 'mini_moonboard/vertical_principal_frame.py' in report['source_sha256']
    assert 'fea/paired_rail_audit.py' in report['source_sha256']
