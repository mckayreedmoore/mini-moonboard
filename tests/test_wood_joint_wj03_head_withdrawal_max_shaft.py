"""Synthetic checks for WJ-03 ordinary-body maximum shaft sensitivity."""

import math
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_frame import BoltStack
from mini_moonboard.wood_joint_geometry import BoltHardware, StackLayer, WasherSeat
from scripts import wood_joint_wj03_compact_outer_tools as compact_tools
from scripts import wood_joint_wj03_head_withdrawal_exact_shaft as exact_shaft
from scripts import wood_joint_wj03_head_withdrawal_max_shaft as maximum_shaft


def _stack(stack_id="synthetic_00", origin=(0.0, 0.0, 0.0)):
    hardware = BoltHardware(
        candidate_sku="provisional ordinary 1/4-20 x 6-in through-bolt",
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
    origin_v = cq.Vector(origin)
    direction = cq.Vector(0, 0, 1)
    layers = (StackLayer("host_head", 4.0), StackLayer("host_nut", 4.0))
    head_seat = origin_v + direction * hardware.washer_thickness_mm
    nut_seat = head_seat + direction * 8.0
    return BoltStack(
        id=stack_id,
        hardware=hardware,
        under_head_origin=origin_v,
        direction=direction,
        layers=layers,
        head_seat=WasherSeat("host_head", head_seat, direction),
        nut_seat=WasherSeat("host_nut", nut_seat, -direction),
    )


def test_audit_bound_and_nominal_report_are_pinned_before_materialization():
    result = maximum_shaft.validate_source_reports()
    audit = result["hardware_schedule_audit"]
    assert audit["ordinary_bolt_body_maximum_in"] == pytest.approx(0.260)
    assert audit["ordinary_bolt_body_maximum_mm"] == pytest.approx(6.604)
    assert audit["source_sha256"] == maximum_shaft.SCHEDULE_AUDIT_SHA256
    assert result["nominal_report_sha256"] == maximum_shaft.NOMINAL_REPORT_SHA256
    assert (
        result["coarse_base_report_sha256"] == exact_shaft.ARCHIVED_BASE_REPORT_SHA256
    )


def test_nominal_exact_report_hash_mismatch_fails_closed(monkeypatch):
    original = maximum_shaft._sha256

    def changed_nominal_hash(path: Path) -> str:
        if Path(path).resolve() == maximum_shaft.NOMINAL_REPORT_PATH.resolve():
            return "0" * 64
        return original(path)

    monkeypatch.setattr(maximum_shaft, "_sha256", changed_nominal_hash)
    with pytest.raises(
        ValueError, match="immutable nominal exact-shaft report hash changed"
    ):
        maximum_shaft.validate_source_reports()


def test_alternate_shaft_and_sweep_change_only_circular_occupancy():
    stack = _stack()
    original_hardware = stack.hardware
    nominal_installed = stack.shaft_shape()
    nominal_sweep, nominal_record = exact_shaft._shaft_sweep(stack, nominal_installed)
    audit = maximum_shaft._ordinary_body_maximum_from_audit()
    diameter = audit["ordinary_bolt_body_maximum_mm"]
    alternate, alternate_sweep, record = maximum_shaft._alternate_shaft_and_sweep(
        stack, nominal_installed, diameter
    )

    assert stack.hardware is original_hardware
    assert stack.hardware.steel_diameter_mm == pytest.approx(6.35)
    assert stack.hardware.cad_occupied_diameter_mm == pytest.approx(6.35)
    assert stack.hardware.drill_diameter_mm == pytest.approx(7.5)
    assert stack.hardware.head_diameter_mm == pytest.approx(12.827)
    assert stack.hardware.nut_diameter_mm == pytest.approx(12.827)
    assert stack.hardware.washer_id_mm == pytest.approx(8.0)
    assert record["nominal_design_diameter_changed"] is False
    assert record["head_seats_nuts_washers_and_bores_changed"] is False
    assert record["same_axis_and_source_length_as_nominal"] is True
    assert record["sku_dimensions_inferred"] is False

    assert alternate.BoundingBox().xlen == pytest.approx(6.604)
    assert alternate.BoundingBox().ylen == pytest.approx(6.604)
    assert alternate.BoundingBox().zlen == pytest.approx(10.0)
    assert alternate_sweep.BoundingBox().zlen == pytest.approx(20.0)
    assert alternate_sweep.Center().toTuple() == pytest.approx(
        nominal_sweep.Center().toTuple()
    )
    assert nominal_record["diameter_mm"] == pytest.approx(6.35)
    assert record["ordinary_class_maximum_cad_occupied_diameter_mm"] == pytest.approx(
        6.604
    )
    assert alternate.Volume() == pytest.approx(math.pi * (6.604 / 2) ** 2 * 10.0)

    near_axis_obstacle = cq.Solid.makeCylinder(
        0.02, 20.0, cq.Vector(3.23, 0, -10), cq.Vector(0, 0, 1)
    )
    nominal_result = maximum_shaft.tool_access.collision_report(
        {"nominal": nominal_sweep}, {"near_axis_obstacle": near_axis_obstacle}
    )
    maximum_result = maximum_shaft.tool_access.collision_report(
        {"maximum": alternate_sweep}, {"near_axis_obstacle": near_axis_obstacle}
    )
    assert nominal_result["external_envelope_clear"] is True
    assert maximum_result["external_envelope_clear"] is False


def test_all_peer_shafts_can_be_replaced_without_mutating_retained_map():
    nominal = {}
    maximum = {}
    for index in range(compact_tools.STACK_COUNT):
        stack = _stack(f"synthetic_{index:02d}", (index * 100.0, 0.0, 0.0))
        key = f"installed_hardware/wj03/{stack.id}/shaft"
        nominal[key] = stack.shaft_shape()
        maximum[key] = maximum_shaft._alternate_shaft_and_sweep(
            stack, nominal[key], 6.604
        )[0]
    nonshaft = cq.Solid.makeBox(5.0, 5.0, 5.0, cq.Vector(0, 0, 0))
    nominal["finished_wood/retained"] = nonshaft

    changed = maximum_shaft._replace_all_modeled_shafts(nominal, maximum)

    assert len(maximum) == compact_tools.STACK_COUNT
    assert all(changed[key] is maximum[key] for key in maximum)
    assert changed["finished_wood/retained"] is nonshaft
    assert all(nominal[key] is not maximum[key] for key in maximum)
    assert all(
        nominal[key].BoundingBox().xlen == pytest.approx(6.35) for key in maximum
    )
