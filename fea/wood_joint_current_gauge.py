"""Source-bound 3-2-1 remote gauge for the frozen current wood-joint mesh.

This emits only six zero SPCs and an audit record.  It does not claim that the
contact model is mechanically complete or that the gauge is a physical support.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"

CONTRACT = ROOT / "docs/wood-joints-mvp/representative-unit-response-contract.md"
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
INPUT_INVENTORY = EVAL / "ordinary-patch-inputs-attempt01/inventory.json"
MESH_REPORT = EVAL / "ordinary-patch-mesh-attempt02/mesh/mesh.json"
MESH_DECK = EVAL / "ordinary-patch-mesh-attempt02/mesh/mesh.inp"
CLASSIFICATION = EVAL / "ordinary-patch-contact-classification-attempt01/classification.json"
CONTACT_MANIFEST = EVAL / "ordinary-patch-contact-deck-attempt01/contact-manifest.json"
CONTACT_FRAGMENT = EVAL / "ordinary-patch-contact-deck-attempt01/contact-fragment.inc"
LOAD_PATCH = EVAL / "ordinary-seating-actuator-attempt02/actuator.json"

FROZEN_SHA256 = {
    "contract": "edba2e6678edba206e920292770d6bd8f20fc7bb2bfc861cc8d4c0e340a7cb9a",
    "source_inventory": "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    "input_inventory": "70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3",
    "mesh_report": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "mesh_deck": "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803",
    "classification": "18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13",
    "contact_manifest": "50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d",
    "contact_fragment": "35a4513b7877b04b0c2be053f3084d07178a148c606780d12d54388636574b24",
    "load_patch": "66f16b3a6157780c563fa03ad976e0caccd6d604023fa007432dec1da2e1054d",
}

PRINCIPAL_MESH_ID = "W02_BASE_PRINCIPAL_CENTER_RIGHT"
PRINCIPAL_PART_ID = "base_principal_center_right"
REMOTE_T_MAX_MM = 2415.403793361191
COORD_TOLERANCE_MM = 1e-5
ROTATION_LENGTH_SCALE_MM = 1000.0

# The literal contract-corner nodes are recorded and rejected below because the
# frozen contact fragment places them on complete CAD master-face surfaces.
# These three remote far-T section nodes are the frozen replacement triad.
GAUGE_NODES = {
    "A": 33824,
    "B": 43470,
    "C": 33822,
}
SPC_ROWS = ((33824, 1), (33824, 2), (33824, 3), (43470, 2), (43470, 3), (33822, 2))
CONTRACT_CORNER_NODES = {"A": 32537, "B": 32554, "C": 32538}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_pinned(path: Path, label: str) -> tuple[bytes, dict[str, Any] | None]:
    data = path.read_bytes()
    digest = _sha(data)
    if digest != FROZEN_SHA256[label]:
        raise ValueError(f"{label} digest differs from the frozen current artifact")
    parsed = json.loads(data) if path.suffix == ".json" else None
    return data, parsed


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def _parse_mesh_nodes(data: bytes) -> dict[int, tuple[float, float, float]]:
    nodes: dict[int, tuple[float, float, float]] = {}
    in_nodes = False
    for raw in data.decode("utf-8").splitlines():
        line = raw.strip()
        if line.upper() == "*NODE":
            in_nodes = True
            continue
        if in_nodes and line.startswith("*"):
            break
        if not in_nodes or not line:
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 4:
            raise ValueError("malformed node record in frozen mesh deck")
        node_id = int(fields[0])
        point = tuple(float(value) for value in fields[1:])
        if node_id in nodes or not all(math.isfinite(value) for value in point):
            raise ValueError("duplicate or non-finite node in frozen mesh deck")
        nodes[node_id] = point  # type: ignore[assignment]
    if not nodes:
        raise ValueError("frozen mesh deck has no *NODE block")
    return nodes


def _contact_node_union(fragment: bytes) -> set[int]:
    contact_nodes: set[int] = set()
    active = False
    current_name: str | None = None
    for raw in fragment.decode("utf-8").splitlines():
        line = raw.strip()
        if line.startswith("*"):
            active = False
            current_name = None
            match = re.match(r"^\*NSET\s*,\s*NSET\s*=\s*([^,]+)", line, re.I)
            if match and match.group(1).strip().upper().startswith("WJCP_N_"):
                active = True
                current_name = match.group(1).strip()
            continue
        if active and line:
            try:
                contact_nodes.update(int(value.strip()) for value in line.split(",") if value.strip())
            except ValueError as error:
                raise ValueError(f"malformed contact node set {current_name}") from error
    if not contact_nodes:
        raise ValueError("frozen contact fragment has no WJCP contact node sets")
    return contact_nodes


def _rigid_constraint_matrix(
    points: dict[str, tuple[float, float, float]],
) -> list[list[float]]:
    """Rows map [tx,ty,tz,wx,wy,wz] to the six constrained SPC scalars."""
    origin = points["A"]
    matrix: list[list[float]] = []
    rows_by_node: dict[int, list[int]] = {
        GAUGE_NODES["A"]: [1, 2, 3],
        GAUGE_NODES["B"]: [2, 3],
        GAUGE_NODES["C"]: [2],
    }
    label_by_node = {node: label for label, node in GAUGE_NODES.items()}
    for node_id, dofs in rows_by_node.items():
        dx, dy, dz = (
            (points[label_by_node[node_id]][i] - origin[i]) / ROTATION_LENGTH_SCALE_MM
            for i in range(3)
        )
        # omega x r, with rotations scaled by 1000 mm for numerical rank.
        rotational = ((0.0, dz, -dy), (-dz, 0.0, dx), (dy, -dx, 0.0))
        for dof in dofs:
            row = [0.0] * 6
            row[dof - 1] = 1.0
            row[3:] = rotational[dof - 1]
            matrix.append(row)
    return matrix


def _matrix_rank(matrix: list[list[float]], tolerance: float = 1e-12) -> int:
    if not matrix:
        return 0
    a = [row[:] for row in matrix]
    row_count, column_count = len(a), len(a[0])
    rank = 0
    for column in range(column_count):
        pivot = max(range(rank, row_count), key=lambda row: abs(a[row][column]), default=rank)
        if rank >= row_count or abs(a[pivot][column]) <= tolerance:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        scale = a[rank][column]
        a[rank] = [value / scale for value in a[rank]]
        for row in range(row_count):
            if row == rank:
                continue
            factor = a[row][column]
            if factor:
                a[row] = [x - factor * y for x, y in zip(a[row], a[rank], strict=True)]
        rank += 1
        if rank == row_count:
            break
    return rank


def build_current_gauge() -> tuple[str, dict[str, Any]]:
    """Return the frozen current mesh's six-SPC gauge fragment and audit."""
    paths = {
        "contract": CONTRACT,
        "source_inventory": SOURCE_INVENTORY,
        "input_inventory": INPUT_INVENTORY,
        "mesh_report": MESH_REPORT,
        "mesh_deck": MESH_DECK,
        "classification": CLASSIFICATION,
        "contact_manifest": CONTACT_MANIFEST,
        "contact_fragment": CONTACT_FRAGMENT,
        "load_patch": LOAD_PATCH,
    }
    raw: dict[str, bytes] = {}
    parsed: dict[str, dict[str, Any]] = {}
    for label, path in paths.items():
        payload, record = _read_pinned(path, label)
        raw[label] = payload
        if record is not None:
            parsed[label] = record

    contract = raw["contract"].decode("utf-8")
    if "(X_min, T_max, N_min)" not in contract or f"{REMOTE_T_MAX_MM} mm" not in contract:
        raise ValueError("representative response contract no longer binds the named triad")

    inventory = parsed["input_inventory"]
    source_inventory = parsed["source_inventory"]
    if inventory.get("geometry_binding", {}).get("source_inventory_sha256") != FROZEN_SHA256["source_inventory"]:
        raise ValueError("current input inventory does not bind the frozen source inventory")
    source_rows = source_inventory.get("parts", [])
    source_part = next((row for row in source_rows if row.get("part_id") == PRINCIPAL_PART_ID), None)
    if not isinstance(source_part, dict):
        raise ValueError("source inventory lacks the principal member frame")
    transform = source_part.get("local_to_global_transform")
    axes = source_part.get("local_axes")
    extents = source_part.get("actual_shape_extents_local_mm")
    if not isinstance(transform, list) or not isinstance(axes, dict) or not isinstance(extents, dict):
        raise ValueError("principal source local frame or extents are missing")
    origin = tuple(float(transform[i][3]) for i in range(3))
    local_axes = {name: tuple(float(value) for value in axes[name]) for name in ("X", "T", "N")}
    contract_axes = {
        "X": (1.0, 0.0, 0.0),
        "T": (0.0, 0.6427876096865394, 0.766044443118978),
        "N": (0.0, -0.766044443118978, 0.6427876096865394),
    }
    if any(math.dist(local_axes[key], contract_axes[key]) > 1e-12 for key in contract_axes):
        raise ValueError("principal local axes differ from the contract WJ04 X/T/N frame")
    if abs(float(extents["T"][1]) - REMOTE_T_MAX_MM) > COORD_TOLERANCE_MM:
        raise ValueError("source principal T_max differs from the contract's remote location")

    mesh_report = parsed["mesh_report"]
    if (mesh_report.get("body_count"), mesh_report.get("node_count"), mesh_report.get("element_count")) != (19, 116162, 57643):
        raise ValueError("current mesh counts differ from the frozen 19-body mesh")
    body_rows = mesh_report.get("bodies", {})
    principal = body_rows.get(PRINCIPAL_MESH_ID)
    if not isinstance(principal, dict) or (
        principal.get("owner_kind") != "wood_member"
        or principal.get("source_body_id") != PRINCIPAL_PART_ID
    ):
        raise ValueError("frozen mesh principal owner does not bind the named timber")
    mesh_nodes = _parse_mesh_nodes(raw["mesh_deck"])
    owner_nodes = {int(node) for node in principal.get("nodes", [])}
    if not owner_nodes or not owner_nodes <= set(mesh_nodes):
        raise ValueError("principal node ownership is absent from the frozen deck")
    owners: dict[int, list[str]] = {}
    for mesh_body_id, row in body_rows.items():
        for node in row.get("nodes", []):
            owners.setdefault(int(node), []).append(str(mesh_body_id))
    if any(owners.get(node) != [PRINCIPAL_MESH_ID] for node in GAUGE_NODES.values()):
        raise ValueError("a selected gauge node is not uniquely owned by the principal body")

    def local_coordinates(point: tuple[float, float, float]) -> tuple[float, float, float]:
        relative = tuple(point[i] - origin[i] for i in range(3))
        return tuple(_dot(relative, local_axes[name]) for name in ("X", "T", "N"))

    local_by_node = {node: local_coordinates(mesh_nodes[node]) for node in owner_nodes}
    measured_extents = {
        axis: [min(point[i] for point in local_by_node.values()), max(point[i] for point in local_by_node.values())]
        for i, axis in enumerate(("X", "T", "N"))
    }
    for axis in ("X", "T", "N"):
        if max(abs(measured_extents[axis][i] - float(extents[axis][i])) for i in (0, 1)) > COORD_TOLERANCE_MM:
            raise ValueError(f"current principal mesh does not reproduce source {axis} extents")

    # Confirm the literal contract corners resolve, then prove why a revised
    # triad is required for this frozen complete-face contact representation.
    mins = {axis: float(extents[axis][0]) for axis in ("X", "T", "N")}
    maxs = {axis: float(extents[axis][1]) for axis in ("X", "T", "N")}
    literal_targets = {
        "A": (mins["X"], maxs["T"], mins["N"]),
        "B": (maxs["X"], maxs["T"], mins["N"]),
        "C": (mins["X"], maxs["T"], maxs["N"]),
    }
    for label, node_id in CONTRACT_CORNER_NODES.items():
        if node_id not in owner_nodes or math.dist(local_by_node[node_id], literal_targets[label]) > COORD_TOLERANCE_MM:
            raise ValueError("literal contract corner no longer resolves to the frozen mesh")

    contact_manifest = parsed["contact_manifest"]
    if contact_manifest.get("contact_fragment_sha256") != FROZEN_SHA256["contact_fragment"]:
        raise ValueError("contact manifest does not bind the frozen contact fragment")
    contact_nodes = _contact_node_union(raw["contact_fragment"])
    actuator = parsed["load_patch"]
    load_rows = actuator.get("owner_unit_wrench_distributions", [])
    load_nodes = {
        int(row["node_id"])
        for owner_rows in load_rows
        for row in owner_rows.get("nodal_forces", [])
    }
    if not load_nodes:
        raise ValueError("frozen load patch has no nodal forces")

    gauge_ids = set(GAUGE_NODES.values())
    if gauge_ids & contact_nodes:
        raise ValueError("revised gauge touches a node in a frozen contact surface set")
    if gauge_ids & load_nodes:
        raise ValueError("revised gauge touches a node in the frozen load patch")
    if not load_nodes <= contact_nodes:
        raise ValueError("the frozen loading patch is not contained in classified contact faces")

    coordinates = {label: mesh_nodes[node] for label, node in GAUGE_NODES.items()}
    constraint_matrix = _rigid_constraint_matrix(coordinates)
    rank = _matrix_rank(constraint_matrix)
    if rank != 6:
        raise ValueError(f"the selected six SPCs remove only {rank} rigid modes")

    def min_distance(node_id: int, other_nodes: set[int]) -> float:
        point = mesh_nodes[node_id]
        return min(math.dist(point, mesh_nodes[other]) for other in other_nodes)

    labels_by_node = {node: label for label, node in GAUGE_NODES.items()}
    chosen = []
    dofs_by_node = {33824: [1, 2, 3], 43470: [2, 3], 33822: [2]}
    for label, node_id in GAUGE_NODES.items():
        chosen.append({
            "label": label,
            "node_id": node_id,
            "owner": PRINCIPAL_PART_ID,
            "mesh_owner": PRINCIPAL_MESH_ID,
            "global_xyz_mm": list(mesh_nodes[node_id]),
            "local_XTN_mm": list(local_by_node[node_id]),
            "fixed_global_dofs": dofs_by_node[node_id],
            "nearest_contact_surface_node_distance_mm": min_distance(node_id, contact_nodes),
            "nearest_load_patch_node_distance_mm": min_distance(node_id, load_nodes),
        })

    fragment = (
        "** Current zero-load 3-2-1 rigid-frame gauge; not a physical support.\n"
        "** Revised remote far-T section triad: literal source corners lie in complete-face contact NSETs.\n"
        "*BOUNDARY\n"
        "33824,1,3,0.\n"
        "43470,2,3,0.\n"
        "33822,2,2,0.\n"
    )
    report = {
        "schema": "wood_joint_current_remote_gauge/v1",
        "status": "CURRENT_REMOTE_GAUGE_FRAGMENT_SOURCE_BOUND",
        "scope": "six-scalar zero-displacement gauge only; not a support, load path, or response result",
        "native_solve_run": False,
        "current_mesh": {
            "wood_bodies": 3,
            "physical_bolts": 4,
            "physical_metal_bodies": 16,
            "wood_interfaces": len(parsed["classification"].get("wood_interfaces", [])),
            "body_count": 19,
            "node_count": 116162,
            "element_count": 57643,
        },
        "source_local_frame": {
            "member_id": PRINCIPAL_PART_ID,
            "origin_global_xyz_mm": list(origin),
            "axes_global_xyz": {key: list(value) for key, value in local_axes.items()},
            "measured_mesh_extents_local_mm": measured_extents,
            "source_extents_local_mm": extents,
            "far_T_max_mm": REMOTE_T_MAX_MM,
            "origin_projected_global_T_mm": _dot(origin, local_axes["T"]),
            "far_T_projected_global_mm": _dot(origin, local_axes["T"]) + REMOTE_T_MAX_MM,
        },
        "gauge_selection": {
            "revised_from_contract_corner_triad": True,
            "triad_type": "revised far-T end-section 3-2-1 triad; not three geometric extreme-corner nodes",
            "selection_basis": "all selected nodes lie at source principal T_max; A and C lie on the N-minimum/maximum end-section boundaries and B is a mesh node interior to that end section; all three are outside emitted contact and generated load node sets",
            "reason": "literal contract corner nodes are present in the frozen complete-face contact NSETs; revised far-T end-section nodes are outside every emitted contact NSET and the frozen generated loading patch",
            "literal_contract_corner_nodes": {
                label: {
                    "node_id": node,
                    "in_contact_surface_node_sets": node in contact_nodes,
                    "in_load_patch": node in load_nodes,
                }
                for label, node in CONTRACT_CORNER_NODES.items()
            },
            "selected_nodes": chosen,
            "contact_nset_node_union_count": len(contact_nodes),
            "load_patch_node_count": len(load_nodes),
            "selected_contact_node_intersection": sorted(gauge_ids & contact_nodes),
            "selected_load_node_intersection": sorted(gauge_ids & load_nodes),
        },
        "constraints": {
            "coordinate_system": "global XYZ",
            "rows_node_dof_value": [[node, dof, 0.0] for node, dof in SPC_ROWS],
            "rigid_body_kinematic_matrix_rank": rank,
            "rigid_body_kinematic_matrix_shape": [len(constraint_matrix), 6],
            "rigid_body_kinematic_matrix_column_order": ["tx", "ty", "tz", "wx_scaled", "wy_scaled", "wz_scaled"],
            "rigid_body_kinematic_matrix_row_order": [[node, dof] for node, dof in SPC_ROWS],
            "rigid_body_kinematic_matrix_rows": constraint_matrix,
            "rank_method": "Gaussian elimination with absolute pivot tolerance 1e-12 after scaling rotations by 1000 mm",
            "rotation_length_scale_mm": ROTATION_LENGTH_SCALE_MM,
            "full_face_clamp": False,
            "constrained_nodes": sorted(gauge_ids),
            "constrained_scalar_count": len(SPC_ROWS),
        },
        "input_sha256": {label: _sha(payload) for label, payload in raw.items()},
        "fragment_sha256": _sha(fragment.encode("utf-8")),
        "limitations": [
            "The representative response contract predates the current three-wood/four-bolt mesh; its named principal member and local far-T extent remain exactly bound here, while the scope difference is retained.",
            "Contact exclusion is conservative at the emitted contact-surface NSET level; the selected nodes are also disjoint from the frozen generated nodal load patch.",
            "The gauge removes only whole-assembly rigid-frame freedom; it adds no contact, support, stiffness, or physical load path.",
        ],
    }
    return fragment, report
