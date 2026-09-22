"""Original center posts can feed the six-duty barrel viewer without backers."""

import pytest

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_barrel_center_layout as center


@pytest.fixture(scope="module")
def original_layout():
    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    assert not any(name.startswith("inner_kicker_backer_") for name in wood)
    return wood, center.build_layout(wood)


def test_original_posts_and_no_backers_are_accepted(original_layout):
    wood, built = original_layout
    assert set(built["stations"]) == set(center.STATIONS)
    assert built["diagnostics"]["approved_post_centers_x_mm"] == [-70.0, 70.0]
    for side, target in (("left", -70.0), ("right", 70.0)):
        bounds = wood[f"base_post_center_{side}"].BoundingBox()
        assert (bounds.xmin + bounds.xmax) / 2 == pytest.approx(target)


def test_original_principal_margin_uses_header_edges(original_layout):
    wood, built = original_layout
    header = wood["base_header"].BoundingBox()
    radius = center.WASHER_DIAMETER_MM / 2
    expected = min(-163.0 - header.ymin - radius, header.ymax - (-137.6) - radius)
    for side in ("left", "right"):
        row = built["diagnostics"]["stations"][f"clip_split_base_center_{side}"]
        assert row["nominal_washer_to_edge_or_backer_margin_mm"] == pytest.approx(
            expected
        )
        assert "washer edge tolerance" in row["revise_reasons"]
        assert "backer/washer tolerance" not in row["revise_reasons"]
        for bolt in row["bolts"].values():
            assert not any(
                "inner_kicker_backer_" in name
                for hits in bolt["unrelated_timber_hits_mm3"].values()
                for name in hits
            )


def test_revised_original_pose_screens_header_edge_without_backers(original_layout):
    wood, _ = original_layout
    revised = center.build_revised_layout(wood)
    trial = revised["diagnostics"]["principal_header_geometry_trial"]
    assert revised["diagnostics"]["approved_post_centers_x_mm"] == [-70.0, 70.0]
    assert "forward_header_edge_mm" in trial["reserves_mm"]
    assert "forward_backer_rear_mm" not in trial["reserves_mm"]
    assert trial["reserves_mm"]["forward_header_edge_mm"] == pytest.approx(
        wood["base_header"].BoundingBox().ymax
        - center.REVISED_PRINCIPAL_ROWS_Y_MM[1]
        - center.REVISED_PRINCIPAL_WASHER_OD_MM / 2
    )
    assert len(trial["bolts"]) == 4
    assert not trial["washer_seat_cad_opportunity"]
    for side, kicker in (
        ("left", "hold_tnut_kicker_5"),
        ("right", "hold_tnut_kicker_6"),
    ):
        post_station = f"clip_split_header_center_{side}"
        principal_station = f"clip_split_base_center_{side}"
        for station in (post_station, principal_station):
            assert revised["stations"][station]["disposition"] == "REVISE"
        post_report = revised["diagnostics"]["stations"][post_station]
        assert "finite protected-service intersection" in post_report["revise_reasons"]
        assert any(
            kicker
            in bolt["protected_hits_mm3"]
            .get("barrel_tool", {})
            .get("hold_hole_and_trial_projection", {})
            for bolt in post_report["bolts"].values()
        )
        principal_report = revised["diagnostics"]["stations"][principal_station]
        assert (
            "unrelated timber or backer intersection"
            in principal_report["revise_reasons"]
        )
        for bolt in principal_report["bolts"].values():
            assert bolt["unrelated_wood_hits_mm3"]["bolt_shaft_full_nominal"][
                f"base_post_center_{side}"
            ] == pytest.approx(52.285878)
    assert not revised["diagnostics"]["drilling_released"]
