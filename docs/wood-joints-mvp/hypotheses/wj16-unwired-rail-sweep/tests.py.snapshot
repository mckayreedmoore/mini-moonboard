from __future__ import annotations

import math
from copy import deepcopy

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts import wood_joint_wj06_outer_pair_probe as outer_probe
from scripts import wood_joint_wj16_compositor as compositor
from scripts import wood_joint_wj16_unwired_rail_sweep as sweep


def _rotated_test_solid() -> cq.Shape:
    return cq.Workplane("XY").box(24, 13, 7).val().rotate(
        (0, 0, 0), (1, 1, 0), 23
    )


def _projected_bounds(shape: cq.Shape) -> tuple[float, float, float, float, float, float]:
    values = []
    for vertex in shape.Vertices():
        point = vertex.Center()
        values.append(
            (
                point.dot(sweep.X_AXIS),
                point.dot(sweep.T_AXIS),
                point.dot(sweep.N_AXIS),
            )
        )
    return (
        min(row[0] for row in values),
        max(row[0] for row in values),
        min(row[1] for row in values),
        max(row[1] for row in values),
        min(row[2] for row in values),
        max(row[2] for row in values),
    )


def test_oriented_prism_contains_start_and_full_positive_n_translation() -> None:
    solid = _rotated_test_solid()
    enclosure, evidence = sweep._build_sweep_enclosure(solid, extension_mm=200)
    endpoint = solid.translate(sweep.N_AXIS.multiply(200))

    assert enclosure.isValid()
    assert float(solid.cut(enclosure).Volume()) <= 1e-7
    assert float(endpoint.cut(enclosure).Volume()) <= 1e-7
    assert evidence["start_and_end_containment_verified"] is True
    assert evidence["intermediate_translation_contained_by_prism"] is True

    start = _frame_bounds_for_test(solid)
    prism = _projected_bounds(enclosure)
    assert prism[0] <= start[0] + 1e-7
    assert prism[1] >= start[1] - 1e-7
    assert prism[2] <= start[2] + 1e-7
    assert prism[3] >= start[3] - 1e-7
    assert prism[4] <= start[4] + 1e-7
    assert prism[5] >= start[5] + 200 - 1e-7


def _frame_bounds_for_test(shape: cq.Shape) -> tuple[float, float, float, float, float, float]:
    return sweep._frame_bounds(shape)


def test_sweep_rejects_invalid_extension_and_bad_source_shape() -> None:
    solid = cq.Workplane("XY").box(1, 2, 3).val()
    with pytest.raises(ValueError, match="finite and nonnegative"):
        sweep._build_sweep_enclosure(solid, extension_mm=-1)
    with pytest.raises(ValueError, match="valid solid"):
        sweep._build_sweep_enclosure(None)  # type: ignore[arg-type]


def test_upper_right_stack_partition_uses_fixed_family_and_trial_ids() -> None:
    moving, absent = sweep._expected_stack_ids(
        {
            "wj04_g7": g7_probe.TRIAL_ID,
            "wj06_outer_pair": outer_probe.TRIAL_ID,
        }
    )

    assert moving == {
        f"wj04_g7/{g7_probe.TRIAL_ID}/upper_rail_1",
        f"wj04_g7/{g7_probe.TRIAL_ID}/upper_rail_2",
        f"wj06_outer_pair/{outer_probe.TRIAL_ID}/upper_rail_1",
        f"wj06_outer_pair/{outer_probe.TRIAL_ID}/upper_rail_2",
    }
    assert absent == {
        f"wj04_g7/{g7_probe.TRIAL_ID}/upper_principal_1",
        f"wj04_g7/{g7_probe.TRIAL_ID}/upper_principal_2",
        f"wj06_outer_pair/{outer_probe.TRIAL_ID}/upper_side_1",
        f"wj06_outer_pair/{outer_probe.TRIAL_ID}/upper_side_2",
    }
    assert moving.isdisjoint(absent)
    assert len(sweep.ABSENT_PANEL_AXIS_IDS) == 2
    assert len(sweep.ABSENT_UPRIGHT_STACK_SUFFIXES["wj04_g7"]) == 2
    assert len(sweep.ABSENT_UPRIGHT_STACK_SUFFIXES["wj06_outer_pair"]) == 2

    with pytest.raises(ValueError, match="trial changed"):
        sweep._expected_stack_ids(
            {"wj04_g7": "stale-trial", "wj06_outer_pair": outer_probe.TRIAL_ID}
        )


def test_other_candidate_stacks_may_keep_their_named_five_component_schema() -> None:
    solid = cq.Workplane("XY").box(1, 1, 1).val()
    nonordinary_roles = {
        "bottom_washer": solid,
        "bottom_head": solid,
        "top_washer": solid,
        "top_nut": solid,
        "shaft": solid,
    }
    checked = sweep._validate_hardware_map_sizes(
        {"backer_header_left_1": nonordinary_roles},
        {"backer_header_left_1"},
    )
    assert set(checked["backer_header_left_1"]) == set(nonordinary_roles)

    with pytest.raises(ValueError, match="five installed shape roles"):
        sweep._validate_hardware_map_sizes(
            {"backer_header_left_1": dict(list(nonordinary_roles.items())[:4])},
            {"backer_header_left_1"},
        )


def test_harness_omission_and_stationary_scene_counts_are_exact() -> None:
    assert sweep.EXPECTED_PROTECTED_COUNTS["lights"] == 132
    assert sweep.EXPECTED_PROTECTED_COUNTS["wires"] == 131
    assert sweep.EXPECTED_STATIONARY_CATEGORY_COUNTS["finished_timber_geometry"] == 43
    assert sum(sweep.EXPECTED_STATIONARY_CATEGORY_COUNTS.values()) == 839
    assert 839 + 132 + 131 == 1102
    assert set.union(*map(set, sweep.MOVING_STACK_SUFFIXES.values())) == {
        "upper_rail_1",
        "upper_rail_2",
    }
    assert WJ04_TRIAL.frame.n_global == pytest.approx(
        (0.0, -math.sin(math.radians(50)), math.cos(math.radians(50)))
    )


def test_protected_shape_inventory_requires_full_harness_before_omission() -> None:
    solid = cq.Workplane("XY").box(1, 1, 1).val()
    protected = {
        family: {f"shape_{index}": solid for index in range(count)}
        for family, count in sweep.EXPECTED_PROTECTED_COUNTS.items()
    }
    checked = sweep._validate_protected_counts(protected)
    assert len(checked["lights"]) == 132
    assert len(checked["wires"]) == 131

    protected["wires"].pop("shape_130")
    with pytest.raises(ValueError, match="counts differ"):
        sweep._validate_protected_counts(protected)


def _overlay_evidence_fixture() -> dict[str, object]:
    source_finished = {}
    overlays = {}
    cutters_by_host = {}
    expected_cut_ids_by_host = {}
    expected_cutters_by_host = {}
    overlay_reconstruction = {}
    for host_index, (host_id, count) in enumerate(
        compositor.EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS.items()
    ):
        base = cq.Workplane("XY").box(20, 20, 20).translate(
            (host_index * 40, 0, 0)
        ).val()
        overlay = cq.Workplane("XY").box(19, 20, 20).translate(
            (host_index * 40, 0, 0)
        ).val()
        source_finished[host_id] = base
        overlays[host_id] = overlay
        cut_ids = {f"panel_purchase/axis_{host_index}_{index}" for index in range(count)}
        expected_cut_ids_by_host[host_id] = cut_ids
        cutters = {
            cut_id: cq.Workplane("XY").box(1, 1, 1).translate(
                (host_index * 40 + index, 0, 0)
            ).val()
            for index, cut_id in enumerate(sorted(cut_ids))
        }
        cutters_by_host[host_id] = dict(cutters)
        expected_cutters_by_host[host_id] = dict(cutters)
        overlay_reconstruction[host_id] = {
            "source_finished_shape_sha256": sweep._source_shape_fingerprint(base),
            "overlaid_finished_shape_sha256": sweep._source_shape_fingerprint(overlay),
            "purchase_cut_ids": sorted(cut_ids),
            "purchase_cut_intersection_mm3_by_id": {
                cut_id: 1.0 for cut_id in cut_ids
            },
            "matches_source_plus_purchase_cuts": True,
        }
    return {
        "overlay_reconstruction": overlay_reconstruction,
        "source_finished": source_finished,
        "overlays": overlays,
        "cutters_by_host": cutters_by_host,
        "expected_cut_ids_by_host": expected_cut_ids_by_host,
        "expected_cutters_by_host": expected_cutters_by_host,
    }


def test_source_overlay_evidence_requires_exact_source_and_purchase_cut_binding() -> None:
    evidence = _overlay_evidence_fixture()
    sweep._validate_overlay_reconstruction(**evidence)

    legacy_evidence = deepcopy(evidence)
    row = next(iter(legacy_evidence["overlay_reconstruction"].values()))
    row.pop("matches_source_plus_purchase_cuts")
    row["matches_source_finished_member"] = True
    with pytest.raises(ValueError, match="reconstruction evidence changed"):
        sweep._validate_overlay_reconstruction(**legacy_evidence)

    wrong_cutter = deepcopy(evidence)
    host_id = next(iter(wrong_cutter["cutters_by_host"]))
    cut_id = next(iter(wrong_cutter["cutters_by_host"][host_id]))
    wrong_cutter["cutters_by_host"][host_id][cut_id] = cq.Workplane("XY").box(
        2, 2, 2
    ).val()
    with pytest.raises(ValueError, match="cutter geometry differs"):
        sweep._validate_overlay_reconstruction(**wrong_cutter)

    wrong_cut_ids = deepcopy(evidence)
    host_id = next(iter(wrong_cut_ids["overlay_reconstruction"]))
    wrong_cut_ids["overlay_reconstruction"][host_id]["purchase_cut_ids"].pop()
    with pytest.raises(ValueError, match="reconstruction evidence changed"):
        sweep._validate_overlay_reconstruction(**wrong_cut_ids)


def test_enclosure_screen_finds_path_overlap_and_bbox_prunes_distant_obstacle() -> None:
    moving = cq.Workplane("XY").box(10, 10, 10).val()
    enclosure, _ = sweep._build_sweep_enclosure(moving, extension_mm=200)
    crossing_obstacle = moving.translate(sweep.N_AXIS.multiply(100))
    distant_obstacle = moving.translate(cq.Vector(1000, 1000, 1000))
    scene = sweep.SweepScene(
        moving_shapes={"moving" : moving},
        moving_categories={"moving": "test_moving"},
        stationary_shapes={
            "crossing": crossing_obstacle,
            "distant": distant_obstacle,
        },
        stationary_categories={"crossing": "test_obstacle", "distant": "test_obstacle"},
        enclosures={"moving": enclosure},
        enclosure_evidence={},
        source_evidence={},
        omitted_upright_stack_ids=(),
        omitted_upright_component_ids=(),
        absent_panel_axis_ids=(),
        omitted_harness_shape_ids=(),
        omitted_access_shape_ids=(),
    )

    report = sweep._screen_enclosures(scene)

    assert report["exact_boolean_pair_count_after_bbox_pruning"] == 1
    assert report["positive_volume_overlap_count"] == 1
    assert report["positive_volume_overlaps"][0]["obstacle_id"] == "crossing"
    assert report["conservative_enclosures_clear_of_stationary_shapes"] is False
