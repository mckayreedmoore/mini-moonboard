"""Insert layout revisions preserve historical candidates and move complete joints."""
import pytest

from mini_moonboard import horizontal_service_frame as horizontal
from mini_moonboard import round_insert_frame as model
from mini_moonboard import round_panel_layout as historical_layout


def test_attachment_revision_preserves_history_and_upper_axes():
    original = historical_layout.datums()
    rows = {row['name']: row for row in model.attachment_datums()}
    assert horizontal.RAIL_SPANS['lower'] == (1031.1, 1069.2)
    assert historical_layout.KICKER_ROWS == (50.8, 127.)
    assert model.RAIL_SPANS['lower'] == pytest.approx((1115.15, 1153.25))
    for old in original:
        new = rows[old['name']]
        if old['receiver'].startswith('base_rail_service_lower_'):
            aligned = rows['round_panel_lower_left_center_4']
            assert new['s'] == aligned['s'] == pytest.approx(1134.2)
        elif old['panel'].startswith('kicker_'):
            assert new['s'] == (60. if old['name'].endswith('_1') else 140.)
        else:
            assert new == old
    assert historical_layout.datums() == original


def test_lower_clips_and_both_screw_faces_translate_with_receiver():
    original = {c.name: c for c in model.previous.connections()}
    shift = model.lower_rail_translation()
    old_stations = {station[0]: station for station in model.previous.stations()}
    moved = []
    for station in model.stations():
        old = old_stations[station[0]]
        delta = shift if station[4].startswith('base_rail_service_lower_') else shift*0
        assert (station[1]-old[1]-delta).Length < 1.e-7
        assert station[2:] == old[2:]
    for connection in model.connections():
        if isinstance(connection, model.PanelMachineScrew):
            continue
        old = original[connection.name]
        if connection.name.startswith('clip_horizontal_lower_'):
            assert (connection.start-old.start-shift).Length < 1.e-7
            assert connection.direction == old.direction
            assert connection.members == old.members
            moved.append(connection)
        else:
            assert connection is old
    assert len(moved) == 24
    assert sum(c.members[1].startswith('base_rail_service_lower_') for c in moved) == 12


def test_lower_attachment_axes_enter_moved_raw_receivers():
    from mini_moonboard.connection_geometry import material_intervals

    raw = {part.name: part for part in model.uncut_wood_parts()}
    old = {part.name: part for part in model.previous.uncut_wood_parts()}
    shift = model.lower_rail_translation()
    for name, part in raw.items():
        if name.startswith('base_rail_service_lower_'):
            assert (part.shape.Center()-old[name].shape.Center()-shift).Length < 1.e-7
        else:
            assert part is old[name]
    lower = [c for c in model.panel_connections()
             if c.members[1].startswith('base_rail_service_lower_')]
    assert len(lower) == 4
    for connection in lower:
        runs = material_intervals(raw[connection.members[1]].shape,
            connection.start, connection.direction, 0., connection.length)
        assert len(runs) == 1
        assert runs[0][0] == pytest.approx(model.PANEL)
        assert runs[0][1] == pytest.approx(connection.length)
