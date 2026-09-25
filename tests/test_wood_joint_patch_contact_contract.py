"""Focused provenance and finite-face tests for the WJ04 contact fragment."""

from __future__ import annotations

import copy
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from fea import wood_joint_patch_classification as surface_contract
from fea import wood_joint_patch_contact_contract as contract
from fea import wood_joint_patch_mesh as wood_mesh_contract


def _tri6_mesh() -> contract.MeshInput:
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    refs = []
    for element_id, station_case in enumerate(
        ("inside", "upper-crossing", "outside"), start=1
    ):
        points = [
            (0.2, 0.0, 0.0),
            (0.8, 0.0, 0.0),
            (0.5, 1.0, 0.0),
            (0.5, 0.0, 1.0),
            (0.5, 0.0, 0.0),
            (0.65, 0.5, 0.0),
            (0.35, 0.5, 0.0),
            (0.35, 0.0, 0.5),
            (0.65, 0.0, 0.5),
            (0.5, 0.5, 0.5),
        ]
        if station_case == "upper-crossing":
            # The three corner stations and their centroid remain in range;
            # one TRI6 midside node crosses the upper interval boundary.
            points[4] = (1.2, 0.0, 0.0)
        elif station_case == "outside":
            points = [(x + 1.1, y, z) for x, y, z in points]
        first_node = (element_id - 1) * 10 + 1
        nodes.update(
            {first_node + offset: point for offset, point in enumerate(points)}
        )
        elements[element_id] = tuple(range(first_node, first_node + 10))
        refs.append([element_id, 1])
    return contract.MeshInput(
        source_kind="metal",
        report_path=Path("mesh.json"),
        deck_path=Path("mesh.inp"),
        report={},
        report_sha256="a" * 64,
        deck_sha256="b" * 64,
        nodes=nodes,
        elements=elements,
        body_nodes={"bolt": tuple(nodes)},
        body_elements={"bolt": (1, 2, 3)},
        body_surfaces={
            "bolt": {
                "1": {"cad_entity_tag": 1, "tri6_exterior_face_refs": refs},
            }
        },
    )


def _classification_fixture() -> tuple[
    dict[str, Any],
    contract.MeshInput,
    dict[tuple[str, str], dict[str, Any]],
    dict[str, Any],
    str,
    dict[str, Any],
    str,
]:
    patch_hash = "c" * 64
    mechanics_hash = "d" * 64
    mesh_nodes: dict[int, tuple[float, float, float]] = {}
    mesh_elements: dict[int, tuple[int, ...]] = {}
    body_nodes: dict[str, tuple[int, ...]] = {}
    body_elements: dict[str, tuple[int, ...]] = {}
    body_surfaces: dict[str, dict[str, dict[str, Any]]] = {}
    next_node = 1
    for element_id, body_id in enumerate(wood_mesh_contract.WOOD_BODY_IDS, start=1):
        ids = tuple(range(next_node, next_node + 10))
        next_node += 10
        mesh_nodes.update({node: (float(node), 0.0, 0.0) for node in ids})
        mesh_elements[element_id] = ids
        body_nodes[body_id] = ids
        body_elements[body_id] = (element_id,)
        body_surfaces[body_id] = {
            "1": {
                "cad_entity_tag": 1,
                "tri6_exterior_face_refs": [[element_id, 1]],
            }
        }
    mesh = contract.MeshInput(
        source_kind="wood",
        report_path=Path("wood-mesh.json"),
        deck_path=Path("wood-mesh.inp"),
        report={"input_bundle_inventory_sha256": patch_hash},
        report_sha256="1" * 64,
        deck_sha256="2" * 64,
        nodes=mesh_nodes,
        elements=mesh_elements,
        body_nodes=body_nodes,
        body_elements=body_elements,
        body_surfaces=body_surfaces,
    )

    mechanics_bolts = []
    patch_bolts = []
    bore_rows = []
    for stack_id in contract.STACK_IDS:
        interface_id = next(
            key
            for key, stack_ids in wood_mesh_contract.EXPECTED_INTERFACE_STACKS.items()
            if stack_id in stack_ids
        )
        receiver_ids = wood_mesh_contract.STACK_RECEIVERS[stack_id]
        receiver_rows = [
            {"member_id": receiver_ids[0], "wood_thickness_mm": 4.0},
            {"member_id": receiver_ids[1], "wood_thickness_mm": 6.0},
        ]
        bolt = {
            "stack_spec_id": stack_id,
            "physical_bolt_id": f"physical/{stack_id}",
            "interface_id": interface_id.split("__", 1)[-1],
            "receivers_head_to_nut": receiver_rows,
            "wood_grip_mm": 10.0,
            "world_axis_origin_xyz_mm": [0.0, 0.0, 0.0],
            "world_axis_direction_head_to_nut": [0.0, 0.0, 1.0],
        }
        mechanics_bolts.append(bolt)
        patch_bolts.append(
            {
                "stack_spec_id": stack_id,
                "physical_bolt_id": bolt["physical_bolt_id"],
                "interface_id": interface_id,
                "receivers_head_to_nut": copy.deepcopy(receiver_rows),
                "wood_grip_mm": 10.0,
                "world_axis_origin_xyz_mm": [0.0, 0.0, 0.0],
                "world_axis_direction_head_to_nut": [0.0, 0.0, 1.0],
                "composed_occupancy_bore": {"volume_mm3": 100.0},
            }
        )
        for receiver_index, receiver in enumerate(receiver_rows):
            low = 0.0 if receiver_index == 0 else 4.0
            high = 4.0 if receiver_index == 0 else 10.0
            bore_rows.append(
                {
                    "semantic_pair_id": f"{stack_id}::{receiver['member_id']}",
                    "stack_spec_id": stack_id,
                    "physical_bolt_id": bolt["physical_bolt_id"],
                    "interface_id": interface_id,
                    "member_id": receiver["member_id"],
                    "receiver_order_head_to_nut": list(receiver_ids),
                    "receiver_layer_station_mm": [low, high],
                    "axis_origin_xyz_mm": [0.0, 0.0, 0.0],
                    "axis_direction_head_to_nut": [0.0, 0.0, 1.0],
                    "analysis_occupancy_bore_radius_mm": math.sqrt(
                        100.0 / (math.pi * 10.2)
                    ),
                    "occupancy_bore_is_hardware_or_drill_instruction": False,
                    "matched_surfaces": [{"cad_entity_tag": 1}],
                    "contact_or_strength_result": False,
                }
            )

    interface_rows = []
    wood_pairs = []
    normal_rows = {}
    for interface_id, stack_ids in wood_mesh_contract.EXPECTED_INTERFACE_STACKS.items():
        members = list(wood_mesh_contract.STACK_RECEIVERS[stack_ids[0]])
        candidate = next(
            member
            for member in members
            if wood_mesh_contract.EXPECTED_BODY_ROLES[member]
            == "finished_candidate_part"
        )
        host = next(member for member in members if member != candidate)
        interface_rows.append(
            {
                "interface_id": interface_id,
                "family_stack_ids": list(stack_ids),
                "members_head_to_nut": members,
                "candidate_cleat_face": {"part_id": candidate},
                "source_host_face": {"part_id": host},
            }
        )
        wood_pairs.append(
            {
                "interface_id": interface_id,
                "candidate_member_id": candidate,
                "host_member_id": host,
                "candidate_surfaces": [{"cad_entity_tag": 1}],
                "host_surfaces": [{"cad_entity_tag": 1}],
                "archived_finite_common_area_mm2": 10.0,
                "host_area_is_not_equated_to_common_footprint": True,
                "active_pressure_established": False,
            }
        )
        for member in members:
            normal_rows[(interface_id, member)] = {"exterior_tri6_face_count": 1}

    mechanics = {
        "physical_bolts": mechanics_bolts,
        "physical_interfaces": interface_rows,
    }
    patch_inventory = {
        "schema": "wood_joint_wj04_patch_geometry/v1",
        "status": "source_bound_finished_geometry_export_inputs_only",
        "composition": {
            "mechanics_manifest_sha256": mechanics_hash,
            "live_composition_report_matches_archive": True,
        },
        "physical_bolts": patch_bolts,
    }
    classification = {
        "schema": surface_contract.SCHEMA,
        "status": "SOURCE_BOUND_GEOMETRIC_SURFACE_CLASSIFICATION_ONLY",
        "native_solve_run": False,
        "contact_law_assigned": False,
        "source_hashes": {
            "mesh.json": mesh.report_sha256,
            "mesh.inp": mesh.deck_sha256,
            "patch_bundle/inventory.json": patch_hash,
        },
        "wood_contact_pairs": wood_pairs,
        "candidate_bore_member_pairs": bore_rows,
    }
    return (
        classification,
        mesh,
        normal_rows,
        mechanics,
        mechanics_hash,
        patch_inventory,
        patch_hash,
    )


def _validate_fixture(fixture):
    (
        classification,
        mesh,
        normal_rows,
        mechanics,
        mechanics_hash,
        inventory,
        inventory_hash,
    ) = fixture
    return contract._validate_surface_classification(
        classification,
        "f" * 64,
        mesh,
        normal_rows,
        mechanics,
        mechanics_hash,
        inventory,
        inventory_hash,
    )


def test_axial_clip_checks_all_six_tri6_nodes_and_accounts_for_boundary_faces():
    selected, tags, audit = contract._select_axial_faces(
        _tri6_mesh(), "bolt", (1,), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.0, 1.0
    )

    assert selected == ((1, 1),)
    assert tags == ("1",)
    assert audit["method"] == "all_six_TRI6_face_nodes_inside_interval"
    assert audit["source_face_count"] == 3
    assert audit["selected_face_count"] == 1
    assert audit["boundary_excluded_face_count"] == 1
    assert audit["outside_interval_face_count"] == 1
    assert audit["selected_chord_area_estimate_mm2"] > 0
    assert 0 < audit["contained_area_fraction_of_touched_faces"] < 1


def test_axial_boundary_exclusions_keep_diagnostic_fragment_unready():
    _selected, _tags, audit = contract._select_axial_faces(
        _tri6_mesh(), "bolt", (1,), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.0, 1.0
    )
    pair = {
        "pair_id": "stack::receiver::bolt_bore",
        "category": "bolt_shank_to_receiver_bore",
        "slave": {
            "owner_body": "stack__bolt",
            "axial_face_selection_audit": audit,
        },
        "master": {"owner_body": "receiver"},
    }

    readiness = contract._response_readiness([pair])

    assert readiness["status"] == "NOT_RESPONSE_READY_AXIAL_BOUNDARY_EXCLUSIONS"
    assert readiness["response_ready"] is False
    assert readiness["axial_contact_patch_coverage_ready"] is False
    assert readiness["boundary_excluded_face_count"] == 1
    assert readiness["boundary_excluded_chord_area_estimate_mm2"] > 0
    assert readiness["chord_area_is_exact_interval_omission"] is False
    assert (
        readiness["unresolved_boundary_exclusions"][0][
            "true_interval_omitted_area_known"
        ]
        is False
    )


def test_axial_patch_coverage_can_pass_without_boundary_exclusions_but_response_stays_unready():
    mesh = _tri6_mesh()
    mesh.body_surfaces["bolt"]["1"]["tri6_exterior_face_refs"] = [[1, 1]]
    _selected, _tags, audit = contract._select_axial_faces(
        mesh, "bolt", (1,), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.0, 1.0
    )
    pair = {
        "pair_id": "stack::receiver::bolt_bore",
        "category": "bolt_shank_to_receiver_bore",
        "slave": {"axial_face_selection_audit": audit},
        "master": {},
    }

    readiness = contract._response_readiness([pair])

    assert readiness["status"] == "NOT_RESPONSE_READY_INCOMPLETE_MODEL"
    assert readiness["response_ready"] is False
    assert readiness["axial_contact_patch_coverage_ready"] is True
    assert readiness["unresolved_boundary_exclusions"] == []


def test_axial_contact_pair_without_selection_audit_is_unready():
    readiness = contract._response_readiness(
        [
            {
                "pair_id": "stack::receiver::bolt_bore",
                "category": "bolt_shank_to_receiver_bore",
                "slave": {},
                "master": {},
            }
        ]
    )

    assert readiness["axial_contact_patch_coverage_ready"] is False
    assert readiness["axial_pairs_missing_selection_audit"] == [
        "stack::receiver::bolt_bore"
    ]


def test_axial_clip_rejects_duplicate_or_foreign_source_face_ownership():
    mesh = _tri6_mesh()
    mesh.body_surfaces["bolt"]["2"] = {
        "cad_entity_tag": 2,
        "tri6_exterior_face_refs": [[1, 1]],
    }
    with pytest.raises(ValueError, match="repeat a TRI6 face"):
        contract._select_axial_faces(
            mesh, "bolt", (1, 2), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.0, 1.0
        )

    mesh.body_elements["bolt"] = (2, 3)
    with pytest.raises(ValueError, match="outside its body ownership"):
        contract._select_axial_faces(
            mesh, "bolt", (1,), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.0, 1.0
        )


def test_mechanics_receiver_members_must_match_the_frozen_order():
    stack_id = "lower_rail_1"
    expected = wood_mesh_contract.STACK_RECEIVERS[stack_id]
    bolt = {
        "receivers_head_to_nut": [
            {"member_id": expected[0]},
            {"member_id": expected[1]},
        ]
    }
    interface = {"members_head_to_nut": list(expected)}
    assert (
        contract._validate_ordered_receiver_ownership(stack_id, bolt, interface)
        == expected
    )

    with pytest.raises(ValueError, match="frozen physical receiver mapping"):
        contract._validate_ordered_receiver_ownership(
            stack_id,
            {"receivers_head_to_nut": list(reversed(bolt["receivers_head_to_nut"]))},
            interface,
        )
    with pytest.raises(ValueError, match="interface member order"):
        contract._validate_ordered_receiver_ownership(
            stack_id, bolt, {"members_head_to_nut": list(reversed(expected))}
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        ("duplicate", "repeats a bolt-bore owner pair"),
        ("axis", "bore axis origin differs"),
        ("interval", "receiver interval differs"),
        ("receiver_order", "bore receiver ordering differs"),
    ],
)
def test_bore_rows_are_unique_and_bound_to_mechanics(mutate, message):
    fixture = list(_classification_fixture())
    classification = copy.deepcopy(fixture[0])
    rows = classification["candidate_bore_member_pairs"]
    if mutate == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif mutate == "axis":
        rows[0]["axis_origin_xyz_mm"] = [1.0, 0.0, 0.0]
    elif mutate == "interval":
        rows[0]["receiver_layer_station_mm"] = [0.0, 5.0]
    else:
        rows[0]["receiver_order_head_to_nut"] = list(
            reversed(rows[0]["receiver_order_head_to_nut"])
        )
    fixture[0] = classification

    with pytest.raises(ValueError, match=message):
        _validate_fixture(tuple(fixture))


def test_classification_fixture_covers_all_four_interfaces_and_sixteen_receiver_pairs():
    by_interface, bore_rows = _validate_fixture(_classification_fixture())

    assert set(by_interface) == set(contract.EXPECTED_INTERFACE_IDS)
    assert len(bore_rows) == 16
    assert all(row["_resolved_member_refs"] for row in bore_rows)


@pytest.mark.parametrize("source", ["mechanics", "patch"])
def test_physical_bolt_ids_must_be_unique_per_source(source):
    fixture = list(_classification_fixture())
    rows = (
        fixture[3]["physical_bolts"]
        if source == "mechanics"
        else fixture[5]["physical_bolts"]
    )
    rows[1]["physical_bolt_id"] = rows[0]["physical_bolt_id"]

    with pytest.raises(ValueError, match="unique physical bolt IDs"):
        _validate_fixture(tuple(fixture))


def test_hardware_inventory_digest_is_compared_to_mesh_report_bytes(monkeypatch):
    sentinel = ({"stacks": {}}, {("profile", "stack"): {}})
    monkeypatch.setattr(
        contract, "_validate_hardware_inventory_body", lambda *_args: sentinel
    )
    mesh = SimpleNamespace(report={"input_bundle_inventory_sha256": "a" * 64})
    seat_audit = {"hardware_inventory_sha256": "a" * 64}

    assert (
        contract._validate_hardware_inventory_with_sha({}, "a" * 64, mesh, seat_audit)
        == sentinel
    )
    with pytest.raises(ValueError, match="mesh and supplied inventory bytes"):
        contract._validate_hardware_inventory_with_sha({}, "b" * 64, mesh, seat_audit)


def test_patch_inventory_digest_is_bound_to_wood_mesh_and_classification():
    fixture = list(_classification_fixture())
    fixture[0] = copy.deepcopy(fixture[0])
    fixture[0]["source_hashes"]["patch_bundle/inventory.json"] = "9" * 64

    with pytest.raises(ValueError, match="supplied patch inventory"):
        _validate_fixture(tuple(fixture))
