from __future__ import annotations

from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_probe as wj04_probe
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts import wood_joint_wj05_center_node_probe as center_probe
from scripts import wood_joint_wj12_sections as sections
from scripts import wood_joints_wj05_center_backer_transfer_probe as backer_probe


def _box() -> cq.Shape:
    return cq.Solid.makeBox(10.0, 20.0, 30.0)


def test_exact_section_area_and_local_bounds_match_analytic_box_and_bore() -> None:
    raw = _box()
    bore = cq.Solid.makeCylinder(
        1.0, 30.0, cq.Vector(5.0, 10.0, 0.0), cq.Vector(0.0, 0.0, 1.0)
    )
    finished = raw.cut(bore)
    geometry = SimpleNamespace(
        candidate_bores={
            "candidate_axis": SimpleNamespace(
                receiver_ids=("member",), shape=bore
            )
        },
        purchased_panel_cutters_by_candidate_part={},
    )

    report = sections._measurements(
        geometry=geometry,
        part_id="member",
        raw_stock=raw,
        family_input=raw,
        finished=finished,
        origin=cq.Vector(0.0, 0.0, 15.0),
        normal=cq.Vector(0.0, 0.0, 1.0),
        u_axis=cq.Vector(1.0, 0.0, 0.0),
        v_axis=cq.Vector(0.0, 1.0, 0.0),
        sample_id="analytic_midplane",
        purpose="Synthetic exact transverse section.",
        cut_feature_ids=("synthetic/bore",),
    )

    assert report["stock_section"]["area_mm2"] == pytest.approx(200.0)
    assert report["finished_section"]["area_mm2"] == pytest.approx(
        200.0 - 3.141592653589793
    )
    assert report["finished_section"]["bounds_uv_mm"] == {
        "u": pytest.approx([0.0, 10.0]),
        "v": pytest.approx([0.0, 20.0]),
    }
    assert report["candidate_bore_ids_intersecting_plane"] == ["candidate_axis"]
    assert report["sample_basis"] == "exact zero-thickness plane; no finite probe thickness"


def test_section_outside_stock_is_reported_as_zero_without_bounds() -> None:
    box = _box()

    result = sections._section_measure(
        box,
        origin=cq.Vector(0.0, 0.0, 31.0),
        normal=cq.Vector(0.0, 0.0, 1.0),
        u_axis=cq.Vector(1.0, 0.0, 0.0),
        v_axis=cq.Vector(0.0, 1.0, 0.0),
    )

    assert result == {
        "status": "no_material_on_sample_plane",
        "area_mm2": 0.0,
        "bounds_uv_mm": None,
    }


def test_report_marks_absent_feature_geometry_and_keeps_claim_gates_closed() -> None:
    geometry = SimpleNamespace(
        trial_id="synthetic-wj12",
        raw_candidate_parts={},
        finished_candidate_parts={},
        candidate_bores={},
        purchased_panel_cutters_by_candidate_part={},
    )

    report = sections.diagnostic_report(geometry)

    assert report["status"] == "sampled_sections_with_explicit_missing_basis"
    assert report["missing_feature_ids"] == [
        "wj03_compact_outer_rear_bridge_bevel",
        "wj04_upper_g7_crosscut",
        "wj05_center_principal_wire_relief",
        "wj05_backer_left_bottom_counterbores",
        "wj05_backer_right_bottom_counterbores",
    ]
    assert all(row["samples"] == [] for row in report["features"])
    assert report["claim_boundary"] == {
        "capacity_established": False,
        "net_section_adequacy_evaluated": False,
        "minimum_over_entire_member_proven": False,
        "strength_or_resistance_inferred": False,
        "native_solve_run": False,
    }


def test_report_samples_four_named_features_from_synthetic_composed_shapes() -> None:
    outer_raw = cq.Solid.makeBox(
        100.0, 38.1, 88.9, cq.Vector(10.0, 20.0, 100.0)
    )
    outer_finished = outer_raw.cut(
        cq.Solid.makeBox(100.0, 5.0, 20.0, cq.Vector(10.0, 20.0, 160.0))
    )
    g7_input = wj04_probe._box_in_trial_frame(
        WJ04_TRIAL,
        g7_probe.UPPER_CLEAT_ORIGIN_MM,
        g7_probe.UPPER_CLEAT_SIZE_MM,
    )
    center_input = center_probe._upper_cleat_right()
    backers = {}
    candidate_bores = {}
    for side in ("left", "right"):
        part_id = f"inner_kicker_backer_{side}"
        backer_raw = cq.Solid.makeBox(
            *backer_probe.BACKER_DIMS_MM,
            cq.Vector(
                backer_probe.BACKER_X_MM[side][0],
                backer_probe.BACKER_Y_MM[0],
                0.0,
            ),
        )
        backer_finished = backer_raw
        for index, (x, y) in enumerate(
            backer_probe.BACKER_BOLT_STATIONS[side], start=1
        ):
            axis_id = f"backer_header_{side}_{index}"
            bore = cq.Solid.makeCylinder(
                backer_probe.BORE_DIAMETER_MM / 2,
                backer_probe.HEADER_Z_MM[1],
                cq.Vector(x, y, 0.0),
                cq.Vector(0, 0, 1),
            )
            candidate_bores[axis_id] = SimpleNamespace(
                receiver_ids=(part_id, "base_header"), shape=bore
            )
            backer_finished = backer_finished.cut(
                cq.Solid.makeCylinder(
                    backer_probe.BOTTOM_COUNTERBORE_DIAMETER_MM / 2,
                    backer_probe.BOTTOM_COUNTERBORE_DEPTH_MM,
                    cq.Vector(x, y, 0.0),
                    cq.Vector(0, 0, 1),
                )
            ).cut(bore)
        backers[part_id] = (backer_raw, backer_finished)

    raw = {
        sections.OUTER_BRIDGE: outer_raw,
        sections.G7_UPPER: g7_input,
        sections.CENTER_UPPER: center_input,
        **{part_id: pair[0] for part_id, pair in backers.items()},
    }
    finished = {
        **raw,
        sections.OUTER_BRIDGE: outer_finished,
        **{part_id: pair[1] for part_id, pair in backers.items()},
    }
    geometry = SimpleNamespace(
        trial_id="synthetic-wj12-sections",
        raw_candidate_parts=raw,
        finished_candidate_parts=finished,
        candidate_bores=candidate_bores,
        purchased_panel_cutters_by_candidate_part={},
    )

    report = sections.diagnostic_report(geometry)

    assert report["status"] == "sampled_sections_diagnostic_only"
    assert report["missing_feature_ids"] == []
    by_id = {feature["feature_id"]: feature for feature in report["features"]}
    assert by_id["wj03_compact_outer_rear_bridge_bevel"]["samples"][0][
        "finished_section"
    ]["area_mm2"] < by_id["wj03_compact_outer_rear_bridge_bevel"]["samples"][0][
        "stock_section"
    ]["area_mm2"]
    g7_removed = by_id["wj04_upper_g7_crosscut"]["samples"][0]
    assert g7_removed["stock_section"]["area_mm2"] > 0.0
    assert g7_removed["family_input_section"]["area_mm2"] == 0.0
    center_relief = by_id["wj05_center_principal_wire_relief"]["samples"][0]
    assert center_relief["stock_section"]["area_mm2"] > 0.0
    assert center_relief["family_input_section"]["area_mm2"] == 0.0
    backer_left = by_id["wj05_backer_left_bottom_counterbores"]
    backer_right = by_id["wj05_backer_right_bottom_counterbores"]
    backer_counterbore = backer_left["samples"][0]
    assert backer_counterbore["finished_section"]["area_mm2"] < backer_counterbore[
        "stock_section"
    ]["area_mm2"]
    left_bounds = backer_left["samples"][0]["stock_section"]["bounds_uv_mm"]
    right_bounds = backer_right["samples"][0]["stock_section"]["bounds_uv_mm"]
    assert left_bounds["u"] == pytest.approx([-90.4875, -1.5875])
    assert right_bounds["u"] == pytest.approx([-1.5875, 87.3125])
    assert backer_left["samples"][0]["feature_specific_cut_ids"] == [
        "backer_header_left_1",
        "backer_header_left_2",
    ]
    assert backer_right["samples"][0]["feature_specific_cut_ids"] == [
        "backer_header_right_1",
        "backer_header_right_2",
    ]
    assert backer_left["samples"][0]["candidate_bore_ids_intersecting_plane"] == [
        "backer_header_left_1",
        "backer_header_left_2",
    ]
    assert backer_right["samples"][0]["candidate_bore_ids_intersecting_plane"] == [
        "backer_header_right_1",
        "backer_header_right_2",
    ]
