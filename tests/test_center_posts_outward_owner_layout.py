"""Light geometry checks for the detached, owner-review-only layout."""

import csv

import pytest

from scripts import center_posts_outward_owner_layout as trial


@pytest.fixture(scope="module")
def layout():
    return trial.build_layout()


def test_posts_move_110_mm_and_clear_kicker_flanges(layout):
    assert layout["post_bounds_x_mm"] == {
        "left": [-199.05, -160.95],
        "right": [160.95, 199.05],
    }
    assert layout["post_shift_x_mm"] == {"left": -110.0, "right": 110.0}
    assert layout["flange_bounds_x_mm"]["KICK5"] == pytest.approx([-137.66, -112.26])
    assert layout["flange_bounds_x_mm"]["KICK6"] == pytest.approx([110.9, 136.3])
    assert layout["post_to_flange_x_clearance_mm"] == pytest.approx(
        {"KICK5": 23.29, "KICK6": 24.65}
    )
    assert layout["post_backer_overlap_mm3"] == 0


def test_all_66_fixed_axes_and_original_bracket_duties_are_untouched(layout):
    with trial.AXES.open(newline="") as file:
        rows = list(csv.DictReader(file))
    fixed = {
        row["name"]: row
        for row in rows
        if row["name"].startswith(("round_panel_", "round_kicker_", "kicker_header_"))
    }
    assert len(fixed) == 66
    assert layout["fixed_panel_axes"] == {
        name: (
            tuple(float(row[f"start_{axis}_mm"]) for axis in "xyz"),
            tuple(float(row[f"direction_{axis}"]) for axis in "xyz"),
            float(row["shop_purchased_length_mm"]),
        )
        for name, row in fixed.items()
    }
    assert layout["panel_receiver_map"] == {
        name: (
            f"inner_kicker_backer_{'left' if '_left_' in name else 'right'}"
            if name.startswith("round_kicker_") and "_center_" in name
            else row["second_member"]
        )
        for name, row in fixed.items()
    }
    bracket_map = {}
    for row in rows:
        if row["name"].startswith("clip_"):
            station = row["name"].rsplit("_beam_", 1)[0].rsplit("_upright_", 1)[0]
            bracket_map.setdefault(station, []).append(
                (row["name"], row["first_member"], row["second_member"])
            )
    assert len(bracket_map) == 24
    assert layout["bracket_duty_map"] == {
        name: tuple(rows) for name, rows in bracket_map.items()
    }
    assert layout["frame_bolt_names"] == {
        row["name"] for row in rows if row["kind"] == "bolt"
    }
    assert layout["unresolved_bracket_stations"] == {
        "clip_split_header_center_left",
        "clip_split_header_center_right",
    }
    assert layout["disposition"] == "OWNER_REVIEW_LAYOUT_ONLY"


def test_backers_receive_actual_screws_and_support_both_inner_edges(layout):
    assert layout["backer_bounds_x_mm"]["left"] == pytest.approx([-90.4875, -1.5875])
    assert layout["backer_bounds_x_mm"]["right"] == pytest.approx([-1.5875, 87.3125])
    assert len(layout["center_kicker_screws"]) == 4
    for row in layout["center_kicker_screws"].values():
        assert row["purchased_length_mm"] == 63.5
        assert row["embedded_wood_length_mm"] == pytest.approx(45.24375)
        assert row["tip_to_backer_rear_mm"] == pytest.approx(43.65625)
        assert row["full_shaft_received"]
    assert layout["inner_edge_backed"] == {"kicker_left": True, "kicker_right": True}
    assert layout["backer_frame_attachment_qualified"] is False
    assert set(layout["protected_3d_gates"]) == set(trial.PROTECTED_3D_GATES)
    assert all(
        gate == {"status": "UNVERIFIED", "clearance_mm": None}
        for gate in layout["protected_3d_gates"].values()
    )
