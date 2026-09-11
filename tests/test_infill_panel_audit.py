"""Infill interval and retained-axis checks remain separate from resistance."""
from dataclasses import dataclass, replace
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea import infill_panel_audit as audit


@dataclass
class Screw:
    name: str
    start: cq.Vector
    members: tuple = ('main_lower_left', 'base_principal_test')
    diameter: float = 4.14
    product_status: str = 'provisional'


def fixture():
    model = SimpleNamespace(b=SimpleNamespace(point=lambda x, s, n: cq.Vector(x, s, n)),
                            ADDED_CENTERS={'test': 0}, timber=SimpleNamespace(PanelScrew=Screw))
    first, last = Screw('first', cq.Vector(0, 0, 0)), Screw('last', cq.Vector(0, 300, 0))
    return model, (first, last)


def test_interval_gate_rejects_long_gaps_and_off_line_infill():
    model, old = fixture()
    assert not audit.infill_intervals(model, old, old)[0]['passed']
    middle = Screw('middle', cq.Vector(0, 150, 0))
    row = audit.infill_intervals(model, old, (*old, middle))[0]
    assert row['passed'] and row['maximum_interval_mm'] == 150
    assert not row['strength_qualified']
    assert not audit.infill_intervals(model, old, (*old, replace(middle, start=cq.Vector(1, 150, 0))))[0]['passed']
    assert not audit.infill_intervals(model, old, (*old, replace(middle, start=cq.Vector(0, 140, 0))))[0]['passed']


def test_retained_axis_gate_checks_geometry_not_description():
    _, old = fixture()
    assert audit.connection_unchanged(old[0], replace(old[0], product_status='new explanation'))
    assert not audit.connection_unchanged(old[0], replace(old[0], start=cq.Vector(.01, 0, 0)))
    assert not audit.connection_unchanged(old[0], replace(old[0], diameter=5.))
    body = SimpleNamespace(shape=cq.Solid.makeBox(10, 10, 10), blank=(10, 10, 10), laminations=1)
    raw = {'wood': body}
    assert audit.retained_geometry(raw, raw, old, old)['passed']
    assert not audit.retained_geometry(raw, raw, old, old[:1])['passed']
    assert not audit.retained_geometry(raw, {**raw, 'extra': body}, old, old)['passed']


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_full_infill_keeps_raw_geometry_and_existing_connections(report):
    assert report['all_tested_geometry_gates_passed'], report['geometry_failures']
    assert report['all_tested_product_geometry_gates_passed'], report['product_geometry_failures']
    assert report['retained_geometry']['passed']
    lines = report['principal_screw_intervals']
    assert len(lines) == 12 and len({r['receiver'] for r in lines}) == 6
    assert all(r['passed'] and r['maximum_interval_mm'] <= 150.+1e-6 for r in lines)
    assert all(r['endpoint_shift_mm'] < 1e-6 for r in lines)
    assert all(not r['strength_qualified'] for r in lines)
    for name in ('qualified_for_design', 'structural_analysis_run', 'joint_strength_passed', 'floor_qualified'):
        assert not report[name]


def test_new_drilling_hardware_and_repair_reserves_cover_dynamic_inventory(report):
    count = report['inventory']['panel_kicker_screws']
    assert count > 80
    assert len(report['panel_kicker_screws']) == count
    assert report['future_insert_reserves']['reserve_count'] == count
    assert report['future_insert_reserves']['passes_nominal_reserves']
    assert all(r['passed'] for r in report['receiver_checks'])
    assert all(r['passed'] for r in report['drilled_axis_checks'])
    assert len(report['bolt_component_envelopes']) == 16
    assert all(r['passed'] for r in report['bolt_component_envelopes'])
    assert not report['retained_gussets']['force_reduction_established']
    assert not report['vertical_panel_seam']['strength_qualified']
    assert 'mini_moonboard/infill_panel_frame.py' in report['source_sha256']
    assert 'fea/split_center_audit.py' in report['source_sha256']
