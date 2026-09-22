"""Visual-only timber replacement for the outward-post barrel viewer."""

import pytest

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_barrel_outer_header_cut_integrity as outer_header
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.owner_barrel_visual_wood import build_visual_wood


@pytest.fixture(scope="module")
def visual():
    assembly = build_viewer_assembly()
    volumes = {name: shape.Volume() for name, shape in assembly["wood"].items()}
    result = build_visual_wood(assembly=assembly)
    assert volumes == {name: shape.Volume() for name, shape in assembly["wood"].items()}
    return assembly, result


def test_exact_replacement_scope_and_protected_inventories(visual):
    assembly, result = visual
    assert set(result["wood"]) == {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_post_outer_left",
        "base_post_outer_right",
        "base_principal_center_left",
        "base_principal_center_right",
        "base_rail_bottom_left",
        "base_rail_bottom_right",
        "base_rail_service_lower_left",
        "base_rail_service_lower_right",
        "base_rail_service_upper_left",
        "base_rail_service_upper_right",
        "base_rail_top",
        "base_side_left",
        "base_side_right",
    }
    report = result["report"]
    assert report["former_angle_stations"] == 24
    assert report["excluded_legacy_sds_axes"] == 144
    assert report["fixed_panel_kicker_axes"] == 66
    assert report["fixed_panel_receiver_cuts_in_replacements"] == 62
    assert report["retained_frame_bolt_axes"] == 12
    assert report["retained_frame_bolt_cuts_in_replacements"] == 8
    assert report["inherited_service_cuts_in_replacements"] == 32
    assert report["outer_header_trial_cuts"] == 16
    assert report["per_member"]["base_header"]["counts"]["outer_header_trial"] == 8
    assert (
        report["per_member"]["base_post_outer_right"]["counts"]["outer_header_trial"]
        == 4
    )
    assert report["candidate_barrel_body_cuts"] == 4
    assert report["release"] is False
    assert len(assembly["removed_legacy_sds"]) == 144
    applied = {
        cutter
        for member in report["per_member"].values()
        for names in member["cutter_names"].values()
        for cutter in names
    }
    assert not applied & {row.name for row in assembly["removed_legacy_sds"]}


def test_old_angle_holes_are_absent_at_representative_rail_and_header_axes(visual):
    assembly, result = visual
    source = variant(KERF_RIGHT)
    finished = {part.name: part.shape for part in source.parts()}
    for station in ("clip_horizontal_lower_right_2", "clip_timber_header_outer_right"):
        rows = [
            row
            for row in assembly["removed_legacy_sds"]
            if row.name.startswith(station + "_")
        ]
        assert len(rows) == 6
        witnesses = []
        for row in rows:
            member = row.members[1]
            if member not in result["wood"]:
                continue
            for fraction in (0.25, 0.5, 0.75):
                point = row.start + row.direction * (row.length * fraction)
                if (
                    assembly["wood"][member].isInside(point, 1e-5)
                    and not finished[member].isInside(point, 1e-5)
                    and result["wood"][member].isInside(point, 1e-5)
                ):
                    witnesses.append(row.name)
                    break
        assert witnesses, station


def test_inherited_service_bore_remains_and_moved_post_has_no_old_kicker_bores(visual):
    assembly, result = visual
    source = variant(KERF_RIGHT)
    member, _, cutter = next(
        row
        for row in source.service_cutters()
        if row[1] == "bore_base_rail_bottom_left_001"
    )
    assert assembly["wood"][member].intersect(cutter).Volume() > 1.0
    assert result["wood"][member].intersect(cutter).Volume() < 1e-4
    for side in ("left", "right"):
        name = f"base_post_center_{side}"
        assert result["wood"][name].Volume() == pytest.approx(
            assembly["wood"][name].Volume(), abs=1e-4
        )


def test_outer_header_trial_bores_remain_after_fixed_cuts_with_overlap_report(visual):
    assembly, result = visual
    rows = outer_header._rows(assembly)
    for prefix, row in rows.items():
        side = row["side"]
        for role in ("counterbore", "machine_bore"):
            cutter = row["paths"][role]
            assert result["wood"]["base_header"].intersect(cutter).Volume() < 1e-4
            assert (
                f"{prefix}/{role}"
                in result["report"]["per_member"]["base_header"]["cutter_names"][
                    "outer_header_trial"
                ]
            )
        for role in ("barrel_bore", "machine_bore"):
            cutter = row["paths"][role]
            assert (
                result["wood"][f"base_post_outer_{side}"].intersect(cutter).Volume()
                < 1e-4
            )
    assert isinstance(result["report"]["trial_to_protected_cut_intersections"], list)
    assert isinstance(result["report"]["trial_to_trial_intersections"], list)
