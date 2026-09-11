"""Current insert export guards and dimension semantics without heavy CAD export."""
import json
from pathlib import Path

import pytest

from mini_moonboard import round_insert_drilling as drilling
from mini_moonboard import round_insert_exports as exports
from mini_moonboard import round_insert_hardware as hardware


def test_export_rejects_old_screw_candidate_without_creating_outputs(tmp_path, monkeypatch):
    wrong = tmp_path/'wrong.json'
    wrong.write_text(json.dumps({'candidate': 'round-bore-service-development', 'source_sha256': {}}))
    monkeypatch.setattr(exports, 'AUDIT', wrong)
    with pytest.raises(ValueError, match='Recompute the candidate geometry audit'):
        exports.export(tmp_path/'export', tmp_path/'viewer')
    assert not (tmp_path/'export').exists()
    assert not (tmp_path/'viewer').exists()
    assert exports.model.KEY == 'round-insert-development'


def test_drilling_rejects_old_screw_audit(tmp_path, monkeypatch):
    wrong = tmp_path/'wrong.json'
    wrong.write_text(json.dumps({'candidate': 'round-bore-service-development', 'source_sha256': {}}))
    monkeypatch.setattr(drilling, 'AUDIT', wrong)
    with pytest.raises(ValueError, match='Recompute the candidate geometry audit'):
        drilling.generate(tmp_path/'sheets')
    assert not (tmp_path/'sheets').exists()


def test_schedule_preserves_axes_and_distinguishes_reservations_from_shop_dimensions():
    panels = drilling.panel_fastening_rows()
    assert {name: len(rows) for name, rows in panels.items()} == {
        'main_lower_left': 12, 'main_lower_right': 12,
        'main_upper_left': 12, 'main_upper_right': 12,
        'kicker_left': 4, 'kicker_right': 4}
    connections = {c.name: c for c in exports.model.panel_connections()}
    for rows in panels.values():
        for row in rows:
            c = connections[row['name']]
            assert row['receiver'] == c.members[1]
            assert row['insert_front_world_mm'] == pytest.approx(c.insert_start.toTuple())
            assert row['panel_clearance_reservation_mm'] < row['manufacturer_pilot_recommendation_mm']
            assert row['manufacturer_pilot_recommendation_mm'] < row['insert_body_nominal_od_mm']
            assert row['pilot_diameter_mm'] is None
            assert row['machining_countersink_angle_deg'] is None
            assert row['machining_countersink_depth_mm'] is None
            assert row['effective_thread_engagement_mm'] is None
            assert not row['qualified_for_machining']
            assert row['insert_recess_mm'] == hardware.INSERT_RECESS_MM
    svg = drilling.panel_fastening_svg('main_lower_left', panels['main_lower_left'])
    assert '80–82 degrees' in svg and 'DEVELOPMENT ONLY' in svg
    assert 'No released countersink angle or depth' in svg
    assert 'do not mirror' in svg


def test_material_classification_distinguishes_zinc_insert_from_steel_hardware():
    assert exports.material_for('insert') == 'die_cast_zinc'
    assert exports.material_for('screw') == exports.material_for('bolt') == exports.material_for('bracket') == 'steel'
    assert exports.material_for('panel') == 'plywood'
    assert exports.material_for('light') == exports.material_for('wire') == 'unknown'
    assert exports.AUDIT == drilling.AUDIT == Path('fea/results/round-insert-audit-v1.json')
