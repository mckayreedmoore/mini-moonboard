"""Synthetic checks for exact coaxial bolt-shaft withdrawal supplement."""

import hashlib
import json
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_frame import BoltStack
from mini_moonboard.wood_joint_geometry import (
    BoltHardware,
    StackLayer,
    WasherSeat,
)
from scripts import wood_joint_wj03_compact_outer_access as compact_access
from scripts import wood_joint_wj03_compact_outer_tools as compact_tools
from scripts import wood_joint_wj03_head_withdrawal as withdrawal
from scripts import wood_joint_wj03_head_withdrawal_exact_shaft as exact_shaft


def _stack(stack_id="synthetic_00", origin=None, direction=None):
    hardware = BoltHardware(
        candidate_sku="synthetic provisional 1/4-20 through-bolt",
        under_head_length_mm=10.0,
        steel_diameter_mm=6.35,
        cad_occupied_diameter_mm=6.35,
        drill_diameter_mm=7.5,
        head_diameter_mm=12.827,
        head_height_mm=4.1656,
        washer_od_mm=18.6436,
        washer_id_mm=8.0,
        washer_thickness_mm=1.651,
        nut_diameter_mm=12.827,
        nut_height_mm=5.7404,
        usable_thread_start_mm=0.0,
        usable_thread_end_mm=10.0,
    )
    origin = cq.Vector(origin or (0, 0, 30))
    direction = cq.Vector(direction or (0, 0, 1))
    layers = (StackLayer("host_head", 4.0), StackLayer("host_nut", 4.0))
    head_seat = origin + direction * hardware.washer_thickness_mm
    nut_seat = head_seat + direction * 8.0
    return BoltStack(
        id=stack_id,
        hardware=hardware,
        under_head_origin=origin,
        direction=direction,
        layers=layers,
        head_seat=WasherSeat("host_head", head_seat, direction),
        nut_seat=WasherSeat("host_nut", nut_seat, -direction),
    )


def _synthetic_geometry():
    stacks = {}
    installed = {}
    for index in range(compact_tools.STACK_COUNT):
        stack_id = f"synthetic_{index:02d}"
        stack = _stack(stack_id, (index * 500.0, 0, 300.0))
        stacks[stack_id] = stack
        installed.update(
            {
                f"wj03/{stack_id}/{role}": shape
                for role, shape in stack.installed_shapes().items()
            }
        )
    return SimpleNamespace(
        trial_id=compact_access.TRIAL_ID,
        source_binding={"synthetic": "source"},
        source_pins={"synthetic": "geometry-pin"},
        floor_z_mm=0.0,
        stacks=stacks,
        panels={},
        staged_panels={},
        finished_wood={
            "synthetic_body": cq.Solid.makeBox(
                20.0, 20.0, 20.0, cq.Vector(99999.0, 500.0, 10.0)
            )
        },
        protected={"solids": {}},
        tnut_owners={},
        installed_hardware=installed,
        wj05_bolts={},
        wj05_stacks={},
    )


def test_exact_cylinder_clears_hole_and_washer_where_bbox_box_hits():
    stack = _stack()
    shaft = stack.shaft_shape()
    exact, record = exact_shaft._shaft_sweep(stack, shaft)
    coarse = exact_shaft.tool_access.translation_sweep(
        shaft, -cq.Vector(stack.direction) * stack.hardware.under_head_length_mm
    )

    washer = cq.Solid.makeCylinder(
        stack.hardware.washer_od_mm / 2,
        stack.hardware.washer_thickness_mm,
        cq.Vector(0, 0, 31.651),
        cq.Vector(0, 0, 1),
    ).cut(
        cq.Solid.makeCylinder(
            stack.hardware.washer_id_mm / 2,
            stack.hardware.washer_thickness_mm,
            cq.Vector(0, 0, 31.651),
            cq.Vector(0, 0, 1),
        )
    )
    wood = cq.Solid.makeBox(20.0, 20.0, 10.0, cq.Vector(-10, -10, 30)).cut(
        cq.Solid.makeCylinder(7.5 / 2, 10.0, cq.Vector(0, 0, 30), cq.Vector(0, 0, 1))
    )

    exact_report = exact_shaft.tool_access.collision_report(
        {"exact": exact}, {"washer_ring": washer, "drilled_wood": wood}
    )
    coarse_report = exact_shaft.tool_access.collision_report(
        {"coarse": coarse}, {"washer_ring": washer, "drilled_wood": wood}
    )

    assert exact_report["external_envelope_clear"] is True
    assert coarse_report["external_envelope_clear"] is False
    assert set(coarse_report["external_envelope_hits_mm3"]["coarse"]) == {
        "drilled_wood",
        "washer_ring",
    }
    assert record["source_length_mm"] == pytest.approx(10.0)
    assert record["withdrawal_travel_mm"] == pytest.approx(10.0)
    assert record["sweep_length_mm"] == pytest.approx(20.0)
    assert record["radius_mm"] == pytest.approx(6.35 / 2)
    assert record["source_center_and_volume_verified_against_installed_shape"] is True


def test_archived_source_and_markdown_hashes_are_required():
    base_data = json.loads(exact_shaft.DEFAULT_BASE_REPORT.read_text())
    validation = exact_shaft.validate_base_report()
    assert validation["sha256"] == exact_shaft.ARCHIVED_BASE_REPORT_SHA256
    assert validation["schema"] == withdrawal.SCHEMA

    stale_data = json.loads(json.dumps(base_data))
    stale_path = next(iter(stale_data["source_pins"]["head_withdrawal_direct_inputs"]))
    stale_data["source_pins"]["head_withdrawal_direct_inputs"][stale_path] = "0" * 64
    with pytest.raises(ValueError, match="archived head-withdrawal input changed"):
        exact_shaft._validate_archived_base(exact_shaft.DEFAULT_BASE_REPORT, stale_data)


def test_supplement_pins_archived_base_and_screens_only_exact_shafts(
    monkeypatch, tmp_path
):
    geometry = _synthetic_geometry()
    direct_producer_sha = hashlib.sha256(
        (exact_shaft.ROOT / "scripts/wood_joint_wj03_head_withdrawal.py").read_bytes()
    ).hexdigest()
    base_data = {
        "schema": withdrawal.SCHEMA,
        "trial_id": geometry.trial_id,
        "source_binding": geometry.source_binding,
        "source_pins": {
            "geometry_materializer_inputs": geometry.source_pins,
            "head_withdrawal_direct_inputs": {
                "scripts/wood_joint_wj03_head_withdrawal.py": direct_producer_sha
            },
        },
        "candidate_stack_count": compact_tools.STACK_COUNT,
        "stacks": {
            stack_id: {
                "bolt_withdrawal_after_unthreading": {
                    "shaft_path": {
                        "external_envelope_hits_mm3": {
                            "shaft_axial_withdrawal": {
                                "finished_wood/synthetic_body": 1.0,
                                "tool_pair/stationary_nut_ratchet/heading_+90deg/ratchet_head": 0.2,
                            }
                        }
                    }
                }
            }
            for stack_id in geometry.stacks
        },
    }
    base_path = tmp_path / "base.json"
    base_path.write_text(json.dumps(base_data, sort_keys=True))
    base_hash = hashlib.sha256(base_path.read_bytes()).hexdigest()

    calls = []

    def record_collision(
        candidate_shapes,
        obstacles,
        *,
        excluded_target_ids=(),
        exclusion_scope="",
    ):
        excluded = set(excluded_target_ids)
        assert excluded <= set(obstacles)
        calls.append(
            {
                "candidate_names": set(candidate_shapes),
                "obstacle_names": set(obstacles),
                "excluded": excluded,
                "exclusion_scope": exclusion_scope,
            }
        )
        heading_hits = {}
        if any("heading_+0deg/" in name for name in obstacles):
            heading_hits = {
                "exact_coaxial_shaft_withdrawal": {
                    next(name for name in obstacles if "heading_+0deg/" in name): 1.0
                }
            }
        return {
            "external_envelope_hits_mm3": heading_hits,
            "external_envelope_clear": not heading_hits,
            "excluded_target_obstacle_ids": sorted(excluded),
            "exclusion_scope": exclusion_scope,
            "physical_access_established": False,
        }

    monkeypatch.setattr(exact_shaft.tool_access, "collision_report", record_collision)
    report = exact_shaft.build_exact_shaft_supplement(
        geometry, base_report_path=base_path
    )

    assert report["schema"] == exact_shaft.SCHEMA
    assert report["base_report"]["sha256"] == base_hash
    assert report["candidate_stack_count"] == 20
    assert report["summary"]["archived_aabb_hit_stacks"] == 20
    assert report["summary"]["exact_fixed_obstacle_clear_stacks"] == 20
    assert (
        report["summary"]["stacks_with_at_least_one_sampled_counterhold_heading_clear"]
        == 20
    )
    assert report["release_claims"]["shaft_withdrawal_access_established"] is False
    assert len(calls) == compact_tools.STACK_COUNT * 5
    for row in report["stacks"].values():
        assert row["archived_aabb_hit_obstacle_ids"] == [
            "finished_wood/synthetic_body",
            "tool_pair/stationary_nut_ratchet/heading_+90deg/ratchet_head",
        ]
        assert row["archived_counterhold_heading_union_hit_ids"] == [
            "tool_pair/stationary_nut_ratchet/heading_+90deg/ratchet_head"
        ]
        assert row["aabb_only_nonheading_obstacle_ids"] == [
            "finished_wood/synthetic_body"
        ]
        assert row["exact_fixed_obstacle_hit_ids"] == []
        heading_screens = row["stationary_nut_ratchet_heading_screens"]
        assert heading_screens["+0deg"]["ratchet_heading_hit_obstacle_ids"]
        assert not heading_screens["+0deg"]["sampled_pose_clear_with_this_heading"]
        assert heading_screens["+0deg"]["exact_sweep_hit_obstacle_ids"]
        for heading in ("+90deg", "+180deg", "+270deg"):
            assert heading_screens[heading]["ratchet_heading_hit_obstacle_ids"] == []
            assert heading_screens[heading]["sampled_pose_clear_with_this_heading"]
        assert row["shaft_sweep_geometry"][
            "source_center_and_volume_verified_against_installed_shape"
        ]
        assert row["analytic_sweep_collision"]["excluded_target_obstacle_ids"] == [
            "tool_pair/stationary_nut_socket"
        ]
    first_call = calls[0]
    assert first_call["candidate_names"] == {"exact_coaxial_shaft_withdrawal"}
    assert "finished_wood/synthetic_body" in first_call["obstacle_names"]
    assert not any(
        "stationary_nut_ratchet/" in name for name in first_call["obstacle_names"]
    )
    for call in calls[1::5]:
        headings = {
            name.split("stationary_nut_ratchet/", 1)[1].split("/", 1)[0]
            for name in call["obstacle_names"]
        }
        assert len(headings) == 1
