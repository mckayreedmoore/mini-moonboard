"""Square-cut alternatives: reuse full nominal MVP checks, not capacity gates."""
import math
from importlib import import_module

import cadquery as cq
import pytest
import test_mvp_fasteners as hardware
import test_redesign_mvp as layouts

from mini_moonboard import box_frame as b
from mini_moonboard import product_frame as product
from mini_moonboard.box_exports import exact_bounds


@pytest.fixture(scope="module", params=[
    ("easy_frame", "square-cut-bracket"),
    ("easy_blocks", "square-cut-wood-blocks"),
])
def candidate(request):
    module, key = request.param
    frame = import_module("mini_moonboard."+module)
    assert frame.KEY == key
    values = frame.parts()
    parts = {p.name: p for p in values}
    assert len(parts) == len(values), "Duplicate body identifiers"
    return frame, parts


# Pytest supplies this module's candidate fixture to these unchanged checks.
test_purchased_face_datums = layouts.test_purchased_face_thickness_and_fixed_backing_datums
test_official_hold_led_grid = layouts.test_all_official_hold_and_led_axes_remain_open
test_floor_and_connection_graph = layouts.test_four_independent_legs_have_flat_floor_faces_and_connected_inventory
test_body_contacts_and_collisions = layouts.test_body_housings_contact_without_unintended_penetration
test_hardware_body_clearance = hardware.test_heads_washers_nuts_and_unrelated_shafts_clear_all_bodies
test_receivers_and_pilot_paths = hardware.test_axes_have_real_receivers_and_open_pilot_paths
test_hardware_pair_clearance = hardware.test_distinct_fastener_components_do_not_intersect
test_hold_and_led_service = hardware.test_rear_hold_flanges_and_led_reservations_clear_nonface_parts


def test_valid_inventory_without_custom_steel(candidate):
    frame, parts = candidate
    assert layouts.FACES <= parts.keys()
    for name, part in parts.items():
        assert part.shape.isValid() and len(part.shape.Solids()) == 1, name
        assert math.isfinite(part.shape.Volume()) and part.shape.Volume() > 0, name
        assert all(math.isfinite(v) and v > 0 for v in part.blank), name
        assert not name.startswith(("angle_", "transition_")), name
        if name.startswith("clip_"):
            assert frame.KEY == "square-cut-bracket", name
            assert "ML24Z" in part.description, name


def test_flat_ledges_are_square_cut_stock_with_only_service_reliefs(candidate):
    frame, _ = candidate
    easy = import_module("mini_moonboard.easy_frame")
    raw = {p.name: p for p in frame.parts(False)}
    ledger_layout = list(easy.ledger_layout())
    names = {row[0] for row in ledger_layout}
    assert len(names) == len(ledger_layout) == 11
    assert names == {name for name in raw if name.startswith(("wood_rail_", "wood_vertical_"))}
    for name, x0, x1, s0, s1 in ledger_layout:
        part = raw[name]
        blank = b.block(x0, x1, s0, s1, 0., 38.1)
        witness = b.Part("panel_"+name, blank, part.blank, "test service-only stock")
        expected = product._backing_reliefs(witness)
        assert sorted(part.blank) == pytest.approx(sorted((x1-x0, s1-s0, 38.1))), name
        assert part.shape.Volume() == pytest.approx(expected.Volume(), abs=1e-5), name
        assert part.shape.intersect(expected).Volume() == pytest.approx(expected.Volume(), abs=1e-5), name
    verticals = [row for row in ledger_layout if row[0].startswith("wood_vertical_")]
    assert len(verticals) == 8
    assert all(row[2]-row[1] == pytest.approx(88.9) for row in verticals)
    assert all(row[4]-row[3] == pytest.approx(verticals[0][4]-verticals[0][3]) for row in verticals)


def test_other_new_timbers_are_full_rectangular_stock_not_hidden_housings(candidate):
    frame, _ = candidate
    origin = b.point(0, 0, 0)
    tangent = (b.point(0, 1, 0)-origin).normalized()
    checked = []
    for part in frame.parts(False):
        if not part.name.startswith(("wood_", "easy_lower_corner_")) or part.name.startswith(("wood_rail_", "wood_vertical_")):
            continue
        assert len(part.shape.Faces()) == 6, part.name
        assert all(f.geomType() == "PLANE" for f in part.shape.Faces()), part.name
        if part.name.startswith("wood_kicker_block_"):
            bounds = exact_bounds(part.shape)
            expected = cq.Solid.makeBox(bounds.xlen, bounds.ylen, bounds.zlen,
                cq.Vector(bounds.xmin, bounds.ymin, bounds.zmin))
            dimensions = (bounds.xlen, bounds.ylen, bounds.zlen)
        else:
            positions = [(v.Center().x, (v.Center()-origin).dot(tangent),
                          (v.Center()-origin).dot(b.normal())) for v in part.shape.Vertices()]
            lower = [min(p[i] for p in positions) for i in range(3)]
            upper = [max(p[i] for p in positions) for i in range(3)]
            expected = b.block(lower[0], upper[0], lower[1], upper[1], lower[2], upper[2])
            dimensions = [upper[i]-lower[i] for i in range(3)]
        assert sorted(part.blank) == pytest.approx(sorted(dimensions), abs=1e-6), part.name
        assert part.shape.Volume() == pytest.approx(expected.Volume(), abs=1e-5), part.name
        assert part.shape.intersect(expected).Volume() == pytest.approx(expected.Volume(), abs=1e-5), part.name
        checked.append(part.name)
    assert {"wood_principal_left", "wood_principal_right"} <= set(checked)


def test_principal_ledge_screws_are_short_and_installed_from_open_front(candidate):
    frame, _ = candidate
    connections = frame.connections()
    assert not any(c.name.startswith("wood_principal_ledge_") for c in connections)
    assert not any(c.name.startswith("wood_deep_lap_") for c in connections)
    screws = [c for c in connections if c.name.startswith("easy_principal_ledge_")]
    assert len(screws) == 8
    origin = b.point(0, 0, 0)
    for c in screws:
        assert c.kind == "screw" and c.length == pytest.approx(63.5), c.name
        assert c.direction.toTuple() == pytest.approx(b.normal().toTuple()), c.name
        assert (c.start-origin).dot(b.normal()) == pytest.approx(0., abs=1e-7), c.name
        assert c.members[0].startswith("wood_vertical_center_"), c.name
        assert c.members[-1].startswith("wood_principal_"), c.name
        head = c.components()[1]
        depths = [(v.Center()-origin).dot(b.normal()) for v in head.Vertices()]
        assert min(depths) == pytest.approx(0., abs=1e-7), c.name
        assert max(depths) <= 5.+1e-7, c.name
    # These are accessible before skins, not a claim of installed tool access.


def test_assumed_straight_front_driver_clears_framing_before_skins_and_legs(candidate):
    frame, parts = candidate
    origin, normal = b.point(0, 0, 0), b.normal()
    screws = [c for c in frame.connections() if c.name.startswith("easy_")
              and c.kind == "screw" and (c.direction-normal).Length < 1e-7
              and abs((c.start-origin).dot(normal)) < 1e-7]
    assert len(screws) == 20, "Expected all twenty front-driven easy-frame screws"
    framing = {name: p for name, p in parts.items()
               if name not in layouts.FACES and not name.startswith("leg_")}
    # Assumed Ø25.4 x100 mm straight approach, not a measured driver/tool body
    # or a swept insertion path. Skins and leg plies are absent at this stage.
    drivers = {c.name: cq.Solid.makeCylinder(12.7, 100., c.start-normal*100., normal)
               for c in screws}
    bounds, findings = {}, []
    for name, driver in drivers.items():
        for member, part in framing.items():
            volume = hardware.positive_overlap(driver, part.shape, bounds)
            if volume > hardware.THRESHOLD_MM3:
                findings.append((name, member, volume))
    assert findings == [], findings
