"""Current panel datum ownership and independent structural bolt coordinates."""
import hashlib
from collections import Counter

import pytest

from mini_moonboard import horizontal_service_drilling as drawing


def test_wiring_reference_change_invalidates_drilling_provenance(tmp_path, monkeypatch):
    (tmp_path/'mini_moonboard').mkdir()
    (tmp_path/'mini_moonboard/example.py').write_text('# unchanged model\n')
    (tmp_path/'docs').mkdir()
    reference = tmp_path/'docs/led-wiring-reference.json'
    reference.write_text('{"route": ["A1", "A2"]}\n')
    monkeypatch.chdir(tmp_path)
    saved = drawing.source_hashes()
    assert saved['docs/led-wiring-reference.json'] == hashlib.sha256(reference.read_bytes()).hexdigest()
    drawing.assert_sources_unchanged(saved)
    reference.write_text('{"route": ["A2", "A1"]}\n')
    with pytest.raises(ValueError, match='Source changed'):
        drawing.assert_sources_unchanged(saved)


def test_front_view_panel_datums_preserve_stock_adaptation_and_led7():
    panels = drawing.panel_rows()
    assert len(panels) == 4
    rows = [row for panel in panels.values() for row in panel['rows']]
    assert Counter(row['kind'] for row in rows) == {'T-nut': 132, 'LED': 132}
    assert len({(row['kind'], row['label']) for row in rows}) == len(rows)
    for name, panel in panels.items():
        assert panel['width_mm'] == panel['height_mm'] == 1219.2
        lower = 'lower' in name
        assert panel['datum_edge'] == ('TOP' if lower else 'BOTTOM')
        assert panel['measurement_direction'] == ('DOWN' if lower else 'UP')
        assert all(0 < row['from_left_mm'] < 1219.2 and 0 < row['from_bottom_mm'] < 1219.2
                   for row in panel['rows'])
        assert {row['label'][0] for row in panel['rows']} == (set('ABCDEF') if name.endswith('left') else set('GHIJK'))
    lower = {(row['kind'], row['label']): row for row in panels['main_lower_left']['rows']}
    upper = {(row['kind'], row['label']): row for row in panels['main_upper_left']['rows']}
    assert lower['T-nut', 'A1']['from_datum_edge_mm'] == 1120.
    assert lower['T-nut', 'A6']['from_datum_edge_mm'] == 120.
    assert lower['LED', 'A1']['from_bottom_mm'] == pytest.approx(19.2)
    assert lower['LED', 'A7']['from_datum_edge_mm'] == 20.
    assert ('LED', 'A7') not in upper
    assert upper['T-nut', 'A7']['from_datum_edge_mm'] == 100.
    assert min(row['from_left_mm'] for row in panels['main_lower_right']['rows']) == pytest.approx(180.8)
    assert 'FRONT / CLIMBING FACE' in drawing.panel_svg('main_lower_left', panels['main_lower_left'])


def test_current_bolt_references_cover_each_axis_in_both_members():
    from mini_moonboard import horizontal_service_frame as model

    data = drawing.bolt_rows(model)
    assert set(data) == {prefix+side for prefix in ('base_side_', 'lumber_leg_') for side in ('left', 'right')}
    rows = [row for record in data.values() for row in record['rows']]
    assert len(rows) == 16
    assert set(Counter(row['connection'] for row in rows).values()) == {2}
    actual = {c.name: c for c in model.connections() if c.name.startswith('lumber_leg_bolt_')}
    assert {row['connection'] for row in rows} == actual.keys()
    for name, record in data.items():
        assert len(record['rows']) == 4
        assert record['width_mm'] == pytest.approx(139.7)
        for row in record['rows']:
            assert name in actual[row['connection']].members
            assert row['axis_world'] == pytest.approx(actual[row['connection']].start.toTuple())
            assert row['diameter_mm'] == 11.1125
            assert sum(row['long_edge_distances_mm']) == pytest.approx(139.7)
            assert row['from_long_edge_mm'] == pytest.approx(row['long_edge_distances_mm'][0])
            assert min(row['end_distances_on_axis_mm']) > 0
        if name.startswith('lumber_leg_'):
            assert all(row['from_top_end_mm'] == pytest.approx(row['end_distances_on_axis_mm'][0])
                       for row in record['rows'])


def test_open_front_groove_datums_reconstruct_actual_cut_bounds():
    from mini_moonboard import horizontal_service_frame as model

    records = {row['name']: row for row in model.cutout_records()}
    pages = drawing.groove_rows(model)
    mapped = {row['name']: (datum, row) for datum in pages.values() for row in datum['rows']}
    assert mapped.keys() == records.keys() and mapped
    for name, (datum, row) in mapped.items():
        original = records[name]
        assert row['entry_face'].startswith('front N=0')
        assert not row['qualified_for_machining']
        assert row['depth_mm'] == original['depth_mm']
        assert row['from_left_start_mm'] >= -1e-5
        assert row['from_left_end_mm'] <= datum['width_mm']+1e-5
        assert row['from_top_start_mm'] >= -1e-5
        assert row['from_top_end_mm'] <= datum['height_mm']+1e-5
        assert datum['left_edge_world_x_mm']+row['from_left_start_mm'] == pytest.approx(original['x0_mm'])
        assert datum['left_edge_world_x_mm']+row['from_left_end_mm'] == pytest.approx(original['x1_mm'])
        assert datum['top_edge_station_mm']-row['from_top_start_mm'] == pytest.approx(original['s1_mm'])
        assert datum['top_edge_station_mm']-row['from_top_end_mm'] == pytest.approx(original['s0_mm'])
    first = next(iter(pages.values()))
    svg = drawing.groove_svg('example', {**first, 'rows': first['rows'][:10]})
    assert 'Open grooves, NOT closed bores' in svg
    assert 'NOT RELEASED FOR CONSTRUCTION' in svg
