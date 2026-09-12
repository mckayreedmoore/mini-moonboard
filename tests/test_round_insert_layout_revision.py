"""Insert layout revisions preserve historical candidates and move complete joints."""
import pytest

from mini_moonboard import horizontal_service_frame as horizontal
from mini_moonboard import round_insert_frame as model
from mini_moonboard import round_panel_layout as historical_layout


def test_attachment_revision_preserves_history_and_upper_principal_axes():
    original = historical_layout.datums()
    rows = {row['name']: row for row in model.attachment_datums()}
    assert horizontal.RAIL_SPANS['lower'] == (1031.1, 1069.2)
    assert horizontal.RAIL_SPANS['upper'] == (1219.2, 1257.3)
    assert historical_layout.KICKER_ROWS == (50.8, 127.)
    assert model.RAIL_SPANS['lower'] == pytest.approx((1115.15, 1153.25))
    assert model.RAIL_SPANS['upper'] == pytest.approx((1259.2, 1297.3))
    for old in original:
        new = rows[old['name']]
        if old['receiver'].startswith('base_rail_service_lower_'):
            aligned = rows['round_panel_lower_left_center_4']
            assert new['s'] == aligned['s'] == pytest.approx(1134.2)
        elif old['receiver'].startswith('base_rail_service_upper_'):
            aligned = rows['round_panel_upper_left_center_1']
            assert new['s'] == aligned['s'] == pytest.approx(1278.25)
            assert new['s']-old['s'] == pytest.approx(40.)
        elif old['panel'].startswith('kicker_'):
            assert new['s'] == (60. if old['name'].endswith('_1') else 140.)
        else:
            assert new == old
    for side in ('left', 'right'):
        name = f'round_panel_upper_{side}_center_4'
        assert rows[name] == next(row for row in original if row['name'] == name)
    assert historical_layout.datums() == original


def test_service_clips_and_both_screw_faces_translate_with_receivers():
    original = {c.name: c for c in model.previous.connections()}
    shifts = {level: model.rail_translation(level) for level in ('lower', 'upper')}
    assert (model.lower_rail_translation()-shifts['lower']).Length < 1.e-7
    old_stations = {station[0]: station for station in model.previous.stations()}
    moved = {level: [] for level in shifts}
    for station in model.stations():
        old = old_stations[station[0]]
        delta = next((shift for level, shift in shifts.items()
                      if station[4].startswith(f'base_rail_service_{level}_')),
                     shifts['lower']*0)
        assert (station[1]-old[1]-delta).Length < 1.e-7
        assert station[2:] == old[2:]
    for connection in model.connections():
        if isinstance(connection, model.PanelMachineScrew):
            continue
        old = original[connection.name]
        level = next((level for level in shifts
                      if connection.name.startswith(f'clip_horizontal_{level}_')), None)
        if level is not None:
            assert (connection.start-old.start-shifts[level]).Length < 1.e-7
            assert connection.direction == old.direction
            assert connection.members == old.members
            moved[level].append(connection)
        else:
            assert connection is old
    for level, connections in moved.items():
        assert len(connections) == 24
        assert sum(c.members[1].startswith(f'base_rail_service_{level}_')
                   for c in connections) == 12


def test_service_attachment_axes_enter_moved_raw_receivers():
    from mini_moonboard.connection_geometry import material_intervals

    raw = {part.name: part for part in model.uncut_wood_parts()}
    old = {part.name: part for part in model.previous.uncut_wood_parts()}
    shifts = {level: model.rail_translation(level) for level in ('lower', 'upper')}
    for name, part in raw.items():
        level = next((level for level in shifts
                      if name.startswith(f'base_rail_service_{level}_')), None)
        if level is not None:
            assert (part.shape.Center()-old[name].shape.Center()-shifts[level]).Length < 1.e-7
        else:
            assert part is old[name]
    for level in shifts:
        attachments = [c for c in model.panel_connections()
                       if c.members[1].startswith(f'base_rail_service_{level}_')]
        assert len(attachments) == 4
        for connection in attachments:
            runs = material_intervals(raw[connection.members[1]].shape,
                connection.start, connection.direction, 0., connection.length)
            assert len(runs) == 1
            assert runs[0][0] == pytest.approx(model.PANEL)
            assert runs[0][1] == pytest.approx(connection.length)
