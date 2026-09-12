"""Reject stale evidence before either exporter creates candidate artifacts."""
import json

import pytest

from mini_moonboard import round_structural_drilling as drawing
from mini_moonboard import round_structural_exports as exports


@pytest.mark.parametrize('consumer', [drawing, exports])
@pytest.mark.parametrize('defect', ['candidate', 'empty', 'stale'])
def test_invalid_audit_prevents_output_creation(tmp_path, monkeypatch, consumer, defect):
    source = tmp_path/'source.py'
    source.write_text('original')
    report = {'candidate': consumer.model.KEY,
              'source_sha256': {str(source): consumer.digest(source)}}
    if defect == 'candidate':
        report['candidate'] = 'round-insert-development'
    elif defect == 'empty':
        report['source_sha256'] = {}
    else:
        source.write_text('modified geometry')
    audit = tmp_path/'audit.json'
    audit.write_text(json.dumps(report))
    monkeypatch.setattr(consumer, 'AUDIT', audit)
    output = tmp_path/'output'
    with pytest.raises(ValueError, match='Recompute the candidate geometry audit'):
        if consumer is drawing:
            consumer.generate(output)
        else:
            consumer.export(output, tmp_path/'viewer')
    assert not output.exists()
    assert not (tmp_path/'viewer').exists()


def test_fastening_drawings_follow_current_candidate_datums():
    panels = drawing.panel_fastening_rows()
    assert sum(map(len, panels.values())) == 56
    for panel, rows in panels.items():
        assert len(rows) == (4 if panel.startswith('kicker_') else 12)
        assert all(row['pilot_diameter_mm'] is None for row in rows)
        assert all(not row['future_insert_pilot_cut'] for row in rows)
        svg = drawing.panel_fastening_svg(panel, rows)
        assert 'SPAX XFT08P-2000' in svg
        assert 'no inserts installed or future insert pilots cut' in svg
    lower = panels['main_lower_left']
    upper = panels['main_upper_right']
    assert {row['from_bottom_mm'] for row in lower if row['role'] == 'service'} == {1134.2}
    assert [row['from_bottom_mm'] for row in upper if row['role'] == 'service'] == pytest.approx([59.05, 59.05])
    center = next(row for row in upper if row['name'] == 'round_panel_upper_right_center_4')
    assert center['from_bottom_mm'] == pytest.approx(1134.2)


@pytest.mark.parametrize('diameter', [25.4, 38.1])
def test_passage_sheet_uses_each_bores_actual_diameter(diameter):
    row = {'name': 'bore_fixture', 'member': 'receiver', 'datums': ['A1', 'A2'],
           'diameter_mm': diameter, 'entry_face_description': 'Entry face',
           'through_wood_length_mm': 38.1, 'width_datum_description': 'Left edge',
           'center_from_width_edges_mm': [100., 100.],
           'center_from_front_rear_faces_mm': [30., 109.7],
           'entry_world_mm': [0., 0., 0.], 'exit_world_mm': [38.1, 0., 0.],
           'drilling_direction_world': [1., 0., 0.], 'width_axis_world': [0., 1., 0.],
           'local_ligaments_width_low_high_front_rear_mm': [100.-diameter/2]*4}
    svg = drawing.previous.passage_svg(row)
    assert f'Circular diameter: {diameter:.3f} mm' in svg
    assert 'NOT RELEASED FOR CONSTRUCTION' in svg
