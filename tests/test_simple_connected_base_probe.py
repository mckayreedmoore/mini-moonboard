"""Combined center/backer and rail-cleat kerf-right geometry checks only."""

from pathlib import Path

import cadquery as cq
import pytest

from scripts.simple_connected_base_probe import AXES, _split_clashes, probe

ROOT = Path(__file__).resolve().parents[1]
SHARED = (
    AXES,
    ROOT / "scripts/simple_center_support_offset.py",
    ROOT / "scripts/simple_rail_joint_comparison.py",
)


@pytest.fixture(scope="module")
def report():
    before = {path: path.read_bytes() for path in SHARED}
    result = probe()
    assert all(path.read_bytes() == content for path, content in before.items())
    return result


def test_one_center_assembly_preserves_axes_and_reports_baseline_overlap(report):
    assert report["physical_width"] == "kerf-right"
    assert report["raw_wood_and_panel_part_count"] == 26
    assert report["fixed_axes_count"] == {"main": 48, "kicker": 18}
    assert report["center_post_shift_x_mm"] == pytest.approx(37.8)
    assert report["center_backer_xyz_size_mm"] == [139.7, 88.9, 238.9]
    baseline = report["baseline_positive_volume_clashes"]
    assert baseline["wood_wood_mm3"] == {
        "lumber_leg_left|base_floor_left": pytest.approx(765784.421),
        "lumber_leg_right|base_floor_right": pytest.approx(765784.421),
    }
    assert baseline["wood_panel_mm3"] == {}
    assert report["new_center_wood_wood_clashes_mm3"] == {}
    assert report["new_center_wood_panel_clashes_mm3"] == {}
    assert report["center_assembly_positive_volume_clashes"] == baseline
    assert report["center_face_contact_area_mm2"] == {
        "backer_to_left_post": pytest.approx(21238.21),
        "backer_to_shifted_right_post": pytest.approx(21238.21),
        "backer_to_header": pytest.approx(12419.33),
    }


def test_full_purchased_kicker_paths_and_fixed_main_receivers(report):
    kicker = report["full_purchased_kicker_receiver_paths"]
    assert len(kicker) == 18
    assert sum(name.startswith("round_kicker_right_center_") for name in kicker) == 2
    for name, row in kicker.items():
        assert row["purchased_length_mm"] == pytest.approx(63.5)
        assert row["received_length_mm"] == pytest.approx(45.24375)
        assert row["legacy_path_received_fraction"] == pytest.approx(1)
        assert row["nominal_head_diameter_full_length_proxy_fraction"] == pytest.approx(
            1
        )
        if name.startswith("round_kicker_right_center_"):
            assert row["receiver"] == "center_backer"
    main = report["main_receiver_paths_unchanged"]
    assert len(main) == 48
    assert all(
        row["purchased_length_mm"] == pytest.approx(63.5) for row in main.values()
    )
    assert all(
        row["baseline_receiver_fraction"] == pytest.approx(1) for row in main.values()
    )
    assert all(
        row["legacy_path_received_fraction"] == pytest.approx(1)
        for row in main.values()
    )
    assert all(
        row["nominal_head_diameter_full_length_proxy_fraction"] == pytest.approx(1)
        for row in main.values()
    )
    assert all(
        row["baseline_to_assembled_intersection_delta_mm3"] == 0
        for row in main.values()
    )
    for edge in report["kicker_inner_edge_support"].values():
        assert edge["inner_x_mm"] == pytest.approx(-1.5875)
        assert edge["backer_under_edge_at_z120"]
        assert edge["header_under_edge_at_z257_95"]


def test_both_grain_n_cleat_alternatives_in_same_center_frame(report):
    alternatives = report["alternatives"]
    assert set(alternatives) == {"grain_n_4x6_single", "grain_n_4x6_group"}
    assert alternatives["grain_n_4x6_single"]["cleat_datums"]["n_length_mm"] == 200
    assert alternatives["grain_n_4x6_group"]["cleat_datums"]["n_length_mm"] == 300
    for item in alternatives.values():
        assert item["cleat_datums"]["x_width_mm"] == pytest.approx(139.7)
        assert item["cleat_datums"]["t_width_mm"] == pytest.approx(57.15)
        assert all(area > 0 for area in item["face_contact_area_mm2"].values())
        assert item["cleat_center_backer_overlap_mm3"] == 0
        assert item["cleat_shifted_post_overlap_mm3"] == 0
        assert item["cleat_to_backer_bbox_z_separation_mm"] > 0
        assert item["new_wood_wood_clashes_mm3"] == {}
        assert item["new_wood_panel_clashes_mm3"] == {}
        assert item["cleat_vs_full_length_nominal_head_proxy_screws_mm3"] == {}
        assert (
            item["positive_volume_clashes"]
            == report["center_assembly_positive_volume_clashes"]
        )
    assert report["bolt_selection"] is None
    assert report["load_rating_adopted"] is False
    assert report["drilling_released"] is False


def test_positive_volume_clash_detector_is_not_a_status_assumption():
    first = cq.Solid.makeBox(10, 10, 10)
    second = cq.Solid.makeBox(10, 10, 10, cq.Vector(5, 0, 0))
    hits = _split_clashes({"wood_a": first, "wood_b": second})
    assert hits["wood_wood_mm3"] == {"wood_a|wood_b": pytest.approx(500)}
