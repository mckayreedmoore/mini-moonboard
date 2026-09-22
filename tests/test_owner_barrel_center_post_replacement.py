"""Source-bound geometry checks for the integrated center-post replacement."""

import pytest

from scripts import owner_barrel_center_post_replacement as replacement


@pytest.fixture(scope="module")
def model():
    return replacement.build_model()


def test_two_standard_posts_replace_both_separate_backers(model):
    wood, report = model["wood"], model["report"]
    assert not any(name.startswith("inner_kicker_backer_") for name in wood)
    assert report["stock_name"] == "4x6_depth"
    assert report["stock_actual_section_mm"] == [88.9, 139.7]
    assert report["original_post_header_y_support_preserved"]
    assert report["kicker_seam_x_mm"] == pytest.approx(-1.5875)
    for side, expected_x in (
        ("left", [-90.4875, -1.5875]),
        ("right", [-1.5875, 87.3125]),
    ):
        name = f"base_post_center_{side}"
        box = wood[name].BoundingBox()
        assert [box.xmin, box.xmax] == pytest.approx(expected_x)
        assert [box.ymin, box.ymax] == pytest.approx([-175.7, -36.0])
        assert [box.zmin, box.zmax] == pytest.approx([0.0, 238.9])
        assert report["inner_edge_backed"][side]


def test_all_four_fixed_purchased_screws_are_received(model):
    rows = model["report"]["center_kicker_screws"]
    assert set(rows) == {
        "round_kicker_left_center_1",
        "round_kicker_left_center_2",
        "round_kicker_right_center_1",
        "round_kicker_right_center_2",
    }
    for name, row in rows.items():
        side = "left" if "_left_" in name else "right"
        assert row["receiver"] == f"base_post_center_{side}"
        assert row["axis_x_mm"] == (-70.0 if side == "left" else 70.0)
        assert row["purchased_length_mm"] == 63.5
        assert row["full_embedded_shaft_received"]
        assert row["wood_embed_length_mm"] == pytest.approx(45.24375)


def test_three_dimensional_screen_is_explicit_and_no_release(model):
    report = model["report"]
    assert report["protected_inventory_counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert set(report["screens"]) == {
        "protected",
        "other_wood",
        "current_barrel_hardware",
    }
    assert report["fixed_geometry_disposition"] == "CLEAR"
    assert report["current_barrel_hardware_disposition"] == "CONFLICT"
    assert report["stock_trials"]["4x6_depth"]["fixed_geometry_disposition"] == "CLEAR"
    assert (
        report["stock_trials"]["4x6_depth"]["current_barrel_hardware_disposition"]
        == "CONFLICT"
    )
    assert (
        report["stock_trials"]["4x6_face"]["fixed_geometry_disposition"] == "CONFLICT"
    )
    assert report["stock_trials"]["4x4"]["fixed_geometry_disposition"] == "CLEAR"
    assert not report["stock_trials"]["4x4"]["original_post_header_y_support_preserved"]
    assert report["unexpected_protected_hits_mm3"] == {
        "base_post_center_left": {},
        "base_post_center_right": {},
    }
    rotated = report["stock_trials"]["4x6_face"]["unexpected_protected_hits_mm3"]
    for side, kicker in (("left", 5), ("right", 6)):
        hits = rotated[f"base_post_center_{side}"]
        name = f"hold_tnut_kicker_{kicker}"
        assert hits["tnuts"][name] == pytest.approx(804.105091)
        assert hits["hold_hole_and_trial_projection"][name] == pytest.approx(
            4926.938504
        )
    assert report["screens"]["other_wood"] == {
        "base_post_center_left": {},
        "base_post_center_right": {},
    }
    for side in ("left", "right"):
        hits = report["screens"]["current_barrel_hardware"][f"base_post_center_{side}"]
        assert len(hits) == 6
        for index in (1, 2):
            stem = f"stack/barrel_center_clip_split_base_center_{side}_{index}_bolt"
            assert hits[f"{stem}/head"] == pytest.approx(380.132711)
            assert hits[f"{stem}/shaft"] == pytest.approx(52.285878)
            assert hits[f"{stem}/washer"] == pytest.approx(627.599106)
        assert all(
            volume == 0
            for volume in report["current_post_station_barrel_overlap_mm3"][
                f"clip_split_header_center_{side}"
            ].values()
        )
    assert not any(report["release_flags"].values())
    assert report["retained_barrel_station_fit_verified"] is False
