"""Contract tests for the bounded WJ24 tool-operation probe."""

from __future__ import annotations

import copy
import json

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts.wood_joint_wj24_tool_operation_probe import (
    BACKER_ROLES,
    COMPOSITION_PATH,
    DIAGNOSTIC_PATH,
    INVENTORY_PATH,
    ORDINARY_ROLES,
    AxisContract,
    _counterhold_screen,
    _shaft_withdrawal_screen,
    load_archived_wj24_contract,
)


def _archive_triplet() -> tuple[dict, dict, dict]:
    composition = json.loads(COMPOSITION_PATH.read_text())
    inventory = json.loads(INVENTORY_PATH.read_text())
    diagnostic = json.loads(DIAGNOSTIC_PATH.read_text())
    return composition, inventory, diagnostic


def test_archived_wj24_contract_joins_all_real_axes_and_roles() -> None:
    contract = load_archived_wj24_contract()

    assert len(contract.axes) == 104
    assert len(contract.family_trial_ids) == 10
    assert (
        sum(axis.role_ids == ORDINARY_ROLES for axis in contract.axes.values()) == 100
    )
    assert sum(axis.role_ids == BACKER_ROLES for axis in contract.axes.values()) == 4
    assert sum(len(axis.role_ids) for axis in contract.axes.values()) == 520
    assert contract.axes["knee_outer_left_header_1"].station_id is None
    assert contract.axes["backer_header_left_1"].role_ids == BACKER_ROLES

    # The frozen producer artifact has nine source-fingerprint families and
    # ten family-trial bindings. They are intentionally distinct maps.
    composition, _inventory, _diagnostic = _archive_triplet()
    assert len(composition["family_source_fingerprints_sha256"]) == 9
    assert len(composition["family_trial_ids"]) == 10


def test_inventory_axis_role_drift_is_rejected() -> None:
    composition, inventory, diagnostic = _archive_triplet()
    inventory = copy.deepcopy(inventory)
    row = next(
        row
        for row in inventory["candidate_hardware_axis_schedule"]
        if row["axis_id"] == "center_principal_header_left_1"
    )
    row["installed_cad_role_ids"].remove("nut_washer")
    row["cad_role_count"] -= 1

    with pytest.raises(ValueError, match="inventory/composition binding"):
        load_archived_wj24_contract(composition, inventory, diagnostic)


def test_diagnostic_must_name_the_full_archived_axis_set() -> None:
    composition, inventory, diagnostic = _archive_triplet()
    diagnostic = copy.deepcopy(diagnostic)
    diagnostic["counts_and_ids"]["candidate_bore_axes"]["ids"].pop()

    with pytest.raises(ValueError, match="candidate bore axis IDs"):
        load_archived_wj24_contract(composition, inventory, diagnostic)


def test_duplicate_inventory_axis_is_rejected() -> None:
    composition, inventory, diagnostic = _archive_triplet()
    inventory = copy.deepcopy(inventory)
    inventory["candidate_hardware_axis_schedule"].append(
        copy.deepcopy(inventory["candidate_hardware_axis_schedule"][0])
    )

    with pytest.raises(ValueError, match="exactly 104 candidate axes"):
        load_archived_wj24_contract(composition, inventory, diagnostic)


def test_operation_helpers_keep_sampled_counterhold_and_continuous_bolt_scope() -> None:
    axis_id = "fixture_axis"
    roles = {
        "head": cq.Solid.makeCylinder(7, 7, cq.Vector(0, 0, 100), cq.Vector(0, 0, 1)),
        "head_washer": cq.Solid.makeCylinder(
            8, 2, cq.Vector(0, 0, 98), cq.Vector(0, 0, 1)
        ),
        "shaft": cq.Solid.makeCylinder(4, 100, cq.Vector(0, 0, 7), cq.Vector(0, 0, 1)),
        "nut": cq.Solid.makeCylinder(7, 7, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1)),
        "nut_washer": cq.Solid.makeCylinder(
            8, 2, cq.Vector(0, 0, 5), cq.Vector(0, 0, 1)
        ),
    }
    obstacles = {
        f"candidate_stack/{axis_id}/{role}": shape for role, shape in roles.items()
    }

    counterhold = _counterhold_screen(
        axis_id, roles, obstacles, WJ04_TRIAL.fasteners.tools[0]
    )
    assert counterhold["status"] == "sampled_seated_envelopes_only"
    assert counterhold["turning_stroke_screened"] is False
    assert len(counterhold["paired_wrench_pose_overlaps"]) == 4
    first_head_screen = counterhold["head_pose_collision_screens"]["15.0"]
    assert first_head_screen["excluded_target_obstacle_ids"] == [
        f"candidate_stack/{axis_id}/head",
        f"candidate_stack/{axis_id}/shaft",
    ]

    receivers = {}
    for receiver_id, z0 in (("receiver_a", 20), ("receiver_b", 50)):
        block = cq.Solid.makeBox(30, 30, 10, cq.Vector(-15, -15, z0))
        bore = cq.Solid.makeCylinder(6, 10, cq.Vector(0, 0, z0), cq.Vector(0, 0, 1))
        receivers[receiver_id] = block.cut(bore)
    obstacles.update({f"wood/{name}": shape for name, shape in receivers.items()})
    withdrawal = _shaft_withdrawal_screen(
        AxisContract(
            axis_id,
            "fixture_family",
            "fixture_trial",
            "fixture_station",
            ("receiver_a", "receiver_b"),
            ORDINARY_ROLES,
        ),
        roles,
        obstacles,
        receivers,
    )
    assert withdrawal["status"] == "screened_continuous_translation_enclosure"
    assert withdrawal["method"].startswith("continuous linear translation")
    assert (
        withdrawal["shaft_sweep_method"] == "exact_coaxial_cylinder_translation_sweep"
    )
    assert withdrawal["terminal_clearance_margin_mm"] == 0.0
    assert withdrawal["derived_translation_distance_mm"] == 53.0
    assert withdrawal["physical_removal_established"] is False
    assert withdrawal["sweep_collision_screen"]["external_envelope_clear"] is True
    assert withdrawal["sweep_collision_screen"][
        "excluded_target_obstacle_ids"
    ] == sorted(
        [
            f"candidate_stack/{axis_id}/head",
            f"candidate_stack/{axis_id}/head_washer",
            f"candidate_stack/{axis_id}/shaft",
            f"candidate_stack/{axis_id}/nut",
            f"candidate_stack/{axis_id}/nut_washer",
        ]
    )
