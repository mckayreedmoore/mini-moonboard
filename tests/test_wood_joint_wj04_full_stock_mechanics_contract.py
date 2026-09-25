from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_right_rail_integration as right_integration
from scripts import wood_joint_wj04_full_stock_mechanics_contract as contract
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe

ROOT = Path(__file__).resolve().parents[1]


def _basis_box(origin_basis, size_basis) -> cq.Shape:
    shape = cq.Solid.makeBox(
        size_basis[0],
        size_basis[1],
        size_basis[2],
        cq.Vector(0.0, 0.0, 0.0),
    )
    return shape.rotate((0, 0, 0), (1, 0, 0), 50.0).translate(
        WJ04_TRIAL.frame.to_global(origin_basis)
    )


def _inventory_box(row) -> cq.Shape:
    extents = row["actual_shape_extents_local_mm"]
    low = tuple(extents[axis][0] for axis in ("X", "T", "N"))
    size = tuple(
        extents[axis][1] - extents[axis][0] for axis in ("X", "T", "N")
    )
    transform = row["local_to_global_transform"]
    origin = tuple(transform[index][3] for index in range(3))
    local = cq.Solid.makeBox(*size, cq.Vector(*low))
    return local.rotate((0, 0, 0), (1, 0, 0), 50.0).translate(origin)


def _geometry_fixture():
    inventory = json.loads(
        (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text()
    )
    rows = {row["part_id"]: row for row in inventory["parts"]}
    source_ids = {
        g7_probe.LOWER_RAIL,
        g7_probe.UPPER_RAIL,
        g7_probe.PRINCIPAL,
    }
    finished_hosts = {part_id: _inventory_box(rows[part_id]) for part_id in source_ids}
    finished_candidates = {
        part_id: _basis_box(
            contract.CLEAT_DATUMS[part_id]["origin_basis_x_t_n_mm"],
            contract.CLEAT_DATUMS[part_id]["size_x_t_n_mm"],
        )
        for part_id in contract.CLEAT_DATUMS
    }
    candidate_bores = {}
    hardware = {}
    bore_diameter = WJ04_TRIAL.stacks[0].cad_envelope.bore_occupancy_diameter_mm
    for spec in g7_probe.STACK_SPECS:
        axis_id = contract._axis_id(spec.stack_id)
        direction = cq.Vector(
            *WJ04_TRIAL.frame.vector_to_global(spec.axis_direction_basis)
        ).normalized()
        axis_origin = cq.Vector(*WJ04_TRIAL.frame.to_global(spec.axis_point_basis_mm))
        start = axis_origin - direction * contract.G7_BORE_PROBE_MM
        grip = sum(thickness for _member, thickness in spec.layers)
        bore = cq.Solid.makeCylinder(
            bore_diameter / 2,
            grip + 2 * contract.G7_BORE_PROBE_MM,
            start,
            direction,
        )
        candidate_bores[axis_id] = SimpleNamespace(
            axis_id=axis_id,
            family=contract.FAMILY,
            trial_id=g7_probe.TRIAL_ID,
            receiver_ids=tuple(member for member, _ in spec.layers),
            shape=bore,
            station_id=None,
        )
        hardware[axis_id] = {
            role: cq.Solid.makeCylinder(
                0.5, 1.0, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1)
            )
            for role in ("shaft", "head", "head_washer", "nut_washer", "nut")
        }
    geometry = SimpleNamespace(
        trial_id="synthetic-composed-wj12-or-wj16",
        status="unaccepted_integrated_hypothesis",
        source_inventory_sha256=WJ04_TRIAL.source_inventory_sha256,
        source_inventory=inventory,
        family_trial_ids={"wj04_g7": g7_probe.TRIAL_ID},
        family_source_fingerprints={
            "right_rail": right_integration._source_inputs_sha256()
        },
        finished_hosts=finished_hosts,
        finished_candidate_parts=finished_candidates,
        candidate_bores=candidate_bores,
        candidate_installed_hardware=hardware,
    )
    return geometry


def test_manifest_binds_eight_physical_bolts_four_interfaces_and_open_gates() -> None:
    result = contract.build_mechanics_contract(_geometry_fixture())

    assert result["physical_inventory"] == {
        "ordinary_physical_bolts": 8,
        "modeled_component_shapes_for_these_bolts": 40,
        "physical_interfaces": 4,
        "scope_does_not_cover": (
            "other WJ12/WJ16 duties, the whole frame, the 66 Hillman axes, "
            "or native-model readiness"
        ),
    }
    assert {row["wood_grip_mm"] for row in result["physical_bolts"]} == {127.0}
    assert {row["hardware"]["bolt"]["sku"] for row in result["physical_bolts"]} == {
        "25C600HCS5Z"
    }
    assert all(
        row["hardware"]["bolt"]["raw_Lb_minus_nominal_wood_grip_mm_not_a_margin"] == 0.0
        and row["hardware"]["bolt"]["smooth_shank_through_far_wood_face_proven"] is False
        and "grip-gaging bound" in row["hardware"]["bolt"]["thread_transition_gate"]
        for row in result["physical_bolts"]
    )
    assert all(
        "wood-side head-seat centerline" in row["world_axis_origin_datum"]
        and row["modeled_bolt_under_head_origin_xyz_mm"] != row["world_axis_origin_xyz_mm"]
        and row["axis_authentication"]["composed_bore_extension_each_end_mm"] == 0.1
        for row in result["physical_bolts"]
    )
    assert all(
        row["signed_end_edge_and_bolt_load_classification"].startswith("unresolved")
        and row["four_d_seven_d_status"].startswith("not evaluated")
        for row in result["physical_bolts"]
    )
    assert {row["candidate_cleat_face"]["composed_finished_planar_area_mm2"] for row in result["physical_interfaces"]} == {
        round(88.9 * 119.7, 6),
        round(88.9 * 86.9, 6),
    }
    assert all(len(row["family_stack_ids"]) == 2 for row in result["physical_interfaces"])
    assert not any(result["claims"].values())


def test_manifest_rejects_wrong_receiver_order_and_axis_position() -> None:
    geometry = _geometry_fixture()
    spec = g7_probe.STACK_SPECS[0]
    axis_id = contract._axis_id(spec.stack_id)
    original = geometry.candidate_bores[axis_id]
    geometry.candidate_bores[axis_id] = SimpleNamespace(
        **{
            **vars(original),
            "receiver_ids": tuple(reversed(original.receiver_ids)),
        }
    )
    with pytest.raises(ValueError, match="identity/ordered receivers"):
        contract.build_mechanics_contract(geometry)

    geometry = _geometry_fixture()
    original = geometry.candidate_bores[axis_id]
    geometry.candidate_bores[axis_id] = SimpleNamespace(
        **{**vars(original), "station_id": "contradictory_station"}
    )
    with pytest.raises(ValueError, match="identity/ordered receivers"):
        contract.build_mechanics_contract(geometry)

    geometry = _geometry_fixture()
    original = geometry.candidate_bores[axis_id]
    geometry.candidate_bores[axis_id] = SimpleNamespace(
        **{
            **vars(original),
            "shape": original.shape.translate((1.0, 0.0, 0.0)),
        }
    )
    with pytest.raises(ValueError, match="disagrees with its pinned axis"):
        contract.build_mechanics_contract(geometry)


def test_manifest_rejects_stale_composed_family_hash() -> None:
    geometry = _geometry_fixture()
    geometry.family_source_fingerprints = {
        "right_rail": {
            **right_integration._source_inputs_sha256(),
            "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py": "0" * 64,
        }
    }
    with pytest.raises(ValueError, match="source changed after composition"):
        contract.build_mechanics_contract(geometry)


def test_manifest_rejects_unbound_inventory_edit_or_missing_physical_axis() -> None:
    geometry = _geometry_fixture()
    rows = [dict(row) for row in geometry.source_inventory["parts"]]
    principal = next(row for row in rows if row["part_id"] == g7_probe.PRINCIPAL)
    principal.pop("grain_axis_global_xyz")
    geometry.source_inventory = {**geometry.source_inventory, "parts": rows}
    with pytest.raises(ValueError, match="inventory content differs from the canonical file"):
        contract.build_mechanics_contract(geometry)

    geometry = _geometry_fixture()
    spec = g7_probe.STACK_SPECS[0]
    axis_id = contract._axis_id(spec.stack_id)
    del geometry.candidate_bores[axis_id]
    with pytest.raises(ValueError, match="exact eight-stack family"):
        contract.build_mechanics_contract(geometry)


def test_interface_rejects_translated_host_plane() -> None:
    geometry = _geometry_fixture()
    spec = next(
        row for row in g7_probe.STACK_SPECS if row.stack_id == "lower_rail_1"
    )
    source_row = next(
        row
        for row in geometry.source_inventory["parts"]
        if row["part_id"] == g7_probe.LOWER_RAIL
    )
    source_row = {**source_row}
    faces = [dict(face) for face in source_row["actual_planar_faces"]]
    contact_face = next(face for face in faces if face["face_id"] == "planar_face_04")
    normal = contact_face["normal_global_xyz"]
    contact_face["center_global_xyz_mm"] = [
        coordinate + component
        for coordinate, component in zip(
            contact_face["center_global_xyz_mm"], normal, strict=True
        )
    ]
    source_row["actual_planar_faces"] = faces
    origin = tuple(WJ04_TRIAL.frame.to_global(spec.axis_point_basis_mm))
    direction = tuple(
        WJ04_TRIAL.frame.vector_to_global(spec.axis_direction_basis)
    )
    direction = tuple(value / sum(component**2 for component in direction) ** 0.5 for value in direction)

    with pytest.raises(ValueError, match="source face plane misses"):
        contract._interface_record(
            spec=spec,
            stack_ids=["lower_rail_1", "lower_rail_2"],
            origin=origin,
            direction=direction,
            candidate_shape=geometry.finished_candidate_parts[g7_probe.LOWER_CLEAT],
            source_row=source_row,
        )
