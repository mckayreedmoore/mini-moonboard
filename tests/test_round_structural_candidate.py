"""Current screw candidate preserves datums and selects bores by stock section."""
from types import SimpleNamespace

import pytest

from mini_moonboard import round_insert_frame as inserts
from mini_moonboard import round_service_frame as historical
from mini_moonboard import round_structural_frame as model
from mini_moonboard import round_structural_wiring as wiring


@pytest.mark.parametrize(('dimensions', 'diameter'), [
    ((2000., 139.7, 38.1), 38.1),
    ((38.1, 139.7, 900.), 38.1),
    ((2000., 235., 38.1), 25.4),
    ((2000., 139.7, 63.5), 25.4),
])
def test_passage_size_follows_actual_stock_section(dimensions, diameter):
    assert wiring.bore_diameter_mm(SimpleNamespace(blank=dimensions)) == diameter


def test_structural_screws_keep_latest_axes_and_historical_product():
    screws = model.panel_connections()
    originals = {c.name: c for c in historical.connections()
                 if isinstance(c, historical.CountersunkPanelScrew)}
    latest = {c.name: c for c in inserts.panel_connections()}
    assert len(screws) == 56
    for c in screws:
        assert isinstance(c, historical.CountersunkPanelScrew)
        if '_edge_' in c.name or '_service_' in c.name:
            x = model.INNER_X[int(c.name.rsplit('_', 1)[1])-1]
            assert abs(c.start.x) == pytest.approx(x)
            assert c.start.y == pytest.approx(latest[c.name].start.y)
            assert c.start.z == pytest.approx(latest[c.name].start.z)
        else:
            assert c.start.toTuple() == pytest.approx(latest[c.name].start.toTuple())
        assert c.direction.toTuple() == pytest.approx(latest[c.name].direction.toTuple())
        assert c.length == originals[c.name].length
        assert c.diameter == originals[c.name].diameter
    assert not any(isinstance(c, inserts.PanelMachineScrew) for c in model.connections())
    assert len([c for c in model.connections() if c.name.startswith('lumber_leg_bolt_')]) == 8


def test_candidate_does_not_mutate_historical_wiring_or_layout():
    assert wiring.previous.BORE_DIAMETER_MM == 25.4
    assert model.SERVICE_S == {'lower': 1134.2, 'upper': 1278.25}
    assert model.KICKER_ROWS == (60., 140.)
    assert model.INNER_X == pytest.approx((435.075, 835.075))
    for current, old in zip(model.attachment_datums(), inserts.attachment_datums(), strict=True):
        assert {k: v for k, v in current.items() if k != 'x'} == {
            k: v for k, v in old.items() if k != 'x'}
    assert historical.RAIL_SPANS['upper'] != model.RAIL_SPANS['upper']


def test_all_screw_tips_remain_inside_net_receivers():
    from fea.round_structural_audit import screw_tip_checks

    receivers = {p.name: p for p in model.wood_parts()}
    rows = screw_tip_checks(receivers, model.connections())
    assert len(rows) == 200
    assert all(row['passed'] for row in rows), [r for r in rows if not r['passed']]
