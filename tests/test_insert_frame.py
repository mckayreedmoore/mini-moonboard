"""Panel insert geometry checks, not wood-thread or panel strength tests."""
import math

import cadquery as cq
import pytest
import test_mvp_fasteners as fastener_checks
import test_redesign_mvp as layout_checks

from mini_moonboard import insert_frame as model
from mini_moonboard import timber_frame as baseline
from mini_moonboard.connection_geometry import material_intervals


def test_preserved_connections_and_replaced_panel_inventory():
    current = {c.name: c for c in model.connections()}
    assert len(current) == 176 and len(model.panel_connections()) == 56
    for old in baseline.connections():
        new = current[old.name]
        if isinstance(old, baseline.PanelScrew):
            assert isinstance(new, model.PanelMachineScrew)
            assert new.start == old.start and new.direction == old.direction
            assert new.members == old.members and new.kind == "screw"
            assert new.length == 31.75 and new.diameter == 6.35
        else:
            assert new == old


def test_nominal_reach_is_not_effective_engagement():
    insert, screw, assumptions = model.INSERT, model.SCREW, model.ASSUMPTIONS
    assert insert["full_internal_thread_length"] is None
    assert assumptions["effective_engagement"] is None
    assert screw["nominal_overall_length"]-model.PANEL == pytest.approx(13.49375)
    assert screw["minimum_overall_length"]-model.PANEL == pytest.approx(11.96975)
    assert max(screw["nominal_overall_length"]-model.PANEL,
               insert["nominal_length"]+insert["drawing_general_tolerance_plus_minus"]) < 17.


@pytest.fixture(scope="module")
def candidate():
    return {p.name: p for p in model.parts()}


def test_insert_receivers_and_service_reservations(candidate):
    raw = {p.name: p for p in baseline.wood_parts(True)}
    for c in model.panel_connections():
        receiver = raw[c.members[1]].shape
        runs = material_intervals(receiver, c.insert_start, c.direction, 0., 17.)
        assert len(runs) == 1 and runs[0] == pytest.approx((0., 17.), abs=1e-5), c.name
        radius = (model.INSERT["nominal_outer_diameter"]+
                  model.INSERT["drawing_general_tolerance_plus_minus"])/2
        envelope = cq.Solid.makeCylinder(radius, 17., c.insert_start, c.direction)
        # The full envelope must sit in sound modeled receiver material, not a
        # service pocket, housing or neighboring member. This does not qualify edges.
        assert envelope.cut(receiver).Volume() < .01, c.name
        insert = candidate["insert_"+c.name].shape
        for component in c.components():
            assert component.intersect(insert).Volume() < .01, c.name
        assert insert.intersect(candidate[c.members[1]].shape).Volume() < .01, c.name


def test_insert_head_and_shaft_envelopes_clear_all_bodies(candidate):
    for c in model.panel_connections():
        for component in c.components():
            cb = component.BoundingBox()
            for part in candidate.values():
                pb = part.shape.BoundingBox()
                if any(getattr(cb, a+"max") < getattr(pb, a+"min") or
                       getattr(pb, a+"max") < getattr(cb, a+"min") for a in "xyz"):
                    continue
                volume = component.intersect(part.shape).Volume()
                assert math.isfinite(volume) and volume < .01, (c.name, part.name, volume)


def test_body_inventory_and_validity(candidate):
    assert len(candidate) == 99
    assert sum(name.startswith("insert_") for name in candidate) == 56
    for part in candidate.values():
        assert part.shape.isValid() and part.shape.Volume() > 0., part.name


def test_all_hardware_pairs_and_unrelated_bodies(candidate):
    wrapped = (model, candidate)
    fastener_checks.test_heads_washers_nuts_and_unrelated_shafts_clear_all_bodies(wrapped)
    fastener_checks.test_distinct_fastener_components_do_not_intersect(wrapped)
    layout_checks.test_body_housings_contact_without_unintended_penetration(wrapped)
