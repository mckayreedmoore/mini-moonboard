"""Direct, source-built joint screen for the two integrated 4x6 posts."""

import pytest

from scripts import owner_barrel_center_post_joint_replan as replan


@pytest.fixture(scope="module")
def trial():
    return replan.build()


def test_four_direct_stations_use_integrated_posts_and_fixed_axes(trial):
    report = trial["report"]
    assert set(report["stations"]) == set(replan.STATIONS)
    assert not any(name.startswith("inner_kicker_backer_") for name in trial["wood"])
    assert report["protected_counts"]["panel_screws"] == 66
    assert report["protected_counts"]["frame_bolts"] == 12
    assert report["fixed_center_kicker_screws_received"] == 4
    assert not any(report["release_flags"].values())
    for side in ("left", "right"):
        post = report["stations"][f"clip_split_header_center_{side}"]
        principal = report["stations"][f"clip_split_base_center_{side}"]
        assert post["family"] == "post_header"
        assert principal["family"] == "principal_header"
        assert len(post["bolts"]) == len(principal["bolts"]) == 2
        for bolt in post["bolts"].values():
            assert bolt["barrel_cross_bore_depth_mm"] == pytest.approx(68.501)
            assert bolt["barrel_axis_depth_mm"] == pytest.approx(60.5)
            assert bolt["barrel_body_in_host_fraction"] > 0.999
            assert bolt["bolt_barrel_intersection_mm3"] > 0
            assert bolt["bolt_length_mm"] == pytest.approx(101.6)
        assert {b["entry_face"] for b in principal["bolts"].values()} == {
            "header_rear_recess",
        }
        assert [
            b["bolt_length_mm"] for b in principal["bolts"].values()
        ] == pytest.approx([127.0, 114.3])
        assert all(
            b["washer_diameter_mm"] == pytest.approx(19.05)
            for b in principal["bolts"].values()
        )
        assert all(
            b["barrel_recess_mm"] == pytest.approx(1.049)
            for b in principal["bolts"].values()
        )


def test_complete_geometry_reports_all_clashes_without_claiming_release(trial):
    report = trial["report"]
    for station in report["stations"].values():
        for bolt in station["bolts"].values():
            assert bolt["joined_wood_bore_core_fraction"] > 0.999
            assert bolt["barrel_body_in_host_fraction"] > 0.999
            assert bolt["bolt_barrel_intersection_mm3"] > 0
            assert bolt["nominal_tip_beyond_thread_axis_mm"] > 0
            assert bolt["modeled_bore_depth_past_nominal_tip_mm"] == pytest.approx(4.0)
            assert bolt["tip_extension_in_receiver_fraction"] > 0.999
            assert not bolt["tip_extension_unrelated_wood_hits_mm3"]
            assert not bolt["tip_extension_protected_hits_mm3"]
            assert not bolt["protected_hits_mm3"]
            assert not bolt["unrelated_wood_hits_mm3"]
            assert set(bolt["screened_roles"]) == {
                "bolt_bore",
                "barrel_cross_bore",
                "shaft",
                "barrel",
                "washer",
                "head",
                "bolt_tool",
                "barrel_tool",
            } | ({"head_pocket"} if bolt["entry_face"].startswith("header_") else set())
    assert not report["hardware_to_new_post_hits_mm3"]
    assert not report["installed_hardware_pair_hits_mm3"]
    assert not report["candidate_to_retained_hardware_hits_mm3"]
    assert not report["tool_to_other_hardware_hits_mm3"]
    assert not report["tool_pair_hits_mm3"]
    assert report["nominal_geometry_disposition"] == "CLASH"
    service = report["candidate_to_inherited_service_void_hits_mm3"]
    assert any(
        "bore_base_principal_center_right_072" in cutter
        for hits in service.values()
        for cutter in hits
    )
    assert any(name.endswith("/barrel") for name in service)
    assert report["driver_to_header_after_pocket_hits_mm3"]
    assert report["native_solve"] is False
    assert report["structural_capacity_verified"] is False


def test_adapter_has_four_assembly_rows(trial, monkeypatch):
    monkeypatch.setattr(replan, "build", lambda *, wood: trial)
    adapted = replan.build_layout(trial["wood"])
    assert set(adapted["stations"]) == set(replan.STATIONS)
    for station in adapted["stations"].values():
        assert station["mode"] == "direct"
        assert len(station["bolts"]) == len(station["barrels"]) == 2
        assert set(station["stacks"]) == set(station["bolts"])
        assert len(station["access_paths"]) == 4
        assert len(station["drilling_paths"]) in (4, 6)
