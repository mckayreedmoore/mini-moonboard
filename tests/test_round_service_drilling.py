"""Round passage dimensions use physical entry faces and independent axes."""
from types import SimpleNamespace

import pytest

from mini_moonboard import box_frame as b
from mini_moonboard import round_service_drilling as drawing


def fixture(axis='S', depth=30.):
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    if axis == 'S':
        part = b.Part('base_rail_service_lower_left', b.block(-50., 50., 0., 38.1, 0., 139.7),
                      (100., 139.7, 38.1), 'Synthetic rail', 1)
        center, direction, length = (10., 19.05, depth), tangent, 40.1
    else:
        part = b.Part('base_principal_center_left', b.block(-19.05, 19.05, 0., 2000., 0., 139.7),
                      (2000., 139.7, 38.1), 'Synthetic principal', 1)
        center, direction, length = (0., 500., depth), drawing.cq.Vector(1., 0., 0.), 40.1
    record = {'name': 'test_bore', 'member': part.name, 'axis_local': axis,
              'direction': list(direction.toTuple()), 'diameter_mm': 25.4, 'length_mm': length,
              **dict(zip(('center_x_mm', 'center_s_mm', 'center_n_mm'), center, strict=True)),
              'datums': ['A1', 'A2'], 'qualified_for_machining': False}
    return SimpleNamespace(b=b, uncut_wood_parts=lambda: (part,), bore_records=lambda: (record,))


@pytest.mark.parametrize('axis', ['S', 'X'])
def test_actual_entry_exit_and_closed_circle_ligaments(axis):
    row, = drawing.passage_rows(fixture(axis))
    assert row['through_wood_length_mm'] == pytest.approx(38.1)
    assert row['center_from_front_rear_faces_mm'] == pytest.approx([30., 109.7])
    assert row['local_ligaments_width_low_high_front_rear_mm'][2:] == pytest.approx([17.3, 97.])
    entry, exit = (drawing.cq.Vector(*row[key]) for key in ('entry_world_mm', 'exit_world_mm'))
    assert (exit-entry).Length == pytest.approx(38.1)
    if axis == 'S':
        assert row['center_from_width_edges_mm'] == pytest.approx([60., 40.])
        assert entry.toTuple() == pytest.approx(b.point(10., 0., 30.).toTuple())
    else:
        assert row['center_from_width_edges_mm'] == pytest.approx([500., 1500.])
        assert entry.toTuple() == pytest.approx(b.point(-19.05, 500., 30.).toTuple())
    svg = drawing.passage_svg(row)
    assert 'Circular diameter: 25.400 mm' in svg
    assert 'fit panels' in svg.lower()
    assert 'NOT RELEASED FOR CONSTRUCTION' in svg
    assert not row['qualified_for_machining']


def test_passage_open_to_front_face_is_rejected():
    with pytest.raises(ValueError, match='open to a long face'):
        drawing.passage_rows(fixture(depth=10.))


def test_source_closure_includes_both_wiring_references():
    hashes = drawing.source_hashes()
    assert {'docs/round-service-wiring-reference.json', 'docs/led-wiring-reference.json',
            'docs/ml24z-reference.json', 'docs/panel-insert-reference.json',
            'mini_moonboard/round_service_drilling.py'} <= hashes.keys()


def test_fastening_sheets_use_panel_local_axes_and_preserve_machining_limits():
    panels = drawing.panel_fastening_rows()
    assert len(panels) == 6
    assert sum(map(len, panels.values())) == 56
    for name, rows in panels.items():
        assert len(rows) == (4 if name.startswith('kicker_') else 12)
        assert all(0 < row['from_left_mm'] < 1219.2 for row in rows)
        assert all(row['pilot_diameter_mm'] is None for row in rows)
        svg = drawing.panel_fastening_svg(name, rows)
        assert '90-degree' in svg and 'NOT RELEASED FOR CONSTRUCTION' in svg
        assert 'countersink machining depth is specified' in svg


def test_kicker_hold_sheets_preserve_actual_front_face_datums():
    panels = drawing.kicker_hold_rows()
    assert set(panels) == {'kicker_left', 'kicker_right'}
    assert [r['label'] for r in panels['kicker_left']['rows']] == ['1', '2', '3', '4', '5']
    assert [r['label'] for r in panels['kicker_right']['rows']] == ['6', '7', '8', '9', '10']
    for column, panel in enumerate(panels.values()):
        assert (panel['width_mm'], panel['height_mm']) == (1219.2, 225.)
        for row in panel['rows']:
            x, z = drawing.previous.grid.kicker_foothold_datums()[row['label']]
            assert row['from_left_mm'] == pytest.approx(x-column*1219.2)
            assert row['from_bottom_mm'] == 225.+z == 150.
            assert row['from_top_mm'] == 75.
            assert row['diameter_mm'] == 11.1125
        svg = drawing.kicker_hold_svg('kicker', panel)
        assert 'FRONT / CLIMBING FACE' in svg and 'rear (-Y)' in svg
        assert 'NOT RELEASED FOR CONSTRUCTION' in svg
