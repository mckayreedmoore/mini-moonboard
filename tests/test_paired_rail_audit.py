"""Connection changes must not become structural or floor approval."""
from dataclasses import dataclass
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea import paired_rail_audit as audit


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_current_fit_keeps_unresolved_transverse_header_transfer(report):
    assert report['all_tested_geometry_gates_passed'], report['geometry_failures']
    assert report['all_tested_product_geometry_gates_passed'], report['product_geometry_failures']
    for key in ('qualified_for_design', 'structural_analysis_run', 'joint_strength_passed', 'floor_qualified'):
        assert not report[key]
    transfer = report['unresolved_header_transfer']
    assert transfer['principal_footprint_beyond_post_mm'] == pytest.approx(48.1627295277)
    assert not transfer['strength_assessed']
    principal = next(r for r in report['header_support'] if r['member'] == 'base_principal_center')
    assert principal['gap_mm'] == pytest.approx(0., abs=1e-6)
    assert principal['nominal_contact_area_fraction'] == pytest.approx(1., abs=1e-5)
    assert report['base_bracket_path']['explicit_path_present']
    assert report['base_bracket_path']['center_bracket_screws'] == 6
    assert not report['base_bracket_path']['strength_qualified']


def test_all_repair_reserves_and_new_occupied_holes_are_checked(report):
    inventory = report['inventory']
    assert inventory['panel_kicker_screws'] == 56
    assert inventory['bolts'] == 16
    assert inventory['installed_inserts'] == 0
    assert len(inventory['independent_paired_rails']) == 4
    assert inventory['bracket_screws'] == 6*inventory['brackets']
    assert report['future_insert_reserves']['reserve_count'] == 56
    assert report['future_insert_reserves']['passes_nominal_reserves']
    header = [r for r in report['receiver_checks']
              if r['connection'].startswith('clip_paired_base_center_') and r['member'] == 'base_header']
    assert len(header) == 3
    assert all(r['axial_material_mm'] >= r['required_gross_material_mm']-1e-5 for r in header)
    drilled = [r for r in report['drilled_axis_checks']
               if r['connection'].startswith('clip_paired_base_center_')]
    assert len(drilled) == 6 and all(r['passed'] for r in drilled)
    assert not report['hardware_body_collisions']
    assert not report['distinct_fastener_collisions']
    assert not report['bracket_body_collisions']


def test_real_product_end_failures_are_rechecked_after_relocation(report):
    rows = {r['connection']: r for r in report['panel_kicker_screws']}
    assert len(rows) == 56
    for name in ('timber_kicker_right_0_2', 'timber_panel_upper_right_2'):
        assert min(rows[name]['end_distances_mm']) == pytest.approx(46.9, abs=1e-5)
        assert rows[name]['passes_reversible_end']
    assert 'fea/selective_connection_strength.py' in report['source_sha256']
    assert 'fea/screw_insert_repair_reserve.py' in report['source_sha256']
    assert 'mini_moonboard/paired_rail_frame.py' in report['source_sha256']


def test_hardware_collision_exemption_is_only_own_components_and_threads():
    @dataclass
    class Connection:
        name: str
        members: tuple
        kind: str
        shapes: tuple

        def components(self):
            return self.shapes

    cube = cq.Solid.makeBox(10, 10, 10)
    small = cq.Solid.makeBox(2, 2, 2, cq.Vector(2, 2, 2))
    # Own shaft/head overlap is ignored, but the head still collides with wood.
    own = Connection('own', ('wood', 'clip'), 'screw', (small, small))
    parts = {'wood': SimpleNamespace(shape=cube),
             'clip': SimpleNamespace(shape=cube.translate((20, 0, 0)))}
    body, between = audit.hardware_collisions([own], parts)
    assert body == [{'connection': 'own', 'component': 1, 'member': 'wood'}]
    assert between == []
    other = Connection('other', ('wood', 'clip'), 'screw', (small,))
    _, between = audit.hardware_collisions([own, other], parts)
    assert len(between) == 2
