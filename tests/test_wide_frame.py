"""Wider receiver geometry checks; no resistance or bearing qualification."""
import cadquery as cq
import pytest
import test_mvp_fasteners as fastener_checks
import test_redesign_mvp as layout_checks

from mini_moonboard import insert_frame as previous
from mini_moonboard import wide_frame as model
from mini_moonboard.connection_geometry import material_intervals


def test_explicit_connection_delta():
    current = {c.name: c for c in model.connections()}
    assert len(current) == 188
    assert len(model.panel_connections()) == 56
    assert len(tuple(model.stations())) == 18
    assert sum(n.startswith("clip_") for n in current) == 108
    for old in previous.connections():
        if old.name.startswith("clip_"):
            continue
        new = current[old.name]
        side = "left" if "left" in old.name else "right"
        movable = abs(old.start.x-(-57.15 if side == "left" else 19.05)) < 1e-6 and (
            isinstance(old, model.PanelMachineScrew) or old.name.startswith("timber_backing_bolt_"))
        if not movable:
            assert new == old
        else:
            assert new.start.x == pytest.approx(model.CENTERS[side])
            assert (new.start.y, new.start.z) == (old.start.y, old.start.z)
            assert (new.direction, new.length, new.diameter) == (old.direction, old.length, old.diameter)


def test_backing_bolt_edges_and_stock_plan():
    for c in model.connections():
        if not c.name.startswith("timber_backing_bolt_"):
            continue
        side = "left" if c.name.endswith("left") else "right"
        x0, x1 = model.UPRIGHTS[side]
        assert min(c.start.x-x0, x1-c.start.x) == pytest.approx(44.45)
        assert min(c.start.x-x0, x1-c.start.x) >= 4*c.diameter
        # Backing grain runs X: its reversible transverse S edges also clear 4D.
        assert min(40., 88.9-40.) >= 4*c.diameter
    assert model.POST_Y["front"][0]-model.POST_Y["rear"][1] == pytest.approx(6.35)


@pytest.fixture(scope="module")
def candidate():
    return {p.name: p for p in model.parts()}


def test_inventory_and_validity(candidate):
    assert len(candidate) == 103
    assert sum(n.startswith("insert_") for n in candidate) == 56
    assert sum(n.startswith("base_post_center_") for n in candidate) == 4
    for p in candidate.values():
        assert p.shape.isValid() and p.shape.Volume() > 0, p.name


def test_full_width_post_support_and_unchanged_header():
    raw = {p.name: p for p in model.wood_parts(False)}
    header = raw["base_header"].shape
    for side, (x0, x1) in model.UPRIGHTS.items():
        for end, (y0, y1) in model.POST_Y.items():
            post = raw[f"base_post_center_{side}_{end}"].shape
            bb = post.BoundingBox()
            assert (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmax) == pytest.approx(
                (x0, x1, y0, y1, 186.9))
            assert post.translate((0, 0, .01)).intersect(header).Volume() == pytest.approx(
                88.9*139.7*.01, abs=1e-5)
        principal = raw[f"base_principal_{side}"]
        offcuts = [raw[f"base_post_center_{side}_{end}"] for end in model.POST_Y]
        assert principal.blank[0]+sum(p.blank[0] for p in offcuts)+4*3.2 < 3048.


def test_all_connector_screws_enter_declared_wood_receivers(candidate):
    raw = {p.name: p for p in model.wood_parts(True)}
    screws = [c for c in model.connections() if c.name.startswith("clip_")]
    assert len(screws) == 108
    for c in screws:
        receiver = raw[c.members[1]].shape
        runs = material_intervals(receiver, c.start, c.direction, 0., c.length)
        assert len(runs) == 1, c.name
        assert runs[0] == pytest.approx((model.hardware.ML["thickness"], c.length), abs=1e-5), c.name
        pilot = cq.Solid.makeCylinder(.25, c.length, c.start, c.direction)
        assert pilot.intersect(candidate[c.members[1]].shape).Volume() < .01, c.name


def test_services_and_insert_material(candidate):
    raw = {p.name: p for p in model.wood_parts(True)}
    for p in raw.values():
        if not p.name.startswith(("base_principal_", "base_rail_mid_")):
            continue
        for cutter in model.timber.service_envelopes():
            assert p.shape.intersect(cutter).Volume() < .01, p.name
    for c in model.panel_connections():
        radius = (model.INSERT["nominal_outer_diameter"]+
                  model.INSERT["drawing_general_tolerance_plus_minus"])/2
        envelope = cq.Solid.makeCylinder(radius, 17., c.insert_start, c.direction)
        assert envelope.cut(raw[c.members[1]].shape).Volume() < .01, c.name


def test_collision_checks(candidate):
    wrapped = (model, candidate)
    fastener_checks.test_heads_washers_nuts_and_unrelated_shafts_clear_all_bodies(wrapped)
    fastener_checks.test_distinct_fastener_components_do_not_intersect(wrapped)
    layout_checks.test_body_housings_contact_without_unintended_penetration(wrapped)
    for c in model.panel_connections():
        for component in c.components():
            cb = component.BoundingBox()
            for p in candidate.values():
                pb = p.shape.BoundingBox()
                if any(getattr(cb, a+"max") < getattr(pb, a+"min") or
                       getattr(pb, a+"max") < getattr(cb, a+"min") for a in "xyz"):
                    continue
                assert component.intersect(p.shape).Volume() < .01, (c.name, p.name)


def test_hardware_does_not_consume_reserved_hold_led_access():
    reservations = [(s, s.BoundingBox()) for s in model.timber.service_envelopes()]
    for c in model.connections():
        components = list(c.components())
        if isinstance(c, model.PanelMachineScrew):
            components.append(c.insert_shape())
        for component in components:
            bounds = component.BoundingBox()
            for reservation, other in reservations:
                if any(getattr(bounds, a+"max") < getattr(other, a+"min") or
                       getattr(other, a+"max") < getattr(bounds, a+"min") for a in "xyz"):
                    continue
                assert component.intersect(reservation).Volume() < .01, c.name
