"""Current viewer labels owned panel screws without changing the solved model."""
from mini_moonboard import compact_floor_flush_frame as model
from scripts.floor_flush_exports import viewer_model


def test_hillman_visuals_are_viewer_only():
    actual = {row.name: row for row in model.panel_connections()}
    display = {row.name: row for row in viewer_model.connections()
               if row.name in actual}
    assert len(actual) == len(display) == 66
    assert all(row.length == 63.5 and row.diameter == 4.826
               and 'Hillman 42605' in row.product_status
               for row in display.values())
    assert all(actual[name].length != row.length for name, row in display.items())
    assert sum('Hillman 42605' in row.description
               for row in viewer_model.parts() if row.name.startswith('main_')) == 4
