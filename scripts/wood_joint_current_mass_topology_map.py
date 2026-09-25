"""Map current WJ24 mass rows to source geometry entities and graph references.

This is a read-only, source-bound adapter over the existing mass-centroid,
scene, and geometry-screen artifacts. It is an inventory-to-topology map, not
an FE mass-transfer adapter: no solver DOFs, constraints, or connector laws are
created. It does not build CAD or imply force sharing, stiffness, or capacity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

CURRENT_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_ROWS = 778
EXPECTED_MASS_KG = 224.4207766683882
GRAVITY_M_PER_S2 = 9.80665
EQUIPMENT_ALLOWANCE_KG = 25.0
CURRENT_SCREW_AXIS_ENVELOPE_LENGTH_MM = 63.5
HISTORICAL_SCREW_SOURCE_OCCUPIED_LENGTH_MM = 50.8
METAL_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})

INPUT_SHA256 = {
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json": "4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/export.py": "8da82299d3b2b2b426bdace5c129a412672cacaaafba14c821fff35bcd9a2441",
    "docs/wood-joints-mvp/board-weight-2026-09-24.json": "7425c8100c9bbf0586d8e1732138eb5ec1e6147f8418b5cf3ea95dc6108e035e",
    "site/owner-wood-joints-wj24-scene.json": "74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf",
    "site/owner-wood-joints-review-report.json": "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json": "851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/complete-contact-graph-attempt02.json": "7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_current_inputs(repo_root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Read the pinned artifacts and fail if any source is no longer frozen."""
    payloads: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    for relative, expected_hash in INPUT_SHA256.items():
        path = repo_root / relative
        actual_hash = _sha256(path)
        if actual_hash != expected_hash:
            raise ValueError(f"frozen input changed: {relative}")
        hashes[relative] = actual_hash
        if path.suffix == ".json":
            payloads[relative] = json.loads(path.read_text())

    centroids_path = next(
        path
        for path in INPUT_SHA256
        if path.endswith("current-mass-centroids-attempt01/mass-centroids.json")
    )
    weight_path = "docs/wood-joints-mvp/board-weight-2026-09-24.json"
    scene_path = "site/owner-wood-joints-wj24-scene.json"
    report_path = "site/owner-wood-joints-review-report.json"
    receiver_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json"
    graph_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/complete-contact-graph-attempt02.json"

    centroids = payloads[centroids_path]
    expected_centroid_sources = {
        weight_path: hashes[weight_path],
        scene_path: hashes[scene_path],
        report_path: hashes[report_path],
    }
    if centroids.get("source_sha256") != expected_centroid_sources:
        raise ValueError("centroid export source lineage differs from pinned inputs")

    return (
        {
            "centroids": centroids,
            "weight": payloads[weight_path],
            "scene": payloads[scene_path],
            "receiver": payloads[receiver_path],
            "graph": payloads[graph_path],
        },
        hashes,
    )


def _vector3(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} must be a 3-vector")
    result = [float(component) for component in value]
    if not all(math.isfinite(component) for component in result):
        raise ValueError(f"{label} contains a non-finite component")
    return result


def _assert_close(
    actual: float, expected: float, label: str, *, atol: float = 1e-8
) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=atol):
        raise ValueError(f"{label} differs: {actual!r} != {expected!r}")


def _tnut_panel(name: str) -> str:
    main_match = re.fullmatch(r"hold_tnut_main_([A-K])(1[0-2]|[1-9])", name)
    if main_match:
        column, row_text = main_match.groups()
        row = int(row_text)
        level = "lower" if row <= 6 else "upper"
        side = "left" if column <= "F" else "right"
        return f"main_{level}_{side}"

    kicker_match = re.fullmatch(r"hold_tnut_kicker_(10|[1-9])", name)
    if kicker_match:
        index = int(kicker_match.group(1))
        return "kicker_left" if index <= 5 else "kicker_right"
    raise ValueError(f"unrecognized current T-nut identity: {name}")


def _aabb_contains(
    bounds: list[float], point: list[float], *, tolerance: float = 1e-6
) -> bool:
    if len(bounds) != 6:
        raise ValueError("graph body bounds must have six components")
    return all(
        bounds[2 * axis] - tolerance <= point[axis] <= bounds[2 * axis + 1] + tolerance
        for axis in range(3)
    )


def _source_mass_entity(
    *,
    kind: str,
    entity_id: str,
    graph_member_references: list[str],
    reference_basis: str,
    source_geometry_kind: str,
    integration_class: str,
    optional_mass_carrier_key: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "id": entity_id,
        "source_geometry_kind": source_geometry_kind,
        "current_graph_member_references": graph_member_references,
        "reference_basis": reference_basis,
        "global_model_integration_class": integration_class,
        "optional_mass_carrier_key": optional_mass_carrier_key,
        "solver_dof_id": None,
        "solver_dof_mapping_status": "not_implemented_geometry_to_topology_map_only",
    }


def _row_source_entity(
    row: dict[str, Any],
    *,
    graph_members: dict[str, dict[str, Any]],
    candidate_axes: dict[str, dict[str, Any]],
    graph_candidate_axes: dict[str, dict[str, Any]],
    frame_axes: dict[str, dict[str, Any]],
    graph_frame_axes: dict[str, dict[str, Any]],
    screw_axes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    name = row["name"]
    group = row["group"]

    if group in {"plywood panels", "frame timber", "corner blocks"}:
        if name not in graph_members:
            raise ValueError(
                f"mass row lacks a current physical-member graph node: {name}"
            )
        member_kind = graph_members[name]["member_kind"]
        expected_kind = "panel" if group == "plywood panels" else "timber"
        if member_kind != expected_kind:
            raise ValueError(f"physical-member kind mismatch for {name}: {member_kind}")
        return _source_mass_entity(
            kind="current_physical_member_solid",
            entity_id=f"physical_member/{name}",
            graph_member_references=[name],
            reference_basis="same-named member node in the current contact graph",
            source_geometry_kind="current physical panel/timber/block solid",
            integration_class="direct_body_density_if_meshed_or_distributed_member_element_load_if_beam_reduced",
        )

    if group == "block bolts nuts washers":
        try:
            axis_id, role = name.rsplit("/", 1)
        except ValueError as exc:
            raise ValueError(f"malformed candidate hardware identity: {name}") from exc
        if (
            role not in METAL_ROLES
            or axis_id not in candidate_axes
            or axis_id not in graph_candidate_axes
        ):
            raise ValueError(f"unmapped candidate hardware role: {name}")
        scene_receivers = candidate_axes[axis_id]["receiver_ids"]
        graph_receivers = graph_candidate_axes[axis_id][
            "receiver_member_ids_as_recorded"
        ]
        if set(scene_receivers) != set(graph_receivers) or len(scene_receivers) < 2:
            raise ValueError(f"candidate receiver membership mismatch at {axis_id}")
        if role not in candidate_axes[axis_id]["installed_component_roles"]:
            raise ValueError(f"role not present in the current candidate stack: {name}")
        entity = _source_mass_entity(
            kind="current_candidate_hardware_component",
            entity_id=f"candidate_installed_hardware/{name}",
            graph_member_references=list(scene_receivers),
            reference_basis="scene receiver IDs equal current contact-graph receiver IDs for this axis; no head-to-nut order inferred",
            source_geometry_kind="current bolt/washer/nut component solid",
            integration_class="direct_component_body_density_if_meshed_else_adequate_condensation_or_optional_mass_carrier",
            optional_mass_carrier_key=f"mass_carrier/candidate_bolt_role/{name}",
        )
        entity["axis_id"] = axis_id
        entity["component_role"] = role
        return entity

    if group == "frame bolts nuts washers":
        try:
            axis_id, role = name.rsplit("/", 1)
        except ValueError as exc:
            raise ValueError(
                f"malformed retained frame hardware identity: {name}"
            ) from exc
        if (
            role not in METAL_ROLES
            or axis_id not in frame_axes
            or axis_id not in graph_frame_axes
        ):
            raise ValueError(f"unmapped retained frame hardware role: {name}")
        scene_members = frame_axes[axis_id]["members"]
        graph_members_for_axis = graph_frame_axes[axis_id][
            "source_member_ids_as_recorded"
        ]
        if set(scene_members) != set(graph_members_for_axis) or len(scene_members) != 2:
            raise ValueError(
                f"retained-frame receiver membership mismatch at {axis_id}"
            )
        entity = _source_mass_entity(
            kind="current_retained_frame_hardware_component",
            entity_id=f"retained_frame_hardware/{name}",
            graph_member_references=list(scene_members),
            reference_basis="retained-bolt source member pair matched to current contact graph; no head-to-nut order inferred",
            source_geometry_kind="current frame-bolt/nut/washer component solid",
            integration_class="direct_component_body_density_if_meshed_else_adequate_condensation_or_optional_mass_carrier",
            optional_mass_carrier_key=f"mass_carrier/retained_frame_bolt_role/{name}",
        )
        entity["axis_id"] = axis_id
        entity["component_role"] = role
        return entity

    if group == "panel kicker screws":
        if name not in screw_axes:
            raise ValueError(
                f"screw mass row lacks a current panel/receiver axis: {name}"
            )
        axis = screw_axes[name]
        current_length = float(axis["materialized_axis_envelope"]["axial_length_mm"])
        source_occupied_length = float(axis["source_occupied_length_mm"])
        _assert_close(
            current_length,
            CURRENT_SCREW_AXIS_ENVELOPE_LENGTH_MM,
            f"current screw CAD axis-envelope length {name}",
            atol=1e-6,
        )
        _assert_close(
            source_occupied_length,
            HISTORICAL_SCREW_SOURCE_OCCUPIED_LENGTH_MM,
            f"historical screw source occupied length {name}",
            atol=1e-6,
        )
        entity = _source_mass_entity(
            kind="current_panel_screw_axis_envelope_proxy",
            entity_id=f"panel_screw_axis_envelope/{name}",
            graph_member_references=[axis["panel_member"], axis["receiver_member"]],
            reference_basis="current receiver-screen panel/receiver map for the same screw axis",
            source_geometry_kind="63.5 mm current CAD axis-envelope mass proxy; historical source_occupied_length_mm is 50.8 mm; not a detailed screw solid",
            integration_class="detailed_screw_body_or_adequate_condensation_or_optional_axis_mass_carrier",
            optional_mass_carrier_key=f"mass_carrier/panel_screw_axis/{name}",
        )
        entity["axis_id"] = name
        entity["location_status"] = axis["current_location_status"]
        entity["current_cad_axis_envelope_length_mm"] = current_length
        entity["historical_inventory_source_occupied_length_mm"] = (
            source_occupied_length
        )
        return entity

    if group == "hold T-nuts":
        panel_id = _tnut_panel(name)
        if (
            panel_id not in graph_members
            or graph_members[panel_id]["member_kind"] != "panel"
        ):
            raise ValueError(
                f"T-nut panel owner is absent from current graph: {name} -> {panel_id}"
            )
        center = _vector3(row["mass_center_global_xyz_mm"], f"{name} centroid")
        bounds = graph_members[panel_id]["finished"]["bounds_xyz_mm"]
        if not _aabb_contains(bounds, center):
            raise ValueError(
                f"T-nut centroid fails its source-label panel bounds check: {name}"
            )
        return _source_mass_entity(
            kind="current_physical_tnut_component",
            entity_id=f"protected_tnuts/{name}",
            graph_member_references=[panel_id],
            reference_basis="current grid label maps to this panel and exported centroid falls within its finished-body bounds; this is not an FE attachment or contact definition",
            source_geometry_kind="current physical steel T-nut solid",
            integration_class="direct_component_body_density_if_meshed_else_adequate_condensation_or_optional_tnut_mass_carrier",
            optional_mass_carrier_key=f"mass_carrier/hold_tnut/{name}",
        )

    raise ValueError(f"unhandled physical mass group: {group}")


def build_current_mass_source_topology_map(
    *,
    centroids: dict[str, Any],
    weight: dict[str, Any],
    scene: dict[str, Any],
    receiver: dict[str, Any],
    graph: dict[str, Any],
    source_sha256: dict[str, str],
) -> dict[str, Any]:
    """Join each frozen mass row to its source entity and topology references.

    The returned IDs describe inventory/source geometry. They are not solver
    DOF IDs or implemented mass-transfer owners.
    """
    for label, source in (
        ("centroid export", centroids),
        ("weight inventory", weight),
        ("scene", scene),
        ("receiver screen", receiver),
        ("contact graph", graph),
    ):
        if source.get("revision_id") != CURRENT_REVISION_ID:
            raise ValueError(f"{label} revision mismatch")

    if centroids.get("status") != "MODELED_SOLID_MASS_CENTERS_NOT_A_FRAME_RESPONSE":
        raise ValueError(
            "centroid export status is not the reviewed mass-only artifact"
        )
    if (
        centroids.get("equipment_allowance_kg_excluded_from_centroid")
        != EQUIPMENT_ALLOWANCE_KG
    ):
        raise ValueError("centroid export equipment allowance changed")

    inventory_rows = weight.get("rows")
    mass_rows = centroids.get("rows")
    if not isinstance(inventory_rows, list) or not isinstance(mass_rows, list):
        raise TypeError("frozen input lacks inventory rows")
    if len(inventory_rows) != EXPECTED_ROWS or len(mass_rows) != EXPECTED_ROWS:
        raise ValueError("expected exactly 778 inventory and centroid rows")
    inventory_by_name = {row["name"]: row for row in inventory_rows}
    if len(inventory_by_name) != len(inventory_rows):
        raise ValueError("weight inventory has duplicate identities")
    mass_by_name = {row["name"]: row for row in mass_rows}
    if len(mass_by_name) != len(mass_rows) or set(mass_by_name) != set(
        inventory_by_name
    ):
        raise ValueError(
            "mass-centroid rows do not exactly cover unique inventory identities"
        )

    model_inventory = scene["model_inventory"]
    graph_inventories = graph["inventories"]
    graph_members = {
        row["member_id"]: row for row in graph_inventories["physical_members"]
    }
    if len(graph_members) != 50 or graph["counts"]["physical_member_nodes"] != 50:
        raise ValueError(
            "current contact graph does not contain the expected 50 physical members"
        )
    if set(graph_members) != {
        row["name"]
        for row in inventory_rows
        if row["group"] in {"plywood panels", "frame timber", "corner blocks"}
    }:
        raise ValueError(
            "physical member graph and weighted wood/panel/block identities differ"
        )

    candidate_axes = model_inventory["candidate_axes"]
    graph_candidate_axes = {
        row["axis_id"]: row for row in graph_inventories["candidate_bolt_axes"]
    }
    frame_axes = {row["axis_id"]: row for row in model_inventory["frame_bolts"]}
    graph_frame_axes = {
        row["axis_id"]: row for row in graph_inventories["retained_frame_bolts"]
    }
    if len(candidate_axes) != 92 or len(graph_candidate_axes) != 92:
        raise ValueError(
            "expected 92 current candidate bolt axes in scene and contact graph"
        )
    if len(frame_axes) != 12 or len(graph_frame_axes) != 12:
        raise ValueError(
            "expected 12 retained frame bolt axes in scene and contact graph"
        )

    screw_axes = {row["axis_id"]: row for row in receiver["axes"]}
    if len(screw_axes) != 66 or set(screw_axes) != {
        row["name"] for row in inventory_rows if row["group"] == "panel kicker screws"
    }:
        raise ValueError("current screw axes do not exactly match the 66 mass rows")
    moved_axis_rows = {
        row["axis_id"]: row for row in model_inventory["moved_panel_axes"]
    }
    moved_axes = set(moved_axis_rows)
    moved_by_receiver_map = {
        axis_id
        for axis_id, axis in screw_axes.items()
        if axis["current_location_status"] != "source_station_retained"
    }
    if len(moved_axes) != 8 or moved_axes != moved_by_receiver_map:
        raise ValueError("expected exactly eight current moved panel screw axes")

    source_entity_ids: set[str] = set()
    mapped_rows = []
    source_map_counts: Counter[tuple[str, str]] = Counter()
    for row in mass_rows:
        frozen = inventory_by_name[row["name"]]
        if row["group"] != frozen["group"]:
            raise ValueError(f"mass group changed for {row['name']}")
        _assert_close(
            float(row["mass_kg"]),
            float(frozen["mass_kg"]),
            f"mass {row['name']}",
            atol=1e-12,
        )
        _assert_close(
            float(row["volume_mm3"]),
            float(frozen["volume_mm3"]),
            f"volume {row['name']}",
            atol=1e-6,
        )

        center = _vector3(row["mass_center_global_xyz_mm"], f"{row['name']} centroid")
        force = _vector3(
            row["gravity_force_global_xyz_n"], f"{row['name']} gravity force"
        )
        moment = _vector3(
            row["gravity_moment_about_global_origin_nmm"],
            f"{row['name']} gravity moment",
        )
        expected_force = -float(row["mass_kg"]) * GRAVITY_M_PER_S2
        expected_moment = [center[1] * expected_force, -center[0] * expected_force, 0.0]
        _assert_close(force[0], 0.0, f"force-x {row['name']}")
        _assert_close(force[1], 0.0, f"force-y {row['name']}")
        _assert_close(force[2], expected_force, f"force-z {row['name']}")
        for axis in range(3):
            _assert_close(
                moment[axis],
                expected_moment[axis],
                f"moment-{axis} {row['name']}",
                atol=1e-5,
            )

        if row["group"] == "panel kicker screws":
            screw_axis = screw_axes[row["name"]]
            current_length = float(
                screw_axis["materialized_axis_envelope"]["axial_length_mm"]
            )
            _assert_close(
                current_length,
                CURRENT_SCREW_AXIS_ENVELOPE_LENGTH_MM,
                f"current screw CAD axis-envelope length {row['name']}",
                atol=1e-6,
            )
            midpoint_start = _vector3(
                screw_axis["origin_global_xyz_mm"],
                f"{row['name']} current CAD axis start",
            )
            direction = _vector3(
                screw_axis["axis_global_xyz"], f"{row['name']} current CAD axis"
            )
            if row["name"] in moved_axis_rows:
                moved = moved_axis_rows[row["name"]]
                recorded_start = _vector3(
                    moved["new_start_global_xyz_mm"],
                    f"{row['name']} moved axis start",
                )
                recorded_direction = _vector3(
                    moved["axis_global_xyz_unchanged"],
                    f"{row['name']} moved axis direction",
                )
                for component in range(3):
                    _assert_close(
                        midpoint_start[component],
                        recorded_start[component],
                        f"{row['name']} current/moved start component {component}",
                        atol=1e-6,
                    )
                    _assert_close(
                        direction[component],
                        recorded_direction[component],
                        f"{row['name']} current/moved direction component {component}",
                        atol=1e-9,
                    )
            expected_center = [
                midpoint_start[component] + 0.5 * current_length * direction[component]
                for component in range(3)
            ]
            for component in range(3):
                _assert_close(
                    center[component],
                    expected_center[component],
                    f"{row['name']} current axis-envelope midpoint component {component}",
                    atol=1e-6,
                )

        source_entity = _row_source_entity(
            row,
            graph_members=graph_members,
            candidate_axes=candidate_axes,
            graph_candidate_axes=graph_candidate_axes,
            frame_axes=frame_axes,
            graph_frame_axes=graph_frame_axes,
            screw_axes=screw_axes,
        )
        if source_entity["id"] in source_entity_ids:
            raise ValueError(
                f"two mass rows map to the same source entity: {source_entity['id']}"
            )
        if any(
            member_id not in graph_members
            for member_id in source_entity["current_graph_member_references"]
        ):
            raise ValueError(
                f"mass source entity references an unknown current graph member: {row['name']}"
            )
        source_entity_ids.add(source_entity["id"])
        source_map_counts[(row["group"], row["source_shape_map"])] += 1
        mapped_rows.append(
            {
                "inventory_name": row["name"],
                "group": row["group"],
                "mass_kg": row["mass_kg"],
                "mass_center_global_xyz_mm": center,
                "gravity_force_global_xyz_n": force,
                "gravity_moment_about_global_origin_nmm": moment,
                "source_shape_map": row["source_shape_map"],
                "source_mass_entity": source_entity,
            }
        )

    expected_source_map_counts = {
        ("plywood panels", "panel_replacements"): 5,
        ("plywood panels", "preserved_source_parts"): 1,
        ("frame timber", "finished_hosts"): 16,
        ("frame timber", "preserved_source_parts"): 4,
        ("corner blocks", "finished_candidate_parts"): 24,
        ("block bolts nuts washers", "candidate_installed_hardware"): 460,
        ("frame bolts nuts washers", "protected_retained_frame_components"): 60,
        ("panel kicker screws", "current_screw_axis_envelope"): 66,
        ("hold T-nuts", "protected_tnuts"): 142,
    }
    if dict(source_map_counts) != expected_source_map_counts:
        raise ValueError(
            f"current source-shape counts changed: {dict(source_map_counts)}"
        )

    total_mass = math.fsum(row["mass_kg"] for row in mapped_rows)
    _assert_close(total_mass, EXPECTED_MASS_KG, "total modeled mass", atol=1e-9)
    aggregate_center = [
        math.fsum(
            row["mass_kg"] * row["mass_center_global_xyz_mm"][axis]
            for row in mapped_rows
        )
        / total_mass
        for axis in range(3)
    ]
    aggregate_force = [
        math.fsum(row["gravity_force_global_xyz_n"][axis] for row in mapped_rows)
        for axis in range(3)
    ]
    aggregate_moment = [
        math.fsum(
            row["gravity_moment_about_global_origin_nmm"][axis] for row in mapped_rows
        )
        for axis in range(3)
    ]
    for axis, expected in enumerate(centroids["modeled_mass_center_global_xyz_mm"]):
        _assert_close(
            aggregate_center[axis],
            float(expected),
            f"aggregate center axis {axis}",
            atol=1e-7,
        )
    for axis, expected in enumerate(centroids["gravity_force_global_xyz_n"]):
        _assert_close(
            aggregate_force[axis],
            float(expected),
            f"aggregate force axis {axis}",
            atol=1e-7,
        )
    for axis, expected in enumerate(
        centroids["gravity_moment_about_global_origin_nmm"]
    ):
        _assert_close(
            aggregate_moment[axis],
            float(expected),
            f"aggregate moment axis {axis}",
            atol=1e-3,
        )

    source_entity_counts = Counter(
        row["source_mass_entity"]["kind"] for row in mapped_rows
    )
    expected_source_entity_counts = {
        "current_physical_member_solid": 50,
        "current_candidate_hardware_component": 460,
        "current_retained_frame_hardware_component": 60,
        "current_panel_screw_axis_envelope_proxy": 66,
        "current_physical_tnut_component": 142,
    }
    if (
        dict(source_entity_counts) != expected_source_entity_counts
        or len(source_entity_ids) != EXPECTED_ROWS
    ):
        raise ValueError(
            f"source entity counts/uniqueness mismatch: {dict(source_entity_counts)}"
        )

    return {
        "schema": "current_wood_joint_mass_source_topology_map/v1",
        "status": "GEOMETRY_TOPOLOGY_MAP_ONLY_NO_REDUCED_DOF_OR_TRANSFER_MAP",
        "revision_id": CURRENT_REVISION_ID,
        "source_sha256": source_sha256,
        "mass_inventory_row_count": len(mapped_rows),
        "unique_source_mass_entity_count": len(source_entity_ids),
        "source_mass_entity_counts": dict(sorted(source_entity_counts.items())),
        "modeled_mass_kg": total_mass,
        "modeled_mass_center_global_xyz_mm": aggregate_center,
        "gravity_force_global_xyz_n": aggregate_force,
        "gravity_moment_about_global_origin_nmm": aggregate_moment,
        "equipment_allowance": {
            "mass_kg": EQUIPMENT_ALLOWANCE_KG,
            "included_in_mass_rows": False,
            "additional_allowance_rows": 0,
            "placement_scenarios": "Use the separate current-frame-dead-load-map scenarios; this artifact assigns no actual accessory centroid.",
        },
        "source_to_topology_semantics": {
            "source_entity_identity": "Each row maps to one unique source mass entity ID and keeps its exported center, force, and first moment. This is inventory/source-geometry accounting only.",
            "graph_references": "Member references are associations to named nodes in the current geometry graph. They do not identify FE nodes/elements, apportion mass, define contact, establish constraints, or implement load transfer.",
            "exclusive_future_mass_input": "A future model must account for every source row once using one exclusive representation: body density/integrated mass, member-distributed mass/load, a source-row mass carrier, or a documented aggregate/condensed representation. Do not double-count rows. Aggregation/condensation is acceptable when it preserves exact gravity force and first moments plus the inertia and attachment behavior relevant to the intended analysis.",
            "reduced_member_limit": "A single per-member centroid force preserves that body's external gravity resultant and first moment but not its internal distributed self-weight bending. A reduced beam needs distributed member mass/load or a validated equivalent.",
            "missing_solver_map": "All solver_dof_id values are null. No mass carrier nodes, connector constraints, contact laws, DOF attachment map, stiffness, bolt force split, member capacity, or support reaction is implemented.",
        },
        "global_model_integration": {
            "solver_dof_mapping_implemented": False,
            "reduced_model_mass_transfer_implemented": False,
            "solver_dof_mapping_count": 0,
            "implemented_mass_carrier_count": 0,
            "source_physical_solid_rows": 712,
            "physical_member_rows_with_direct_density_or_distributed_beam_load_path": 50,
            "component_solid_rows_needing_a_mass_representation_if_omitted_from_mesh": 662,
            "screw_axis_proxy_rows_needing_a_mass_representation_unless_detailed_source_added": 66,
            "illustrative_carrier_count_if_one_carrier_is_chosen_per_nonmember_source_row": 728,
            "illustrative_carrier_count_status": "optional accounting route, not an adopted requirement; documented aggregation/condensation may use fewer DOFs if it preserves exact gravity force and first moments plus relevant inertia and attachment behavior",
            "current_screw_axis_envelope_geometry": {
                "axis_count": 66,
                "current_cad_axis_envelope_length_mm": CURRENT_SCREW_AXIS_ENVELOPE_LENGTH_MM,
                "historical_inventory_source_occupied_length_mm": HISTORICAL_SCREW_SOURCE_OCCUPIED_LENGTH_MM,
                "representation": "current fixed-axis CAD envelopes; not detailed purchased screw solids or measured engagement",
            },
            "integration_routes": [
                {
                    "source_rows": "six panels, 20 frame members, 24 solid blocks",
                    "count": 50,
                    "solid_model_route": "apply density to the same meshed physical body represented by the source row",
                    "reduced_model_route": "map member mass to its own beam elements as distributed mass/gravity load when member bending demand is in scope; per-member CG resultant alone does not reproduce internal self-weight bending",
                    "current_status": "no mesh-body or beam-element IDs mapped; same-named graph member references are topology only",
                },
                {
                    "source_rows": "460 candidate bolt/washer/nut roles plus 60 retained frame-bolt roles",
                    "count": 520,
                    "solid_model_route": "apply density to each corresponding meshed hardware component if retained as a body",
                    "reduced_model_route": "possible route: one explicit mass carrier per omitted component role; documented aggregate/condensed mass representation is also valid if it preserves exact source gravity force and first moments plus inertia and attachment behavior relevant to the intended analysis",
                    "current_status": "role and two/three receiver-member references mapped; no component body mesh, mass DOF, or attachment constraint mapped; do not assign to nearest timber",
                },
                {
                    "source_rows": "142 physical hold T-nuts",
                    "count": 142,
                    "solid_model_route": "apply density to each corresponding meshed T-nut component if retained as a body",
                    "reduced_model_route": "possible route: one carrier per omitted T-nut; documented aggregate/condensed representation is also valid if it preserves exact source gravity force and first moments plus inertia and attachment behavior relevant to the intended analysis",
                    "current_status": "mass IDs, centroids, and label-based panel references mapped; no mass DOFs or attachment constraints mapped. A local T-nut/slot law is outside this inventory and is needed only if that local interaction is in scope",
                },
                {
                    "source_rows": "66 panel/kicker screw axis-envelope proxies",
                    "count": 66,
                    "solid_model_route": "not applicable to current proxy rows; replace only with a new detailed screw mass source before treating screws as bodies",
                    "reduced_model_route": "possible route: one axis mass carrier per proxy row; documented aggregate/condensed representation is also valid if it preserves exact source gravity force and first moments plus inertia and attachment behavior relevant to the intended analysis",
                    "current_status": "current axis and panel/receiver geometry refs mapped; no mass DOFs or screw joint relation mapped",
                },
            ],
        },
        "physical_mass_rows": mapped_rows,
        "limits": [
            "The 66 screw rows use current CAD fixed-axis envelopes with 63.5 mm axial length, not detailed screw solids. The inventory's 50.8 mm source_occupied_length_mm is historical; current centroids use the 63.5 mm envelopes. The eight moved axes were checked as new_start + 31.75 mm × unchanged direction.",
            "The 25 kg holds/hold-bolts/electrical allowance is outside the 778-row export and remains scenario-based.",
            "The current graph does not encode physical fastener head-to-nut order or force share across receivers.",
            "Four zero-density nut carriers from the local engagement diagnostic are not extra physical mass rows; if retained, keep them massless and represent each inventoried physical nut exactly once.",
            "Gravity resultants are about the global origin, not a support reaction or solved frame response.",
        ],
        "mechanical_acceptance": False,
        "native_solve_run": False,
        "cad_rebuilt_or_modified": False,
    }


def write_new_json(destination: Path, payload: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="repository root containing the pinned source artifacts",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path(
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-topology-map-attempt03/source-topology-map.json"
        ),
        help="write a new JSON file; existing destinations are never overwritten",
    )
    args = parser.parse_args()
    inputs, hashes = load_current_inputs(args.repo_root.resolve())
    payload = build_current_mass_source_topology_map(**inputs, source_sha256=hashes)
    destination = (
        args.destination
        if args.destination.is_absolute()
        else args.repo_root / args.destination
    )
    write_new_json(destination, payload)
    print(
        json.dumps(
            {
                "destination": str(destination),
                "mass_inventory_row_count": payload["mass_inventory_row_count"],
                "unique_source_mass_entity_count": payload[
                    "unique_source_mass_entity_count"
                ],
                "modeled_mass_kg": payload["modeled_mass_kg"],
                "gravity_force_global_xyz_n": payload["gravity_force_global_xyz_n"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
