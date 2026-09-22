"""Source-built screening and assembly contract for the centered-barrel candidate."""

import pytest

from scripts import owner_barrel_center_single_layout as single


@pytest.fixture(scope="module")
def trial():
    return single.build()


def test_one_centered_principal_row_and_two_retained_post_rows(trial):
    report = trial["report"]
    assert set(report["stations"]) == set(single.integrated.STATIONS)
    assert len(trial["solids"]) == 6
    assert report["protected_counts"]["panel_screws"] == 66
    assert report["protected_counts"]["frame_bolts"] == 12
    assert not any(name.startswith("inner_kicker_backer_") for name in trial["wood"])
    for side, x in (("left", -70.0), ("right", 70.0)):
        post = report["stations"][f"clip_split_header_center_{side}"]
        principal = report["stations"][f"clip_split_base_center_{side}"]
        assert len(post["bolts"]) == 2
        assert len(principal["bolts"]) == 1
        row = next(iter(principal["bolts"].values()))
        assert row["bolt_seat_xyz_mm"][0] == pytest.approx(x)
        assert row["bolt_axis_angle_from_y_deg"] == 50
        assert row["bolt_length_mm"] == 127
        assert row["barrel_radial_x_edge_ligament_mm"] == pytest.approx(14.0462)
        assert row["barrel_recess_mm"] > 41
        assert row["modeled_bore_depth_past_nominal_tip_mm"] == 4
        assert row["tip_extension_in_receiver_fraction"] == 1
        assert row["joined_wood_bore_core_fraction"] == 1
        assert row["head_washer_inside_header_fraction"] == {
            "head": 1.0,
            "washer": 1.0,
        }
        assert row["driver_residual_header_mm3"] == 0
        assert not row["protected_hits_mm3"]
        assert not row["unrelated_wood_hits_mm3"]
        assert not row["retained_hardware_hits_mm3"]
        assert not row["candidate_service_void_hits_mm3"]


def test_full_screen_and_conditional_service_are_never_reported_as_release(trial):
    report = trial["report"]
    assert report["historical_service_diameter_mm"] == 38.1
    assert report["candidate_service_diameter_mm"] == 25.4
    assert report["candidate_service_void"] == (
        "right_072_same_axis_25.4_mm_provisional"
    )
    assert report["nominal_geometry_disposition"] == "CANDIDATE_ONLY_UNVERIFIED"
    assert report["native_solve"] is False
    assert report["structural_capacity_verified"] is False
    assert report["assembly_moment_transfer_verified"] is False
    assert report["service_feed_qualified"] is False
    assert not any(report["release_flags"].values())
    assert all(report["unverified"].values())
    assert "not screened" in report["tool_scope"]
    for key in (
        "installed_hardware_pair_hits_mm3",
        "tool_to_other_hardware_hits_mm3",
        "tool_pair_hits_mm3",
        "role_to_other_hardware_hits_mm3",
    ):
        assert not report[key]
    right = next(
        iter(report["stations"]["clip_split_base_center_right"]["bolts"].values())
    )
    assert right["barrel_insertion_orientation_access_verified"] is False
    assert right["barrel_tool_modeled_axis_span_from_entry_mm"] == [-40, 0]
    assert right["nominal_tip_beyond_barrel_far_wall_mm"] == pytest.approx(20.3452)
    assert right["head_pocket_header_bottom_margin_mm"] == pytest.approx(2.092152)
    bore = "base_principal_center_right/bore_base_principal_center_right_072"
    assert bore in trial["service_voids"]
    assert not right["candidate_service_void_hits_mm3"]


def test_four_row_adapter_and_unchanged_bottom_wrapper(trial, monkeypatch):
    monkeypatch.setattr(single, "build", lambda *, wood: trial)
    adapted = single.build_layout(trial["wood"])
    assert set(adapted["stations"]) == set(single.integrated.STATIONS)
    for station, row in adapted["stations"].items():
        count = 2 if "header_center" in station else 1
        assert len(row["bolts"]) == len(row["barrels"]) == count
        assert len(row["stacks"]) == count
        assert len(row["access_paths"]) == 2 * count
        assert len(row["drilling_paths"]) == (2 if count == 2 else 3) * count
        assert row["disposition"] == "VIEWER_ONLY_UNVERIFIED"

    bottom = {
        "clip_horizontal_bottom_left_2": {"bolts": {"a": object()}},
        "clip_horizontal_bottom_right_1": {"bolts": {"b": object()}},
    }
    monkeypatch.setattr(single.center, "_wood", lambda: (None, {}, None))
    monkeypatch.setattr(
        single.center,
        "build_revised_layout",
        lambda wood: {"stations": bottom, "diagnostics": {"source": "unchanged"}},
    )
    combined = single.build_six_layout(trial["wood"])
    assert len(combined["stations"]) == 6
    assert all(row["bolts"] for row in combined["stations"].values())
    assert (
        combined["diagnostics"]["revised_center"]["assembly_moment_transfer_verified"]
        is False
    )
    assert (
        combined["stations"]["clip_horizontal_bottom_left_2"]
        is bottom["clip_horizontal_bottom_left_2"]
    )
