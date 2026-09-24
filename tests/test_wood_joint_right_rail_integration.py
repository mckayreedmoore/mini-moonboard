"""Focused tests for unioned source and candidate machining on shared rails."""

from __future__ import annotations

import json
import math
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_right_rail_integration as integration


def _axis(x: float, y: float) -> cq.Shape:
    return cq.Solid.makeCylinder(0.4, 12.0, cq.Vector(x, y, 0), cq.Vector(0, 0, 1))


def test_shared_host_omits_only_replaced_sds_and_applies_both_trial_bores():
    raw = cq.Solid.makeBox(12.0, 12.0, 12.0)
    source_cutters = {
        "shared_rail": {
            "retained_sds": _axis(2.0, 2.0),
            "replaced_wj04_sds": _axis(5.0, 5.0),
            "replaced_wj06_sds": _axis(6.0, 6.0),
        }
    }
    candidate_bores = {
        "shared_rail": {
            "wj04/trial/lower_rail_1": _axis(8.0, 8.0),
            "wj06/trial/lower_rail_1": _axis(10.0, 10.0),
        }
    }

    hosts = integration.machine_shared_hosts(
        {"shared_rail": raw},
        source_cutters,
        replaced_source_axis_ids={"replaced_wj04_sds", "replaced_wj06_sds"},
        candidate_bores_by_host=candidate_bores,
    )

    finished = hosts["shared_rail"]
    assert raw.Volume() == pytest.approx(12.0**3)
    assert finished.intersect(
        source_cutters["shared_rail"]["retained_sds"]
    ).Volume() == pytest.approx(0.0)
    assert finished.intersect(
        candidate_bores["shared_rail"]["wj04/trial/lower_rail_1"]
    ).Volume() == pytest.approx(0.0)
    assert finished.intersect(
        candidate_bores["shared_rail"]["wj06/trial/lower_rail_1"]
    ).Volume() == pytest.approx(0.0)

    old_wj04_hole_probe = _axis(5.0, 5.0)
    old_wj06_hole_probe = _axis(6.0, 6.0)
    expected_probe_volume = math.pi * 0.4**2 * 12.0
    assert finished.intersect(old_wj04_hole_probe).Volume() == pytest.approx(
        expected_probe_volume
    )
    assert finished.intersect(old_wj06_hole_probe).Volume() == pytest.approx(
        expected_probe_volume
    )


def test_shared_host_rejects_removing_an_axis_missing_from_source_cutters():
    raw = cq.Solid.makeBox(12.0, 12.0, 12.0)

    with pytest.raises(ValueError, match="not present in the source cutter map"):
        integration.machine_shared_hosts(
            {"shared_rail": raw},
            {"shared_rail": {"retained_sds": _axis(2.0, 2.0)}},
            replaced_source_axis_ids={"unknown_sds"},
            candidate_bores_by_host={},
        )


def test_retained_sds_protection_uses_occupied_source_axis_extent():
    source_axis = SimpleNamespace(
        name="retained_sds",
        kind="screw",
        diameter=0.5,
        length=10.0,
        start=cq.Vector(2.0, 3.0, 4.0),
        direction=cq.Vector(0.0, 0.0, 2.0),
    )

    occupied = integration._source_screw_axis_shape(source_axis)
    bounds = occupied.BoundingBox()

    assert bounds.zmin == pytest.approx(4.0)
    assert bounds.zmax == pytest.approx(14.0)
    assert occupied.Volume() == pytest.approx(math.pi * 0.25**2 * 10.0)


def test_ordinary_class_maximum_changes_only_wj06_side_shaft_envelope():
    nominal = integration.wj06_outer.build_stacks()["lower_side_1"]
    maximum = integration._ordinary_body_maximum_side_stack(nominal)
    maximum_shaft = maximum.shaft_shape()

    assert integration.ORDINARY_BOLT_BODY_MAXIMUM_IN == 0.260
    assert integration.INCH_TO_MM == 25.4
    assert integration.ORDINARY_BOLT_BODY_MAXIMUM_MM == pytest.approx(6.604)
    assert nominal.hardware.steel_diameter_mm == pytest.approx(6.35)
    assert maximum.hardware.steel_diameter_mm == pytest.approx(6.35)
    assert nominal.hardware.cad_occupied_diameter_mm == pytest.approx(6.35)
    assert maximum.hardware.cad_occupied_diameter_mm == pytest.approx(6.604)
    assert maximum.hardware.drill_diameter_mm == nominal.hardware.drill_diameter_mm
    assert (
        maximum.hardware.under_head_length_mm == nominal.hardware.under_head_length_mm
    )
    assert maximum.head_seat == nominal.head_seat
    assert maximum.nut_seat == nominal.nut_seat
    assert maximum.direction == nominal.direction
    assert maximum_shaft.BoundingBox().ylen == pytest.approx(6.604)


def test_ordinary_body_maximum_document_is_pinned_as_an_input():
    inputs = integration._source_inputs_sha256()

    assert (
        integration.ORDINARY_BODY_MAXIMUM_SOURCE
        == "docs/wood-joints-mvp/hypotheses/current-hardware-schedule-audit.md"
    )
    assert len(inputs[integration.ORDINARY_BODY_MAXIMUM_SOURCE]) == 64


def test_pinned_inventory_adapter_uses_lightweight_validated_loader():
    binding = SimpleNamespace(
        inventory_sha256=integration.WJ04_TRIAL.source_inventory_sha256
    )

    inventory = integration._load_pinned_source_inventory(binding)

    assert inventory["candidate"] == integration.wj06_outer.CANDIDATE
    assert len(inventory["legacy_duties"]) == 24
    assert sum(len(row["legacy_sds_axes"]) for row in inventory["legacy_duties"]) == 144
    assert len(inventory["fixed_panel_kicker_screws"]) == 66
    assert len(inventory["starting_frame_bolts"]) == 12


def test_side_shaft_sensitivity_screens_wood_protected_and_installed_geometry():
    source_stacks = integration.wj06_outer.build_stacks()
    by_id = {spec.stack_id: spec for spec in integration.wj06_outer.STACK_SPECS}
    stacks = {
        integration._namespace(
            integration.FAMILY_WJ06,
            integration.wj06_outer.TRIAL_ID,
            stack_id,
        ): stack
        for stack_id, stack in source_stacks.items()
        if by_id[stack_id].interface_id == "cleat_to_side"
    }
    installed = {key: stack.installed_shapes() for key, stack in stacks.items()}
    first_key = min(stacks)
    first_stack = stacks[first_key]
    axis = first_stack.under_head_origin
    direction = first_stack.direction
    offset = cq.Vector(0.0, 0.0, 3.2)
    obstacle_start = axis + offset
    thin_obstacle = cq.Solid.makeCylinder(
        0.01,
        first_stack.hardware.under_head_length_mm,
        obstacle_start,
        direction,
    )
    protected_obstacle = cq.Solid.makeCylinder(
        0.01,
        first_stack.hardware.under_head_length_mm,
        axis + cq.Vector(0.0, 3.2, 0.0),
        direction,
    )
    installed["synthetic_peer_stack"] = {"component_probe": thin_obstacle}

    report = integration._side_shaft_envelope_sensitivity(
        stacks,
        installed,
        {"wood_probe": thin_obstacle},
        {"protected_probe": {"protected_shape": protected_obstacle}},
    )

    nominal = report["scenarios"]["nominal"]["per_stack"][first_key]
    maximum = report["scenarios"]["ordinary_class_maximum"]["per_stack"][first_key]
    assert nominal["finished_wood_hits_mm3"] == {}
    assert maximum["finished_wood_hits_mm3"]["wood_probe"] > 0
    assert maximum["protected_geometry_hits_mm3"]["protected_probe"]
    assert (
        maximum["protected_geometry_hits_mm3"]["protected_probe"]["protected_shape"] > 0
    )
    assert (
        maximum["other_installed_components_hits_mm3"][
            "synthetic_peer_stack/component_probe"
        ]
        > 0
    )
    assert maximum["steel_or_design_diameter_mm"] == pytest.approx(6.35)
    assert maximum["cad_occupied_diameter_mm"] == pytest.approx(6.604)
    assert maximum["drilled_bore_diameter_mm"] == pytest.approx(
        first_stack.hardware.drill_diameter_mm
    )
    assert report["basis"]["delivered_fastener_fit_verified"] is False
    assert report["basis"]["capacity_or_joint_acceptance"] is False
    assert (
        report["scenarios"]["ordinary_class_maximum"]["modeled_overlap_present"] is True
    )


def test_diagnostic_report_is_json_safe_and_keeps_release_gates_closed():
    geometry = SimpleNamespace(
        source_binding=SimpleNamespace(
            inventory_sha256="inventory-hash",
            runtime_module_sha256={},
            uncut_part_shapes_sha256="parts-hash",
            uncut_host_shape_sha256={},
            duty_host_mapping={},
            fixed_screw_axes_sha256="panel-hash",
            frame_bolt_axes_sha256="frame-hash",
        ),
        inventory={"candidate": "trial", "source_commit": "historical-commit"},
        source_inputs_sha256={
            "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py": "g7-hash",
            "scripts/wood_joint_wj06_outer_pair_probe.py": "wj06-hash",
        },
        trial_ids={},
        duties={},
        parts={"candidate_cleat": cq.Solid.makeBox(1.0, 1.0, 1.0)},
        replaced_source_axis_ids=frozenset(),
        retained_source_axis_shapes={},
        retained_legacy_clip_shapes={},
        protected={},
        source_reconstruction={},
        machining={},
        candidate_body_hits={},
        body_solid_checks={
            "candidate_cleat": {
                "valid": True,
                "solid_count": 1,
                "volume_mm3": 1.0,
                "valid_single_positive_volume_solid": True,
            }
        },
        stacks={},
        bores={},
        installed={},
        bore_reports={},
        cross_bore_hits_mm3={},
        washer_support={},
        side_shaft_envelope_sensitivity={"status": "assumption-only"},
        installed_hits={},
        panels={},
        diagnostic_gates={"integrated_clearance_review": "not_run"},
        release={"fabrication_released": False},
    )

    report = integration.diagnostic_report(geometry)
    encoded = json.dumps(report)

    assert '"status": "unaccepted integrated trial geometry"' in encoded
    assert report["candidate_bodies"]["candidate_cleat"][
        "valid_single_positive_volume_solid"
    ]
    assert report["claim_boundary"]["integrated_clearance_accepted"] is False
    assert report["release"]["fabrication_released"] is False
    assert report["side_shaft_envelope_sensitivity"]["status"] == "assumption-only"
