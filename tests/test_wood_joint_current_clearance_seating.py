"""Focused tests for the frozen ordinary-patch clearance geometry witness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from fea.wood_joint_current_clearance_seating import (
    DEFAULT_CLASSIFICATION,
    DEFAULT_INVENTORY,
    DEFAULT_MATERIAL_MAP,
    build_current_clearance_seating_witness,
)

ROOT = Path(__file__).resolve().parents[1]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def _canonical_sha256(value):
    without_hash = {key: row for key, row in value.items() if key != "record_sha256"}
    payload = json.dumps(
        without_hash, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_frozen_ordinary_patch_clearance_chain_is_two_times_115_mm():
    witness = build_current_clearance_seating_witness()

    assert witness["candidate"]["revision_id"] == (
        "led-clearance-2x6-runner-seated-blocks-v1"
    )
    assert witness["candidate"]["ordinary_patch_wood_body_count"] == 3
    assert witness["candidate"]["ordinary_patch_physical_bolt_count"] == 4
    assert witness["direction"]["name"] == "cleat longitudinal grain N"
    assert witness["direction"]["source_grain_axis_global_xyz"] == [
        0.0,
        -0.766044443,
        0.64278761,
    ]
    assert (
        witness["member_grain_axes"]["base_rail_bottom_right"]["grain_axis_local_name"]
        == "X"
    )
    assert (
        witness["member_grain_axes"]["base_principal_center_right"][
            "grain_axis_local_name"
        ]
        == "T"
    )

    by_interface = {
        row["interface_id"]: row
        for row in witness["chain"]["bolted_interfaces_in_order"]
    }
    assert len(by_interface) == 2
    assert all(
        row["common_translation_only_free_travel_mm"] == pytest.approx(1.15)
        for row in by_interface.values()
    )
    assert all(
        travel == pytest.approx(1.15)
        for row in by_interface.values()
        for travel in row["individual_bolt_center_separation_mm"]
    )
    assert witness["chain"]["translation_only_freely_floating_pin_travel_mm"] == (
        pytest.approx(2.30)
    )
    assert witness["chain"]["direct_face_normals_are_tangent_to_N"] is True
    assert witness["chain"]["direct_wood_face_normal_contact_resists_N"] is False

    rail_axes = [
        row
        for row in witness["bolts"].values()
        if row["interface_id"] == "bottom_center_right_cleat_to_base_rail_bottom_right"
    ]
    principal_axes = [
        row
        for row in witness["bolts"].values()
        if row["interface_id"]
        == "bottom_center_right_cleat_to_base_principal_center_right"
    ]
    assert len(rail_axes) == len(principal_axes) == 2
    assert all(
        row["axis_direction_head_to_nut_global_xyz"] == [0.0, -0.64278761, -0.766044443]
        for row in rail_axes
    )
    assert all(
        row["axis_direction_head_to_nut_global_xyz"] == [-1.0, 0.0, 0.0]
        for row in principal_axes
    )
    assert all(
        abs(row["unit_axis_dot_cleat_N"]) <= 1e-6 for row in witness["bolts"].values()
    )
    for interface in witness["wood_interfaces"].values():
        assert all(
            abs(face["unit_normal_dot_cleat_N"]) <= 1e-6
            for face in interface["opposed_face_normals"]
        )

    assert witness["scope"]["member_rotations_included"] is False
    assert witness["scope"]["member_rotations_constrained_or_accepted"] is False
    assert witness["scope"]["native_solve_run"] is False
    assert witness["scope"]["capacity_claim"] is False
    assert witness["record_sha256"] == _canonical_sha256(witness)
    for binding in witness["input_bindings"].values():
        path = ROOT / binding["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"]
    producer = witness["producer_binding"]
    assert (
        hashlib.sha256((ROOT / producer["path"]).read_bytes()).hexdigest()
        == (producer["sha256"])
    )


def test_witness_rejects_changed_receiver_clearance(tmp_path):
    classification = json.loads(DEFAULT_CLASSIFICATION.read_text(encoding="utf-8"))
    classification["bolt_receiver_bore_pairs"][0]["receiver_bore_walls"][0][
        "radial_clearance_mm"
    ] = 0.576
    changed = tmp_path / "classification.json"
    changed.write_text(json.dumps(classification), encoding="utf-8")

    with pytest.raises(ValueError, match="receiver radial gap changed"):
        build_current_clearance_seating_witness(
            DEFAULT_INVENTORY,
            changed,
            DEFAULT_MATERIAL_MAP,
        )
