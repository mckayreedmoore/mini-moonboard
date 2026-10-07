"""Known geometric paths and independently checkable takeoff arithmetic."""

import math

import cadquery as cq
import pytest

from scripts.thin_bolted_access_takeoff import (
    axial_sweep,
    bolt_release_sequence,
    convex_linear_sweep,
    hits,
    metal_gravity_rows,
    pack_purchase,
    stock_takeoff,
)


def test_continuous_axial_sweep_catches_an_obstacle_between_endpoint_poses():
    bolt = cq.Solid.makeCylinder(2, 10)
    obstacle = cq.Solid.makeBox(8, 8, 2, cq.Vector(-4, -4, 24))
    assert not hits(bolt, [("obstacle", "wood", obstacle)])
    assert not hits(bolt.translate((0, 0, 30)), [("obstacle", "wood", obstacle)])
    corridor = axial_sweep(bolt, cq.Vector(0, 0, 1), 30)
    assert corridor.Volume() == pytest.approx(math.pi * 2**2 * 40)
    assert hits(corridor, [("obstacle", "wood", obstacle)])[0]["intersection_mm3"] == pytest.approx(math.pi * 2**2 * 2, abs=1e-6)


def test_annular_sweep_preserves_the_central_hole_on_an_oblique_axis():
    annulus = cq.Solid.makeCylinder(10, 2).cut(cq.Solid.makeCylinder(4, 2))
    shaft = cq.Solid.makeCylinder(3, 30)
    annulus = annulus.rotate((0, 0, 0), (1, 0, 0), 40).translate((5, 9, 7))
    shaft = shaft.rotate((0, 0, 0), (1, 0, 0), 40).translate((5, 9, 7))
    direction = cq.Vector(0, -math.sin(math.radians(40)), math.cos(math.radians(40)))
    corridor = axial_sweep(annulus, direction, 28)
    assert corridor.Volume() == pytest.approx(math.pi * (100 - 16) * 30)
    assert not hits(corridor, [("shaft", "steel", shaft)])


def test_sweep_rejects_nonconstant_section_and_reverse_unit_errors():
    cone = cq.Solid.makeCone(3, 1, 10)
    with pytest.raises(ValueError, match="constant-section"):
        axial_sweep(cone, cq.Vector(0, 0, 1), 15)
    with pytest.raises(ValueError, match="unit"):
        axial_sweep(cone, cq.Vector(0, 0, 2), 15)


def test_polyhedral_panel_corridor_contains_every_intermediate_pose():
    panel = cq.Solid.makeBox(100, 70, 18).rotate((0, 0, 0), (1, 0, 0), 40)
    direction = cq.Vector(0, math.sin(math.radians(40)), -math.cos(math.radians(40)))
    corridor = convex_linear_sweep(panel, direction, 100.)
    assert corridor.Volume() == pytest.approx(100 * 70 * 118)
    for travel in (0, 17, 51, 100):
        assert panel.translate(direction.multiply(travel)).cut(corridor).Volume() < .01
    with pytest.raises(ValueError, match="polyhedral"):
        convex_linear_sweep(cq.Solid.makeCylinder(5, 10), direction, 100.)


def test_cheapest_pack_mixture_can_buy_spares_or_use_singles():
    assert pack_purchase(42, 1.23, 50, 43.98) == {
        "required": 42, "packs": 1, "pack_quantity": 50, "singles": 0,
        "purchased": 50, "spares": 8, "cost_usd": 43.98,
    }
    assert pack_purchase(16, 1.89, 25, 33.7)["cost_usd"] == 30.24
    assert pack_purchase(102, .36, 50, 11.89)["cost_usd"] == 24.5


def test_stock_nesting_keeps_all_members_and_a_positive_kerf_trim_reserve():
    result = stock_takeoff()
    assert result["purchase_quantities"] == [
        {"section": "2x6", "length_ft": 8, "quantity": 6},
        {"section": "2x6", "length_ft": 10, "quantity": 3},
        {"section": "4x6", "length_ft": 8, "quantity": 2},
        {"section": "4x6", "length_ft": 10, "quantity": 2},
    ]
    members = [n for row in result["sticks"] for n in row["members"]]
    assert len(members) == len(set(members)) == 20
    assert min(row["remaining_mm"] for row in result["sticks"]) == pytest.approx(2.648988163343, abs=1e-6)
    assert result["nominal_board_feet"] == 150


def test_two_member_bolt_mass_is_split_and_external_nut_goes_to_the_near_receiver():
    raw = {"left": cq.Solid.makeBox(10, 8, 8, cq.Vector(0, -4, -4)),
           "right": cq.Solid.makeBox(10, 8, 8, cq.Vector(10, -4, -4))}
    shaft = cq.Solid.makeCylinder(2, 20, cq.Vector(), cq.Vector(1, 0, 0))
    nut = cq.Solid.makeCylinder(3, 2, cq.Vector(21, 0, 0), cq.Vector(1, 0, 0))
    frozen = {"installed_axes": [{"id": "test", "receivers": ["left", "right"]}],
              "screw_axes": []}
    result = metal_gravity_rows(frozen, [("test_shaft", "shaft", shaft), ("test_nut", "nut", nut)], raw)
    assert [r["owner"] for r in result] == ["left", "right", "right"]
    assert [r["centroid_xyz_mm"][0] for r in result] == pytest.approx([5, 15, 22])
    assert sum(r["mass_kg"] for r in result) == pytest.approx((math.pi * 4 * 20 + math.pi * 9 * 2) * 7.85e-6)


def test_shared_shaft_dependency_releases_in_order_and_never_waives_wood_or_cycles():
    axes = [{"id": name} for name in ("beam", "post", "wood", "cycle_a", "cycle_b")]
    rows = [{"axis_id": own, "operation": "shaft", "hits": [
        {"obstacle": other, "role": role, "intersection_mm3": 10.}]} for own, other, role in (
            ("post", "beam_shaft", "shaft"), ("wood", "receiver", "timber"),
            ("cycle_a", "cycle_b_shaft", "shaft"), ("cycle_b", "cycle_a_shaft", "shaft"))]
    result = bolt_release_sequence(rows, axes)
    assert result["parallel_clear_stages"] == [["beam"], ["post"]]
    assert result["bolt_stacks_released"] == 2
    assert result["unresolved_axes"] == ["cycle_a", "cycle_b", "wood"]
    assert result["nonmetal_blockers"][0]["obstacle"] == "receiver"
