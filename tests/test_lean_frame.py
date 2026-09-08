"""Single-layer framing geometry and mass, not strength or building approval."""
from collections import Counter

import pytest
import test_mvp_fasteners as hardware
import test_redesign_mvp as layouts

from mini_moonboard import box_frame as b
from mini_moonboard import lean_frame as frame
from mini_moonboard import product_frame as product


@pytest.fixture(scope="module")
def candidate():
    values = frame.parts()
    parts = {p.name: p for p in values}
    assert len(parts) == len(values), "Duplicate part names"
    assert frame.KEY == "lean-38mm-frame"
    return frame, parts


test_purchased_face_datums = layouts.test_purchased_face_thickness_and_fixed_backing_datums
test_official_hold_led_grid = layouts.test_all_official_hold_and_led_axes_remain_open
test_floor_and_connection_graph = layouts.test_four_independent_legs_have_flat_floor_faces_and_connected_inventory
test_body_contacts_and_collisions = layouts.test_body_housings_contact_without_unintended_penetration
test_hardware_body_clearance = hardware.test_heads_washers_nuts_and_unrelated_shafts_clear_all_bodies
test_receivers_and_pilot_paths = hardware.test_axes_have_real_receivers_and_open_pilot_paths
test_hardware_pair_clearance = hardware.test_distinct_fastener_components_do_not_intersect
test_hold_and_led_service = hardware.test_rear_hold_flanges_and_led_reservations_clear_nonface_parts


def test_main_framing_is_one_depth_of_thin_stock_with_only_service_pockets(candidate):
    model, parts = candidate
    assert not any(name.startswith(("wood_vertical_", "wood_principal_",
                                    "wood_beam_", "wood_edge_principal_", "bolted_"))
                   for name in parts)
    assert {name for name in parts if name.startswith("wood_rail_")} == {"wood_rail_lower"}
    raw = {p.name: p for p in model.parts(False)}
    timber = list(model.timber_layout())
    assert len(timber) == len({row[0] for row in timber}) == 14
    assert {row[0] for row in timber} == {name for name in raw if name.startswith("lean_")}
    for name, x0, x1, s0, s1, grain in timber:
        part = raw[name]
        depth = 88.9 if name.startswith("lean_edge_") and name.endswith("_lower") else 139.7
        dimensions = (x1-x0, s1-s0, depth)
        assert min(dimensions) == pytest.approx(38.1), name
        assert (x1-x0 if grain == "S" else s1-s0) == pytest.approx(38.1), name
        assert sorted(part.blank) == pytest.approx(sorted(dimensions)), name
        assert part.laminations == 1, name
        n0, n1 = (38.1, 177.8) if name.startswith("lean_beam_lower_") else (0., depth)
        blank = b.block(x0, x1, s0, s1, n0, n1)
        expected = product._backing_reliefs(b.Part("panel_"+name, blank, part.blank, "test witness"))
        assert part.shape.Volume() == pytest.approx(expected.Volume(), abs=1e-5), name
        assert part.shape.intersect(expected).Volume() == pytest.approx(expected.Volume(), abs=1e-5), name
    assert all(p.shape.isValid() and len(p.shape.Solids()) == 1 for p in parts.values())
    assert not any(name.startswith(("angle_", "transition_")) for name in parts)
    assert all("ML24Z" in p.description for name, p in parts.items() if name.startswith("clip_"))


def test_lower_transition_is_explicit_localized_exception(candidate):
    model, _ = candidate
    raw = {p.name: p for p in model.parts(False)}
    part = raw["wood_rail_lower"]
    assert part.blank == pytest.approx((2438.4, 139.7, 38.1))
    expected = product._backing_reliefs(b.Part("panel_lower_witness",
        b.block(-b.HALF, b.HALF, 0., 139.7, 0., 38.1), part.blank, "test witness"))
    assert part.shape.Volume() == pytest.approx(expected.Volume(), abs=1e-5)
    assert part.shape.intersect(expected).Volume() == pytest.approx(expected.Volume(), abs=1e-5)
    screws = [c for c in model.connections() if c.name.startswith("lean_lower_ledge_")]
    assert len(screws) == 4
    for c in screws:
        assert c.kind == "screw" and c.length == pytest.approx(79.248), c.name
        assert c.members[0] == "wood_rail_lower" and c.members[1].startswith("lean_beam_lower_"), c.name
        assert c.direction.toTuple() == pytest.approx(b.normal().toTuple()), c.name
        assert c.length-38.1 == pytest.approx(41.148), c.name
        assert "unqualified" in c.product_status, c.name


def test_panels_fastened_directly_with_twelve_unique_perimeter_screws_each(candidate):
    model, _ = candidate
    screws = [c for c in model.connections() if c.name.startswith("lean_panel_")]
    expected_panels = {name for name in layouts.FACES if name.startswith("main_")}
    assert Counter(c.members[0] for c in screws) == dict.fromkeys(expected_panels, 12)
    timber = {name: (x0, x1, s0, s1) for name, x0, x1, s0, s1, _ in model.timber_layout()}
    timber["wood_rail_lower"] = (-b.HALF, b.HALF, 0., 139.7)
    origin, normal = b.point(0, 0, 0), b.normal()
    tangent = (b.point(0, 1, 0)-origin).normalized()
    seen = set()
    for c in screws:
        assert c.kind == "screw" and len(c.members) == 2, c.name
        assert c.members[1] in timber, c.name
        assert c.diameter == pytest.approx(4.3942) and c.length == pytest.approx(50.8), c.name
        assert c.direction.toTuple() == pytest.approx(normal.toTuple()), c.name
        assert (c.start-origin).dot(normal) == pytest.approx(-18.25625), c.name
        x, s = c.start.x, (c.start-origin).dot(tangent)
        axis_key = (round(x, 5), round(s, 5))
        assert axis_key not in seen, c.name
        seen.add(axis_key)
        x0, x1, s0, s1 = timber[c.members[1]]
        # Nominal center-to-edge geometric margins only, not product-specific
        # loaded-edge/end-distance or withdrawal qualification.
        assert min(x-x0, x1-x, s-s0, s1-s) >= 19.05-1e-6, c.name
        panel = c.members[0]
        px0, px1 = (-b.HALF, 0.) if panel.endswith("left") else (0., b.HALF)
        ps0, ps1 = (0., b.HALF) if "lower" in panel else (b.HALF, b.LENGTH)
        margins = (x-px0, px1-x, s-ps0, ps1-s)
        assert min(margins) >= 19.05-1e-6, c.name
        assert min(margins) <= 57.15+1e-6, c.name
    assert len(seen) == 48


def test_drilled_volume_mass_materially_lower_than_published_bolted_frame(candidate):
    _, parts = candidate
    # Same declared density basis as the previous actual-CAD mass screen.
    # Excludes holds/fasteners/LEDs/glue; not a weighed assembly or load rating.
    mass = sum(p.shape.Volume()/1e9*(7850 if name.startswith("clip_mvp_") else 600)
               for name, p in parts.items())
    assert mass > 0
    assert mass < .65*280.718, mass
