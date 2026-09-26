"""Verify the exact mesh-node IDs emitted by the ACC output proposal."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path.cwd()
MESH = ROOT / (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "ordinary-transient-seating-100n-every-increment-k1e4-attempt01/mesh.inp"
)
CONTROL_DECK = ROOT / (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "dependent-native-instrumented-attempt01/nut-coupling.inp"
)
OUTPUT = ROOT / (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "all-physical-acc-output-proposal-attempt01/node-map-audit.json"
)
EXPECTED_MESH_SHA256 = (
    "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803"
)
EXPECTED_CONTROL_DECK_SHA256 = (
    "af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903"
)
EXPECTED_PHYSICAL_NODES = 116_162
EXPECTED_SOLIDS = 57_643
EXPECTED_CONTROL_NODES = set(range(116_163, 116_171))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_mesh(path: Path) -> tuple[set[int], set[int], int]:
    node_ids: set[int] = set()
    connectivity_ids: set[int] = set()
    element_ids: set[int] = set()
    mode = ""
    element_type = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            parts = [part.strip().upper() for part in line.split(",")]
            keyword = parts[0]
            mode = ""
            element_type = ""
            if keyword == "*NODE":
                mode = "node"
            elif keyword == "*ELEMENT":
                mode = "element"
                element_type = next(
                    (
                        part.removeprefix("TYPE=")
                        for part in parts[1:]
                        if part.startswith("TYPE=")
                    ),
                    "",
                )
            continue
        fields = [field.strip() for field in line.split(",") if field.strip()]
        if mode == "node":
            if len(fields) != 4:
                raise ValueError("unexpected *NODE row width")
            node_id = int(fields[0])
            if node_id in node_ids:
                raise ValueError(f"duplicate mesh node ID {node_id}")
            node_ids.add(node_id)
        elif mode == "element":
            if element_type != "C3D10" or len(fields) != 11:
                raise ValueError(
                    "unexpected non-C3D10 or malformed original element row"
                )
            element_id = int(fields[0])
            if element_id in element_ids:
                raise ValueError(f"duplicate element ID {element_id}")
            element_ids.add(element_id)
            connectivity_ids.update(int(value) for value in fields[1:])
    return node_ids, connectivity_ids, len(element_ids)


def parse_control_nodes(path: Path) -> set[int]:
    node_ids: set[int] = set()
    in_nodes = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            in_nodes = line.split(",", 1)[0].strip().upper() == "*NODE"
            continue
        if in_nodes:
            node_ids.add(int(line.split(",", 1)[0].strip()))
    return node_ids


def canonical_id_hash(values: set[int]) -> str:
    payload = "".join(f"{value}\n" for value in sorted(values)).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    mesh_hash = sha256(MESH)
    control_hash = sha256(CONTROL_DECK)
    if mesh_hash != EXPECTED_MESH_SHA256:
        raise SystemExit(f"mesh hash changed: {mesh_hash}")
    if control_hash != EXPECTED_CONTROL_DECK_SHA256:
        raise SystemExit(f"control deck hash changed: {control_hash}")

    mesh_ids, connectivity_ids, element_count = parse_mesh(MESH)
    control_ids = parse_control_nodes(CONTROL_DECK)
    expected_ids = set(range(1, EXPECTED_PHYSICAL_NODES + 1))
    if len(mesh_ids) != EXPECTED_PHYSICAL_NODES or mesh_ids != expected_ids:
        raise SystemExit("mesh *NODE IDs do not equal the pinned contiguous ID set")
    if element_count != EXPECTED_SOLIDS:
        raise SystemExit(f"expected {EXPECTED_SOLIDS} solids, got {element_count}")
    if connectivity_ids != mesh_ids:
        raise SystemExit("C3D10 connectivity node IDs differ from the mesh *NODE set")
    if control_ids != EXPECTED_CONTROL_NODES or control_ids & connectivity_ids:
        raise SystemExit(
            "auxiliary control node IDs changed or appear in solid connectivity"
        )

    report = {
        "schema": "wood_joint_all_mesh_acc_node_map_audit/v1",
        "status": "PASS_EXACT_NODE_SET_FROM_PINNED_C3D10_CONNECTIVITY",
        "mesh_sha256": mesh_hash,
        "control_deck_sha256": control_hash,
        "c3d10_element_count": element_count,
        "mesh_node_count": len(mesh_ids),
        "mesh_node_ids_min_max": [min(mesh_ids), max(mesh_ids)],
        "mesh_node_ids_contiguous": True,
        "mesh_node_ids_sha256_sorted_decimal_lf": canonical_id_hash(mesh_ids),
        "connectivity_node_count_unique": len(connectivity_ids),
        "connectivity_node_ids_sha256_sorted_decimal_lf": canonical_id_hash(
            connectivity_ids
        ),
        "mesh_node_set_equals_c3d10_connectivity_node_set": True,
        "auxiliary_control_node_ids": sorted(control_ids),
        "auxiliary_control_ids_absent_from_c3d10_connectivity": True,
        "emitted_node_ids": [1, EXPECTED_PHYSICAL_NODES],
        "solver_node_count_including_controls": EXPECTED_PHYSICAL_NODES
        + len(control_ids),
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
