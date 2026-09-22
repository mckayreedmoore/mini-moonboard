"""Geometry-only center-principal viewer revision; never a drilling release."""

import cadquery as cq
import pytest

from scripts import owner_barrel_center_layout as center
from scripts import owner_layout_protected as protected


@pytest.fixture(scope="module")
def layouts():
    wood = center._wood()[1]
    return wood, center.build_layout(wood), center.build_revised_layout(wood)


def test_default_center_builder_is_unchanged_and_other_four_duties_are_preserved(
    layouts,
):
    wood, original, revised = layouts
    assert original["diagnostics"]["source_id"] == center.SOURCE_ID
    assert revised["diagnostics"]["source_id"] == center.REVISED_SOURCE_ID
    assert set(revised["stations"]) == set(center.STATIONS)
    assert all(row["disposition"] == "REVISE" for row in revised["stations"].values())
    assert all(row["mode"] == "direct" for row in revised["stations"].values())
    assert all(
        "compact_alternate_block" not in row for row in revised["stations"].values()
    )
    for side, target in (("left", -180.0), ("right", 180.0)):
        box = wood[f"base_post_center_{side}"].BoundingBox()
        assert (box.xmin + box.xmax) / 2 == pytest.approx(target)
    for station in center.STATIONS:
        if station.startswith("clip_split_base_center_"):
            assert original["stations"][station]["disposition"] == "REVISE"
            continue
        before, after = original["stations"][station], revised["stations"][station]
        for role in ("bolts", "barrels", "stacks", "drilling_paths", "access_paths"):
            assert set(before[role]) == set(after[role])
        for name, bolt in before["bolts"].items():
            other = after["bolts"][name]
            assert other.start.toTuple() == pytest.approx(bolt.start.toTuple())
            assert other.direction.toTuple() == pytest.approx(bolt.direction.toTuple())
            assert other.length == bolt.length == center.BOLT_LENGTH_MM
        for name, barrel in before["barrels"].items():
            assert after["barrels"][name].Volume() == pytest.approx(barrel.Volume())


def test_revised_center_pose_has_exact_contained_cores_bores_and_shafts(layouts):
    wood, original, revised = layouts
    trial = revised["diagnostics"]["principal_header_geometry_trial"]
    assert trial["rows_y_mm"] == pytest.approx(
        center.REVISED_PRINCIPAL_ROWS_Y_MM, abs=1e-6
    )
    assert trial["washer_od_mm"] == 22.0
    assert trial["bolt_nominal_length_mm"] == pytest.approx(101.6)
    assert trial["washer_seat_cad_opportunity"]
    assert trial["full_nominal_bolt_bore_contained"]
    assert trial["provisional_axis_overrun_met"]
    assert all(not hits for hits in trial["pair_hits_mm3"].values())
    assert min(trial["reserves_mm"].values()) == pytest.approx(2.266666, abs=1e-6)

    for side in ("left", "right"):
        station = f"clip_split_base_center_{side}"
        before, after = original["stations"][station], revised["stations"][station]
        assert len(after["bolts"]) == len(after["barrels"]) == 2
        assert len(after["drilling_paths"]) == len(after["access_paths"]) == 4
        for index, y in enumerate(center.REVISED_PRINCIPAL_ROWS_Y_MM, 1):
            name = f"barrel_center_{station}_{index}"
            bolt = after["bolts"][f"{name}_bolt"]
            old_bolt = before["bolts"][f"{name}_bolt"]
            assert bolt.length == pytest.approx(101.6)
            assert old_bolt.length == center.BOLT_LENGTH_MM
            assert bolt.start.y == pytest.approx(y)
            assert after["stacks"][bolt.name][
                "washer"
            ].BoundingBox().ylen == pytest.approx(22.0)
            bore = after["drilling_paths"][f"{name}/bolt_bore"]
            cross_bore = after["drilling_paths"][f"{name}/barrel_cross_bore"]
            barrel = after["barrels"][name]
            shaft = cq.Solid.makeCylinder(
                bolt.diameter / 2,
                bolt.length - center.WASHER_THICKNESS_MM,
                cq.Vector(
                    bolt.start.x,
                    bolt.start.y,
                    bolt.start.z + center.WASHER_THICKNESS_MM,
                ),
                bolt.direction,
            )
            hosts = (wood["base_header"], wood[f"base_principal_center_{side}"])
            principal = hosts[1]
            for shape in (cross_bore, barrel):
                assert protected._volume(shape, principal) / shape.Volume() > 0.999999
            assert protected._volume(bore, cross_bore) > 400
            for shape in (bore, shaft):
                outside = shape.Volume() - sum(
                    protected._volume(shape, host) for host in hosts
                )
                assert abs(outside) < 0.01
            trial_bolt = trial["bolts"][name]
            assert trial_bolt["minimum_intended_core_fraction"] >= 0.999999
            assert trial_bolt["full_nominal_bore_uncontained_mm3"] == 0
            assert trial_bolt["embedded_nominal_shaft_uncontained_mm3"] == 0
            assert trial_bolt["nominal_bolt_tip_center_in_principal"]
            assert trial_bolt["bolt_barrel_intersection_mm3"] > 400
            assert not trial_bolt["protected_hits_mm3"]
            assert not trial_bolt["unrelated_wood_hits_mm3"]


def test_revised_solids_have_no_finite_protected_hits_and_no_release(layouts):
    _, _, revised = layouts
    candidate = {}
    for side in ("left", "right"):
        row = revised["stations"][f"clip_split_base_center_{side}"]
        candidate.update(row["barrels"])
        candidate.update(row["drilling_paths"])
        candidate.update(row["access_paths"])
        for bolt_name, stack in row["stacks"].items():
            candidate.update(
                {f"{bolt_name}/{role}": solid for role, solid in stack.items()}
            )
    assert all(not hits for hits in protected.hits(candidate).values())
    report = revised["diagnostics"]
    assert report["inventory"]["fixed_panel_kicker_axes"] == 66
    assert report["inventory"]["retained_frame_bolts"] == 12
    assert report["approved_post_centers_x_mm"] == [-180.0, 180.0]
    assert not report["washer_product_selected"]
    assert not report["bolt_product_selected"]
    assert not report["purchased_hillman_fit_verified"]
    assert not report["cross_dowel_resistance_verified"]
    assert not report["drilling_released"]
    assert not report["structural_released"]
    assert report["decision"] == "REVISE_VIEWER_ONLY"
