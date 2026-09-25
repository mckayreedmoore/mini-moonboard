"""Focused validation for the bounded WJ12 upper-right rail motion adapter."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts import wood_joint_wj06_outer_pair_probe as outer_probe
from scripts import wood_joint_wj12_compositor as compositor
from scripts import wood_joint_wj12_right_assembly as assembly

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "docs/wood-joints-mvp/source-inventory.json"


def _box(x: float, y: float = 0.0, z: float = 0.0) -> cq.Shape:
    return cq.Solid.makeBox(1.0, 2.0, 3.0, cq.Vector(x, y, z))


def _shape_map(
    prefix: str, count: int, *, start_x: float = 20_000.0
) -> dict[str, cq.Shape]:
    return {
        f"{prefix}_{index:03d}": _box(start_x + index * 5.0) for index in range(count)
    }


def _scene_geometry() -> compositor.WJ12ComposedGeometry:
    inventory = json.loads(INVENTORY_PATH.read_text())
    inventory_sha = hashlib.sha256(INVENTORY_PATH.read_bytes()).hexdigest()
    all_duties = {row["legacy_station_id"]: row for row in inventory["legacy_duties"]}
    targets = set(compositor.TARGET_STATIONS)
    replaced_axis_ids = frozenset(
        axis["axis_id"]
        for station_id, row in all_duties.items()
        if station_id in targets
        for axis in row["legacy_sds_axes"]
    )
    retained_axis_ids = {
        axis["axis_id"]
        for row in inventory["legacy_duties"]
        for axis in row["legacy_sds_axes"]
    } - replaced_axis_ids
    retained_duty_ids = set(all_duties) - targets

    family_trial_ids = {
        "wj03_outer": "synthetic-wj03",
        "wj05_backer": "synthetic-wj05",
        assembly.G7_FAMILY: g7_probe.TRIAL_ID,
        assembly.OUTER_FAMILY: outer_probe.TRIAL_ID,
        "center_x190": "synthetic-center-x190",
    }
    right_paths = (
        "docs/wood-joints-mvp/source-inventory.json",
        "scripts/wood_joint_right_rail_integration.py",
        "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
        "scripts/wood_joint_wj06_outer_pair_probe.py",
    )
    right_fingerprints = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in right_paths
    }

    source_wood = {
        part_id: _box(8_000.0 + index * 5.0)
        for index, part_id in enumerate(sorted(assembly.EXPECTED_SOURCE_WOOD_IDS))
    }
    source_nonwood_ids = sorted(
        {row["legacy_station_id"] for row in inventory["legacy_duties"]}
        | {f"tnut_{index:03d}" for index in range(142)}
    )
    source_nonwood = {
        name: _box(9_000.0 + index * 5.0)
        for index, name in enumerate(source_nonwood_ids)
    }

    class SyntheticSource:
        def uncut_wood_parts(self) -> tuple[SimpleNamespace, ...]:
            return tuple(
                SimpleNamespace(name=name, shape=shape)
                for name, shape in sorted(source_wood.items())
            )

        def parts(self) -> tuple[SimpleNamespace, ...]:
            # Canonical source parts also exposes legacy clips and T-nuts.
            return self.uncut_wood_parts() + tuple(
                SimpleNamespace(name=name, shape=shape)
                for name, shape in sorted(source_nonwood.items())
            )

    fixed_axes = {
        row["axis_id"]: _box(10_000.0 + index * 5.0)
        for index, row in enumerate(inventory["fixed_panel_kicker_screws"])
    }
    frame_records = tuple(
        {"axis_id": row["axis_id"], "installed_component_count": 5}
        for row in inventory["starting_frame_bolts"]
    )
    frame_shapes = {
        f"{row['axis_id']}/installed_component_{component}": _box(
            12_000.0 + index * 40.0 + component
        )
        for index, row in enumerate(inventory["starting_frame_bolts"])
        for component in range(1, 6)
    }
    frame_shapes.update(
        {
            f"{row['axis_id']}/source_occupied_axis": _box(12_500.0 + index * 40.0)
            for index, row in enumerate(inventory["starting_frame_bolts"])
        }
    )
    protected = {
        "fixed_66_hillman_axes_63p5mm": dict(fixed_axes),
        "retained_12_frame_bolt_components": {
            f"{row['axis_id']}/{role}": frame_shapes[
                f"{row['axis_id']}/installed_component_{index}"
            ]
            for row in inventory["starting_frame_bolts"]
            for index, role in enumerate(
                ("shaft", "head_washer", "nut_washer", "head", "nut"), 1
            )
        },
        "retained_12_frame_bolt_tools_withdrawals": _shape_map("withdrawal", 36),
        "tnuts": _shape_map("tnut", 142),
        "hold_hole_and_provisional_projection": _shape_map("hold", 142),
        "lights": _shape_map("light", 132),
        "wires": _shape_map("wire", 131),
        "retained_legacy_clips": {
            station_id: _box(14_000.0 + index * 5.0)
            for index, station_id in enumerate(sorted(retained_duty_ids))
        },
        "retained_legacy_sds_axes": {
            axis_id: _box(15_000.0 + index * 5.0)
            for index, axis_id in enumerate(sorted(retained_axis_ids))
        },
    }

    moving_receivers = {
        f"{assembly.G7_FAMILY}/{g7_probe.TRIAL_ID}/upper_rail_1": (
            assembly.UPPER_RAIL,
            assembly.G7_UPPER_CLEAT,
        ),
        f"{assembly.G7_FAMILY}/{g7_probe.TRIAL_ID}/upper_rail_2": (
            assembly.UPPER_RAIL,
            assembly.G7_UPPER_CLEAT,
        ),
        f"{assembly.OUTER_FAMILY}/{outer_probe.TRIAL_ID}/upper_rail_1": (
            assembly.UPPER_RAIL,
            assembly.OUTER_UPPER_CLEAT,
        ),
        f"{assembly.OUTER_FAMILY}/{outer_probe.TRIAL_ID}/upper_rail_2": (
            assembly.UPPER_RAIL,
            assembly.OUTER_UPPER_CLEAT,
        ),
    }
    omitted_receivers = {
        f"{assembly.G7_FAMILY}/{g7_probe.TRIAL_ID}/upper_principal_1": (
            assembly.G7_UPPER_CLEAT,
            "base_principal_center_right",
        ),
        f"{assembly.G7_FAMILY}/{g7_probe.TRIAL_ID}/upper_principal_2": (
            assembly.G7_UPPER_CLEAT,
            "base_principal_center_right",
        ),
        f"{assembly.OUTER_FAMILY}/{outer_probe.TRIAL_ID}/upper_side_1": (
            assembly.OUTER_UPPER_CLEAT,
            "base_side_right",
        ),
        f"{assembly.OUTER_FAMILY}/{outer_probe.TRIAL_ID}/upper_side_2": (
            assembly.OUTER_UPPER_CLEAT,
            "base_side_right",
        ),
    }
    known_receivers = moving_receivers | omitted_receivers
    for producer, principal_id in (
        (g7_probe, g7_probe.PRINCIPAL),
        (outer_probe, "base_side_right"),
    ):
        family = assembly.G7_FAMILY if producer is g7_probe else assembly.OUTER_FAMILY
        for spec in producer.STACK_SPECS:
            if spec.station_id == (
                assembly.G7_UPPER_STATION
                if family == assembly.G7_FAMILY
                else assembly.OUTER_UPPER_STATION
            ):
                continue
            if spec.interface_id == "rail_to_cleat":
                receivers = (assembly.UPPER_RAIL, spec.cleat_id)
            elif spec.interface_id in {"principal_to_cleat", "cleat_to_side"}:
                receivers = (spec.cleat_id, principal_id)
            else:
                raise AssertionError(
                    f"unexpected source interface: {spec.interface_id}"
                )
            known_receivers[f"{family}/{producer.TRIAL_ID}/{spec.stack_id}"] = receivers
    candidate_bores = {
        axis_id: compositor.CandidateBore(
            axis_id=axis_id,
            family=axis_id.split("/", maxsplit=1)[0],
            trial_id=axis_id.split("/", maxsplit=2)[1],
            receiver_ids=receiver_ids,
            shape=_box(16_000.0 + index * 5.0),
            station_id=None,
        )
        for index, (axis_id, receiver_ids) in enumerate(known_receivers.items())
    }
    for index in range(40):
        axis_id = f"synthetic_family/synthetic_trial/other_stack_{index:02d}"
        candidate_bores[axis_id] = compositor.CandidateBore(
            axis_id=axis_id,
            family="synthetic_family",
            trial_id="synthetic_trial",
            receiver_ids=("other_part_a", "other_part_b"),
            shape=_box(16_500.0 + index * 5.0),
        )
    candidate_hardware = {
        axis_id: {
            role: _box(17_000.0 + index * 40.0 + component)
            for component, role in enumerate(
                ("shaft", "head", "head_washer", "nut_washer", "nut")
            )
        }
        for index, axis_id in enumerate(candidate_bores)
    }

    finished_hosts = {
        name: _box(0.0) for name in sorted(compositor.source_host_ids(inventory))
    }
    finished_parts = {
        name: _box(1_000.0 + index * 5.0)
        for index, name in enumerate(
            (
                assembly.G7_UPPER_CLEAT,
                assembly.OUTER_UPPER_CLEAT,
                "candidate_part_02",
                "candidate_part_03",
                "candidate_part_04",
                "candidate_part_05",
                "candidate_part_06",
                "candidate_part_07",
                "candidate_part_08",
                "candidate_part_09",
                "candidate_part_10",
                "candidate_part_11",
                "candidate_part_12",
                "candidate_part_13",
                "candidate_part_14",
                "candidate_part_15",
            )
        )
    }
    hosts = dict(finished_hosts)
    panel_replacements = {
        panel_id: _box(9_500.0 + index * 5.0)
        for index, panel_id in enumerate(sorted(assembly.RIGHT_PANEL_NAMES))
    }
    overlays = {
        name: _box(9_700.0 + index * 5.0)
        for index, name in enumerate(
            sorted(compositor.EXPECTED_ADDITIONAL_PANEL_RECEIVER_AXIS_COUNTS)
        )
    }
    geometry = compositor.WJ12ComposedGeometry(
        trial_id=compositor.TRIAL_ID,
        source=SyntheticSource(),
        source_binding=SimpleNamespace(
            inventory_sha256=inventory_sha,
            runtime_module_sha256=inventory["source_runtime_module_hashes_sha256"],
            uncut_part_shapes_sha256=inventory["source_part_shapes_sha256"],
        ),
        source_inventory_sha256=inventory_sha,
        source_inventory=inventory,
        family_source_fingerprints={"right_rail": right_fingerprints},
        family_trial_ids=family_trial_ids,
        target_station_ids=tuple(sorted(targets)),
        raw_hosts=hosts,
        finished_hosts=finished_hosts,
        raw_candidate_parts=dict(finished_parts),
        finished_candidate_parts=finished_parts,
        candidate_bores=candidate_bores,
        candidate_installed_hardware=candidate_hardware,
        replaced_source_axis_ids=replaced_axis_ids,
        replaced_source_cutter_ids=frozenset(),
        source_cutters_by_host={},
        applied_source_cutters_by_host={},
        purchased_panel_cutters_by_host={},
        purchased_panel_cutters_by_candidate_part={},
        additional_finished_source_parts=overlays,
        additional_purchased_panel_cutters_by_host={},
        additional_source_reconstruction={},
        source_reconstruction={},
        panel_replacements=panel_replacements,
        fixed_axes=fixed_axes,
        frame_bolt_records=frame_records,
        frame_bolt_shapes=frame_shapes,
        protected=protected,
    )
    return geometry


def test_registry_moves_full_upper_rail_subassembly_and_declares_omissions() -> None:
    geometry = _scene_geometry()
    scene = assembly._shape_registry(geometry)

    assert set(assembly.MOVING_MEMBER_IDS) == {
        assembly.UPPER_RAIL,
        assembly.G7_UPPER_CLEAT,
        assembly.OUTER_UPPER_CLEAT,
    }
    assert len(scene.moving_shapes) == 3 + 4 * 5
    assert len(scene.moving_stack_ids) == 4
    assert len(scene.omitted_candidate_stack_ids) == 4
    assert len(scene.omitted_candidate_stack_component_ids) == 20
    right_family_bores = [
        bore
        for bore in geometry.candidate_bores.values()
        if bore.family in {assembly.G7_FAMILY, assembly.OUTER_FAMILY}
    ]
    assert len(right_family_bores) == 16
    assert all(bore.station_id is None for bore in right_family_bores)
    assert len(scene.temporarily_absent_panel_axis_ids) == 2
    assert len(geometry.source_inventory["fixed_panel_kicker_screws"]) == 66
    assert len(scene.obstacle_shapes) > 900
    assert set(scene.source_wood_member_ids) == set(assembly.EXPECTED_SOURCE_WOOD_IDS)
    assert len(scene.source_wood_member_ids) == 26
    assert len(scene.finished_wood_member_ids) == 42
    assert len(scene.panel_member_ids) == 6
    assert len(scene.panel_replacement_ids) == 3
    assert all(
        row["candidate_bore_station_tag"] is None
        and row["resolved_producer_station_id"]
        in {assembly.G7_UPPER_STATION, assembly.OUTER_UPPER_STATION}
        for row in scene.source_metadata["upper_station_bolt_stack_axes"]
    )
    panel_obstacle_ids = {
        obstacle_id.removeprefix("finished_wood/")
        for obstacle_id in scene.obstacle_shapes
        if obstacle_id.startswith("finished_wood/")
        and obstacle_id.removeprefix("finished_wood/") in assembly.PANEL_NAMES
    }
    assert panel_obstacle_ids == set(assembly.PANEL_NAMES)
    assert len(panel_obstacle_ids) == 6
    source_nonwood_ids = {
        row["legacy_station_id"] for row in geometry.source_inventory["legacy_duties"]
    } | set(geometry.protected["tnuts"])
    assert not any(
        f"finished_wood/{name}" in scene.obstacle_shapes for name in source_nonwood_ids
    )

    assert len(scene.source_metadata["source_inventory_sha256"]) == 64
    assert set(scene.temporarily_absent_panel_axis_ids) == set(
        assembly.TEMPORARILY_ABSENT_PANEL_AXIS_IDS
    )
    assert set(scene.replaced_source_axis_ids) == set(geometry.replaced_source_axis_ids)
    assert scene.omitted_access_envelopes

    categories = {
        category: sum(value == category for value in scene.obstacle_categories.values())
        for category in set(scene.obstacle_categories.values())
    }
    assert categories["candidate_installed_hardware_shape"] == 240
    assert categories["frame_bolt_installed_component_shape"] == 60
    assert categories["frame_bolt_source_occupied_axis_envelope"] == 12
    assert categories["fixed_panel_screw_axis_envelope"] == 64
    assert categories["provisional_clearance_envelope"] == 142
    assert categories["finished_timber_geometry"] == 39


def test_registry_fails_closed_on_undeclared_protected_family() -> None:
    geometry = _scene_geometry()
    protected = dict(geometry.protected)
    protected["unexpected_new_shape_family"] = {"unexpected": _box(30_000.0)}
    with pytest.raises(ValueError, match="protected geometry families changed"):
        assembly._shape_registry(replace(geometry, protected=protected))


def test_registry_fails_closed_on_unknown_source_nonwood_part() -> None:
    geometry = _scene_geometry()

    class UnexpectedSource:
        def uncut_wood_parts(self) -> tuple[SimpleNamespace, ...]:
            return geometry.source.uncut_wood_parts()

        def parts(self) -> tuple[SimpleNamespace, ...]:
            return geometry.source.parts() + (
                SimpleNamespace(name="unexpected_source_part", shape=_box(31_000.0)),
            )

    with pytest.raises(ValueError, match="source non-wood parts differ"):
        assembly._shape_registry(replace(geometry, source=UnexpectedSource()))


def test_registry_fails_closed_on_unknown_panel_replacement_id() -> None:
    geometry = _scene_geometry()
    replacements = dict(geometry.panel_replacements)
    panel_id = next(iter(replacements))
    replacements["unexpected_panel"] = replacements.pop(panel_id)
    with pytest.raises(ValueError, match="panel replacement IDs differ"):
        assembly._shape_registry(replace(geometry, panel_replacements=replacements))


def test_registry_fails_closed_when_one_declared_upper_stack_is_incomplete() -> None:
    geometry = _scene_geometry()
    hardware = dict(geometry.candidate_installed_hardware)
    rail_axis = next(
        axis_id for axis_id in hardware if axis_id.endswith("upper_rail_1")
    )
    hardware[rail_axis] = dict(hardware[rail_axis])
    del hardware[rail_axis]["nut"]
    with pytest.raises(ValueError, match="counts differ from the declared map"):
        assembly._shape_registry(
            replace(geometry, candidate_installed_hardware=hardware)
        )


def test_registry_rejects_contradictory_optional_bore_station_tag() -> None:
    geometry = _scene_geometry()
    bores = dict(geometry.candidate_bores)
    axis_id = f"{assembly.G7_FAMILY}/{g7_probe.TRIAL_ID}/upper_rail_1"
    bores[axis_id] = replace(bores[axis_id], station_id="clip_horizontal_upper_left_1")
    with pytest.raises(ValueError, match="optional bore station tag contradicts"):
        assembly._shape_registry(replace(geometry, candidate_bores=bores))


def test_frame_aliases_cannot_swap_shapes_between_physical_bolts() -> None:
    geometry = _scene_geometry()
    protected = {family: dict(shapes) for family, shapes in geometry.protected.items()}
    aliases = protected["retained_12_frame_bolt_components"]
    first, second = sorted(key for key in aliases if key.endswith("/shaft"))[:2]
    aliases[first], aliases[second] = aliases[second], aliases[first]
    with pytest.raises(ValueError, match="component aliases differ"):
        assembly._validate_protected_duplicates(replace(geometry, protected=protected))


def test_pose_report_separates_hardware_axis_and_provisional_keepout_hits() -> None:
    moving = {"moving/cleat": _box(0.0)}
    obstacles = {
        "hardware/bolt": _box(0.75),
        "axis/occupied": _box(-0.75),
        "keepout/provisional": _box(10.0),
    }
    obstacle_categories = {
        "hardware/bolt": "candidate_installed_hardware_shape",
        "axis/occupied": "retained_source_sds_axis_envelope",
        "keepout/provisional": "provisional_clearance_envelope",
    }
    report = assembly._evaluate_pose(
        moving,
        obstacles,
        (0.0, 0.0, 0.0),
        moving_categories={"moving/cleat": "finished_timber_geometry"},
        obstacle_categories=obstacle_categories,
    )

    assert report["positive_volume_hit_count"] == 2
    assert {hit["obstacle_category"] for hit in report["positive_volume_hits"]} == {
        "candidate_installed_hardware_shape",
        "retained_source_sds_axis_envelope",
    }
    assert set(report["positive_volume_hits_by_obstacle_category"]) == {
        "candidate_installed_hardware_shape",
        "retained_source_sds_axis_envelope",
    }
    assert report["nearest_nonpenetrating_gap"]["obstacle_id"] == "keepout/provisional"
    assert report["nearest_nonpenetrating_gap"]["gap_mm"] > 0


def test_declared_offsets_and_forward_reverse_step_order_are_exact() -> None:
    assert assembly.SAMPLE_DISTANCES_MM == (0.0, 5.0, 10.0, 25.0, 50.0, 100.0, 200.0)
    assert assembly._path_offsets(1, insertion=True) == [
        200.0,
        100.0,
        50.0,
        25.0,
        10.0,
        5.0,
        0.0,
    ]
    assert assembly._path_offsets(1, insertion=False) == [
        0.0,
        5.0,
        10.0,
        25.0,
        50.0,
        100.0,
        200.0,
    ]
    assert assembly._path_offsets(-1, insertion=True) == [
        -200.0,
        -100.0,
        -50.0,
        -25.0,
        -10.0,
        -5.0,
        0.0,
    ]
    assert assembly._path_offsets(-1, insertion=False) == [
        0.0,
        -5.0,
        -10.0,
        -25.0,
        -50.0,
        -100.0,
        -200.0,
    ]


def test_report_evaluates_each_distinct_pose_once_and_links_path_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    translations = []

    def fake_evaluate_pose(
        moving_shapes: object,
        obstacles: object,
        translation_mm: tuple[float, float, float],
        **_: object,
    ) -> dict[str, object]:
        translations.append(translation_mm)
        return {
            "positive_volume_hit_count": 1,
            "positive_volume_hit_total_mm3": 0.25,
            "positive_volume_hits": [
                {
                    "moving_id": "moving/example",
                    "obstacle_id": "obstacle/example",
                    "obstacle_category": "provisional_clearance_envelope",
                    "intersection_volume_mm3": 0.25,
                }
            ],
            "positive_volume_hits_by_obstacle_category": {
                "provisional_clearance_envelope": {
                    "positive_volume_hit_count": 1,
                    "intersection_volume_mm3": 0.25,
                }
            },
            "nearest_nonpenetrating_gap": {
                "gap_mm": 0.5,
                "moving_id": "moving/example",
                "obstacle_id": "obstacle/clear",
                "exact_shape_distance": True,
            },
            "moving_obstacle_pair_count": 1,
        }

    monkeypatch.setattr(assembly, "_evaluate_pose", fake_evaluate_pose)
    report = assembly.diagnostic_report(_scene_geometry())

    assert len(translations) == 13
    assert len(set(translations)) == 13
    assert report["sampling"]["unique_cad_pose_evaluations"] == 13
    assert report["sampling"]["path_step_results_reuse_sampled_pose_records"] is True
    for path in report["paths"].values():
        for step in (
            *path["approach_steps_from_offset_to_seated"],
            *path["reverse_steps_from_seated_to_offset"],
        ):
            pose = report["sampled_poses"][step["pose_id"]]
            assert (
                step["positive_volume_hit_count"] == pose["positive_volume_hit_count"]
            )
            assert step["positive_volume_hits_record_ref"] == (
                f"sampled_poses/{step['pose_id']}/positive_volume_hits"
            )
            assert (
                step["nearest_nonpenetrating_gap"] == pose["nearest_nonpenetrating_gap"]
            )
    assert all(value is False for value in report["release"].values())
